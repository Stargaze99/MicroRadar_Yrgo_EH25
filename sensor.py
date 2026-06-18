from machine import Pin, time_pulse_us
from utime import sleep_ms, sleep_us

from config import (
    ECHO_PIN,
    ECHO_TIMEOUT_US,
    FILTER_WINDOW,
    MAX_DISTANCE_CM,
    MIN_DISTANCE_CM,
    PING_DELAY_MS,
    SAMPLES,
    TRIG_PIN,
    TRIGGER_US,
)


def median(values):
    ordered = values[:]
    ordered.sort()
    return ordered[len(ordered) // 2]


class DistanceSensor:
    def __init__(self):
        self.trig = Pin(TRIG_PIN, Pin.OUT)
        self.echo = Pin(ECHO_PIN, Pin.IN)

    def read_once_cm(self):
        # Echo should be low before triggering; high here usually means wiring
        # error or a stuck signal.
        idle_before = self.echo.value()
        if idle_before:
            return None, "echo_high_before_trigger", idle_before

        self.trig.low()
        sleep_us(5)
        self.trig.high()
        sleep_us(TRIGGER_US)
        self.trig.low()

        # Pulse length is the round-trip time for the ultrasonic signal.
        duration_us = time_pulse_us(self.echo, 1, ECHO_TIMEOUT_US)
        if duration_us < 0:
            return None, duration_us, idle_before

        # HY-SRF05/HC-SR04 style conversion: distance in cm is pulse_us / 58.
        distance_cm = duration_us / 58.0
        if distance_cm < MIN_DISTANCE_CM or distance_cm > MAX_DISTANCE_CM:
            return None, duration_us, idle_before

        return distance_cm, duration_us, idle_before

    def read_distance_debug(self):
        # Standalone test helper: take multiple samples and return the median.
        readings = []
        last_debug = None

        for _ in range(SAMPLES):
            distance, duration_us, idle_before = self.read_once_cm()
            last_debug = duration_us, idle_before
            if distance is not None:
                readings.append(distance)
            sleep_ms(PING_DELAY_MS)

        if not readings:
            duration_us, idle_before = last_debug
            return None, duration_us, idle_before

        readings.sort()
        return readings[len(readings) // 2], "median", len(readings)

    def read_distance_cm(self):
        distance_cm, _, _ = self.read_distance_debug()
        return distance_cm


class AngleDistanceFilter:
    # Per-angle sliding median filter. Readings from different directions are
    # kept separate because the sensor rotates with the servo.
    def __init__(self):
        self.history = {}

    def update(self, angle, distance_cm):
        if distance_cm is None:
            return None

        values = self.history.get(angle)
        if values is None:
            values = []
            self.history[angle] = values

        values.append(distance_cm)
        if len(values) > FILTER_WINDOW:
            values.pop(0)

        return median(values)
