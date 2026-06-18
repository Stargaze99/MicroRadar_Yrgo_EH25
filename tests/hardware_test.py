from machine import Pin, PWM, time_pulse_us
from utime import sleep, sleep_ms, sleep_us, ticks_ms, ticks_diff


# Pin plan
TRIG_PIN = 2
ECHO_PIN = 3
SERVO_PIN = 4

ENC_A_PIN = 20
ENC_B_PIN = 21
ENC_SW_PIN = 22


# Servo calibration for MG90S-style hobby servos.
# Keep the first tests away from hard mechanical end stops.
SERVO_MIN_US = 500
SERVO_MAX_US = 2500
SERVO_MIN_ANGLE = 0
SERVO_MAX_ANGLE = 180


led = Pin("LED", Pin.OUT)

trig = Pin(TRIG_PIN, Pin.OUT)
echo = Pin(ECHO_PIN, Pin.IN)

servo = PWM(Pin(SERVO_PIN))
servo.freq(50)

enc_a = Pin(ENC_A_PIN, Pin.IN, Pin.PULL_UP)
enc_b = Pin(ENC_B_PIN, Pin.IN, Pin.PULL_UP)
enc_sw = Pin(ENC_SW_PIN, Pin.IN, Pin.PULL_UP)


def set_servo_angle(angle):
    angle = max(0, min(180, angle))
    pulse_us = SERVO_MIN_US + (SERVO_MAX_US - SERVO_MIN_US) * angle // 180
    servo.duty_ns(pulse_us * 1000)


def read_distance_cm():
    trig.low()
    sleep_us(2)
    trig.high()
    sleep_us(10)
    trig.low()

    duration = time_pulse_us(echo, 1, 30_000)
    if duration < 0:
        return None

    return duration * 0.0343 / 2


def read_encoder_step(last_a):
    current_a = enc_a.value()
    if current_a == last_a:
        return 0, last_a

    if enc_b.value() != current_a:
        return 1, current_a
    return -1, current_a


def main():
    print("MicroRadar hardware test")
    print("Pins:")
    print("  HY-SRF05 TRIG GP{}".format(TRIG_PIN))
    print("  HY-SRF05 ECHO GP{} via voltage divider".format(ECHO_PIN))
    print("  MG90S servo GP{}".format(SERVO_PIN))
    print("  Encoder A/B/SW GP{}/{}/{}".format(ENC_A_PIN, ENC_B_PIN, ENC_SW_PIN))
    print()
    print("Press Ctrl+C to stop.")

    last_a = enc_a.value()
    encoder_position = 0
    last_button = enc_sw.value()
    last_report = ticks_ms()

    try:
        while True:
            for angle in range(SERVO_MIN_ANGLE, SERVO_MAX_ANGLE + 1, 15):
                set_servo_angle(angle)
                sleep_ms(120)

                distance = read_distance_cm()
                if distance is None:
                    distance_text = "timeout"
                else:
                    distance_text = "{:.1f} cm".format(distance)

                step, last_a = read_encoder_step(last_a)
                if step:
                    encoder_position += step

                button = enc_sw.value()
                if button != last_button:
                    print("encoder button:", "pressed" if button == 0 else "released")
                    last_button = button

                if ticks_diff(ticks_ms(), last_report) > 250:
                    print(
                        "angle={:3d}  distance={}  enc={}".format(
                            angle, distance_text, encoder_position
                        )
                    )
                    led.toggle()
                    last_report = ticks_ms()

            for angle in range(SERVO_MAX_ANGLE, SERVO_MIN_ANGLE - 1, -15):
                set_servo_angle(angle)
                sleep_ms(120)

                distance = read_distance_cm()
                if distance is None:
                    distance_text = "timeout"
                else:
                    distance_text = "{:.1f} cm".format(distance)

                step, last_a = read_encoder_step(last_a)
                if step:
                    encoder_position += step

                button = enc_sw.value()
                if button != last_button:
                    print("encoder button:", "pressed" if button == 0 else "released")
                    last_button = button

                if ticks_diff(ticks_ms(), last_report) > 250:
                    print(
                        "angle={:3d}  distance={}  enc={}".format(
                            angle, distance_text, encoder_position
                        )
                    )
                    led.toggle()
                    last_report = ticks_ms()

    except KeyboardInterrupt:
        pass
    finally:
        servo.deinit()
        led.off()
        print("Hardware test stopped.")


main()
