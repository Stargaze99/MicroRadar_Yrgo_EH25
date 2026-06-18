from machine import Pin
from utime import ticks_diff, ticks_ms

try:
    from config import ENC_A_PIN, ENC_B_PIN, ENC_SW_PIN
except ImportError:
    # Fallback keeps the standalone encoder test usable if config.py on the
    # Pico has not been updated yet.
    ENC_A_PIN = 20
    ENC_B_PIN = 21
    ENC_SW_PIN = 22


class RotaryEncoder:
    def __init__(self):
        # Encoder contacts pull the GPIOs to ground, so internal pullups are on.
        self.a = Pin(ENC_A_PIN, Pin.IN, Pin.PULL_UP)
        self.b = Pin(ENC_B_PIN, Pin.IN, Pin.PULL_UP)
        self.sw = Pin(ENC_SW_PIN, Pin.IN, Pin.PULL_UP)
        self.last_a = self.a.value()
        self.last_sw = self.sw.value()
        self.last_sw_change_ms = ticks_ms()

    def read_step(self):
        # Quadrature direction is detected when channel A changes.
        current_a = self.a.value()
        if current_a == self.last_a:
            return 0

        self.last_a = current_a
        if self.b.value() != current_a:
            return 1
        return -1

    def read_button_event(self):
        # Basic debounce for the encoder push button.
        current_sw = self.sw.value()
        if current_sw == self.last_sw:
            return None

        now_ms = ticks_ms()
        if ticks_diff(now_ms, self.last_sw_change_ms) < 40:
            return None

        self.last_sw = current_sw
        self.last_sw_change_ms = now_ms

        if current_sw == 0:
            return "pressed"
        return "released"

    def button_value(self):
        return self.sw.value()
