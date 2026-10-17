<div align="center">

# MicroRadar

### Ultrasonic scanning, real-time OLED visualization and MQTT telemetry

**Raspberry Pi Pico 2 W · MicroPython · HY-SRF05 · MG90S · SPI OLED · Wi-Fi / MQTT**

![MicroPython](https://img.shields.io/badge/Language-MicroPython-3776AB?logo=python&logoColor=white)
![Hardware](https://img.shields.io/badge/Board-Pico%202%20W-C51A4A)
![Sensor](https://img.shields.io/badge/Sensing-Ultrasonic-00796B)
![Telemetry](https://img.shields.io/badge/Protocol-MQTT-660066?logo=mqtt&logoColor=white)
![Status](https://img.shields.io/badge/Project-Embedded%20prototype-2E7D32)

*A practical embedded systems and IoT project developed during electronics engineering studies at Yrgo.*

</div>

---

## Overview

**MicroRadar** is a **radar-style ultrasonic distance scanner**, not an RF radar. An **HY-SRF05** ultrasonic sensor mounted on an **MG90S** servo scans across a 180° arc. A **Raspberry Pi Pico 2 W** measures distance, filters readings and draws detections on a **128 × 64 SPI OLED**. A **rotary encoder with a push button** controls the local menu, and measurements are published over **Wi-Fi using MQTT**.

The software separates the measurement/control loop from the user interface using MicroPython threads and a lock-protected shared state.

### Features

- Continuous back-and-forth **0–180° servo scanning**
- Ultrasonic ranging with timeout and out-of-range checks
- **Per-angle sliding median filtering** across successive scans
- Semicircular OLED radar view with sweep line and age-based detection markers
- Encoder-controlled **radar / data / settings** menus
- Live changes to servo delay, angular measurement interval and MQTT publishing frequency
- MQTT topics for angle, valid distance and retained online/offline status
- Dedicated hardware-oriented test scripts

> This is an educational ultrasonic scanning instrument, not a safety-rated collision detector.

## System architecture

~~~mermaid
flowchart TD
    S["HY-SRF05"] --> M["Measurement and validation"]
    V["MG90S servo"] <--> A["Main thread"]
    M --> F["Per-angle median filter"]
    F --> A
    A --> D["Thread-safe shared state"]
    A --> N["Wi-Fi / MQTT"]
    E["Rotary encoder + button"] --> U["UI thread"]
    D --> U
    U -->|"Runtime settings"| D
    U --> O["128×64 SPI OLED"]
~~~

| Part | Responsibility |
|:--|:--|
| Main thread | Servo movement, distance measurement, filtering and MQTT publishing |
| UI thread | Encoder input, menus, OLED rendering and runtime controls |
| Shared state | Lock-protected data copies and settings snapshots |

The UI draws from a copied snapshot rather than holding the shared lock during SPI transfers. The implementation is in [main.py](main.py), [app_state.py](app_state.py) and [ui_thread.py](ui_thread.py).

## Hardware and connections

| Device | Signal | Pico GPIO |
|:--|:--|--:|
| HY-SRF05 | TRIG | **GP2** |
| HY-SRF05 | ECHO | **GP3** |
| MG90S | Servo PWM | **GP4** |
| OLED SPI | SCK | **GP6** |
| OLED SPI | MOSI | **GP7** |
| OLED SPI | RESET | **GP8** |
| OLED SPI | D/C | **GP9** |
| OLED SPI | CS | **GP10** |
| Rotary encoder | A | **GP20** |
| Rotary encoder | B | **GP21** |
| Rotary encoder | Push button | **GP22** |

The pin mapping comes from [config.py](config.py).

**Electrical safety**

- Pico GPIO is **3.3 V logic**. Do not connect a **5 V ECHO** signal directly to GP3. Use a suitable voltage divider or logic-level converter.
- Power the servo from a supply capable of handling its current peaks rather than from a GPIO. Connect the relevant grounds together.
- Check the specific sensor, servo and display module ratings before wiring or powering the setup.
- Start with conservative servo limits and adjust if the mechanism hits its end stops.

## Measurement and visualization

1. The servo moves between 0° and 180°, reversing direction at the ends.
2. The Pico drives the sensor TRIG pin for **10 μs**.
3. The sensor returns an echo pulse; the firmware measures its duration.
4. Valid distance is calculated approximately as **echo duration (μs) / 58**, in centimeters.
5. A sliding median filter maintains separate histories for different servo angles.
6. The latest scan state is displayed on OLED and selected samples are sent over MQTT.

| Configuration | Default |
|:--|--:|
| Scan range | 0–180° |
| Servo step | 1° |
| Servo delay per step | 40 ms |
| Measurement interval | Every 1° (subject to ping timing) |
| Minimum ping delay | 35 ms |
| Accepted sensor distance | 2–450 cm |
| Median history | 3 readings per angle |
| Radar display scale | 0–200 cm |

The radar drawing caps displayed distances at **200 cm**, even though the sensor acceptance range extends farther. These parameters can be found in [config.py](config.py) and [radar_display.py](radar_display.py).

### On-device UI

| View | Contents |
|:--|:--|
| Radar | Semicircle, sweep line, age-based detection dots |
| Data list | Angle, raw/filtered distance, servo speed and MQTT setting |
| Settings | Servo speed, measurement angle spacing, MQTT publish rate |

**Using the encoder:** Rotate to navigate or change a setting, press to select or confirm. Changes affect the current run only and are not stored persistently.

## MQTT

| Topic | Payload |
|:--|:--|
| **yrgo/iot/angle** | Servo angle in degrees |
| **yrgo/iot/distance_cm** | Filtered distance in cm, when valid |
| **yrgo/iot/status** | Retained online/offline status |

MQTT is configured for **port 1883** by default, which typically means unencrypted transmission. Use a trusted network and broker.

## Setup

### Requirements

- Raspberry Pi Pico 2 W with compatible MicroPython firmware
- HY-SRF05 sensor, MG90S servo, 128 × 64 SPI OLED and rotary encoder
- Correct supplies, shared ground and required logic-level adaptation
- Local Wi-Fi and a reachable MQTT broker
- An upload method such as **Thonny** or **mpremote**
- The MicroPython **umqtt.simple** module

### Quick start

1. Clone the repository:

       git clone https://github.com/Stargaze99/MicroRadar_Yrgo_EH25.git
       cd MicroRadar_Yrgo_EH25

2. Verify the wiring and power supplies using the table above.
3. Edit [config.py](config.py) with your **Wi-Fi SSID/password**, MQTT broker address, port and any required credentials.
4. Upload the project Python modules into the **root of the Pico's MicroPython filesystem**. Make sure **umqtt.simple** is available.
5. From the MicroPython REPL, run:

       import main
       main.run()

6. Use the OLED and encoder to inspect the scan. Subscribe to **yrgo/iot/#** on the broker to monitor telemetry.

> **Current startup behavior:** Wi-Fi and MQTT connections happen *before* the sensor, servo and UI initialize. The firmware therefore does **not currently provide a working offline scan mode** when network setup fails.

**Security note:** The repository contains a tracked [config.py](config.py). Keep placeholder credentials in the public repository. Do not commit real Wi-Fi or MQTT passwords.

## Repository layout

    MicroRadar_Yrgo_EH25/
    ├── main.py                # System startup, main scan loop and MQTT
    ├── config.py              # Pin, timing and network configuration
    ├── sensor.py              # Ultrasonic sensor and median filter
    ├── servo.py               # PWM servo and scan-angle generator
    ├── mqtt_service.py        # Network connectivity and publishing
    ├── app_state.py           # Shared data with thread locks
    ├── ui_thread.py           # OLED updates and encoder polling
    ├── oled.py                # SSD1306-compatible SPI driver
    ├── radar_display.py       # Radar graphics
    ├── encoder.py             # Rotary encoder events
    ├── menu.py                # UI state and runtime settings
    └── tests/                 # Standalone sensor, servo and UI tests

## Troubleshooting

| Symptom | What to check |
|:--|:--|
| Scan does not start | Wi-Fi password, broker IP/port and umqtt.simple installation |
| Invalid distance or timeouts | TRIG/ECHO connections, 3.3 V signal adaptation, target range |
| Servo buzzes or binds | Servo power, mechanical limits and configured pulse widths |
| Black OLED | SPI wiring, RESET, D/C, CS and display compatibility |
| Encoder not responding | Encoder connections, pull-ups and shared ground |
| No MQTT data | Broker availability, topic subscription and connection credentials |

The [tests](tests) directory provides individual **hardware test programs**. It is not an automated CI test suite.

## Known limitations and future work

- Network connectivity is currently required at startup, and automatic MQTT reconnection is not implemented.
- Ultrasonic measurement accuracy is not quantified by a published calibration report.
- Runtime UI settings reset on restart.
- MQTT angle and distance are published as **separate topics**, rather than one atomic reading with a timestamp.
- No project photographs, complete wiring schematic or measured performance report are included in this repository yet.

Possible extensions include offline operation, more robust networking, combined timestamped MQTT messages, controlled distance-validation tests and photographs of the final build.

---

<sub>Yrgo · Electronics engineering / Embedded Systems and IoT · [main.py](main.py) · [hardware tests](tests/hardware_test.py)</sub>
