from utime import sleep_ms

from config import (
    MAX_ANGLE,
    MIN_ANGLE,
    SERVO_PIN,
    STEP_DEGREES,
    STEP_DELAY_MS,
)
from servo import Servo


def main():
    servo = Servo()

    try:
        print("MG90S servo test on GP{}".format(SERVO_PIN))
        print("Smooth sweep {}..{} degrees. Press Ctrl+C to stop.".format(
            MIN_ANGLE,
            MAX_ANGLE,
        ))

        while True:
            for angle in range(MIN_ANGLE, MAX_ANGLE + 1, STEP_DEGREES):
                servo.set_angle(angle)
                sleep_ms(STEP_DELAY_MS)

            for angle in range(MAX_ANGLE, MIN_ANGLE - 1, -STEP_DEGREES):
                servo.set_angle(angle)
                sleep_ms(STEP_DELAY_MS)

    except KeyboardInterrupt:
        print("Stopping servo test.")

    finally:
        servo.center()
        sleep_ms(500)
        servo.deinit()


if __name__ == "__main__":
    main()
