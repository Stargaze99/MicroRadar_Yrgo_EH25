import utime
from machine import Pin

from app_state import AppState
from config import PING_DELAY_MS, MAX_ANGLE, MIN_ANGLE, STEP_DEGREES
from mqtt_service import (
    connect_mqtt,
    connect_wifi,
    publish_scan_point,
    publish_status,
)
from sensor import AngleDistanceFilter, DistanceSensor
from servo import Servo, scan_angles
from ui_thread import start_ui_thread


TOPIC_DISTANCE = b"yrgo/iot/distance_cm"
TOPIC_ANGLE = b"yrgo/iot/angle"
TOPIC_STATUS = b"yrgo/iot/status"


def should_measure(angle, settings):
    # Servo can move every degree while the sensor is read less often. This
    # keeps motion smooth without forcing an ultrasonic ping at every step.
    return (angle - MIN_ANGLE) % settings.measure_every_degrees == 0


def should_publish(measurement_count, settings):
    # MQTT publish rate is user-configurable from the settings menu.
    return measurement_count % settings.mqtt_every_measurements == 0


def run():
    # Main thread: owns servo movement, ultrasonic reads, and MQTT publish.
    # UI thread owns OLED, encoder, menu, and runtime settings.
    led = Pin("LED", Pin.OUT)
    servo = None
    mqtt_client = None
    state = AppState()
    distance_filter = AngleDistanceFilter()
    measurement_count = 0
    last_ping_ms = 0

    try:
        ip_address = connect_wifi()
        mqtt_client = connect_mqtt("microradar-" + ip_address)
        publish_status(mqtt_client, TOPIC_STATUS, b"online")

        sensor = DistanceSensor()
        servo = Servo()
        start_ui_thread(state)

        for angle in scan_angles(MIN_ANGLE, MAX_ANGLE, STEP_DEGREES):
            settings = state.get_settings()

            servo.set_angle(angle)
            utime.sleep_ms(settings.step_delay_ms)
            state.update_angle(angle)

            if not should_measure(angle, settings):
                continue

            # Do not ping the ultrasonic sensor faster than its configured
            # recovery interval.
            now_ms = utime.ticks_ms()
            if utime.ticks_diff(now_ms, last_ping_ms) < PING_DELAY_MS:
                continue
            last_ping_ms = now_ms

            raw_distance_cm, _, _ = sensor.read_once_cm()
            filtered_distance_cm = distance_filter.update(angle, raw_distance_cm)
            state.update_measurement(angle, raw_distance_cm, filtered_distance_cm)

            measurement_count += 1
            if should_publish(measurement_count, settings):
                publish_scan_point(
                    mqtt_client,
                    TOPIC_ANGLE,
                    TOPIC_DISTANCE,
                    angle,
                    filtered_distance_cm,
                )

            print("angle={} raw={} filtered={}".format(
                angle,
                raw_distance_cm,
                filtered_distance_cm,
            ))
            led.toggle()

    except KeyboardInterrupt:
        print("Stopping radar.")

    finally:
        state.stop()
        utime.sleep_ms(100)

        if mqtt_client is not None:
            try:
                publish_status(mqtt_client, TOPIC_STATUS, b"offline")
                mqtt_client.disconnect()
            except Exception:
                pass

        if servo is not None:
            servo.center()
            utime.sleep_ms(500)
            servo.deinit()

        led.off()


if __name__ == "__main__":
    run()
