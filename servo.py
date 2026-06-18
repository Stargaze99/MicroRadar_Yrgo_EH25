from machine import Pin, PWM

from config import SERVO_MAX_US, SERVO_MIN_US, SERVO_PIN


class Servo:
    def __init__(self):
        self.pwm = PWM(Pin(SERVO_PIN))
        # Hobby servos expect a 50 Hz control signal.
        self.pwm.freq(50)

    def set_angle(self, angle):
        # Map 0..180 degrees to the calibrated pulse width range.
        angle = max(0, min(180, angle))
        pulse_us = SERVO_MIN_US + (SERVO_MAX_US - SERVO_MIN_US) * angle // 180
        self.pwm.duty_ns(pulse_us * 1000)

    def center(self):
        self.set_angle(90)

    def deinit(self):
        self.pwm.deinit()


def scan_angles(min_angle, max_angle, step_degrees):
    # Continuous back-and-forth scan avoids jumping from max angle to min angle.
    while True:
        for angle in range(min_angle, max_angle + 1, step_degrees):
            yield angle

        for angle in range(max_angle, min_angle - 1, -step_degrees):
            yield angle
