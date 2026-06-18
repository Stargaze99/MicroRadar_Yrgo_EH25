from framebuf import FrameBuffer, MONO_VLSB
from machine import Pin, SPI
from utime import sleep_ms

from config import (
    OLED_CS_PIN,
    OLED_DC_PIN,
    OLED_HEIGHT,
    OLED_MOSI_PIN,
    OLED_RES_PIN,
    OLED_SCK_PIN,
    OLED_SPI_ID,
    OLED_WIDTH,
)


class SSD1306_SPI:
    def __init__(self):
        self.width = OLED_WIDTH
        self.height = OLED_HEIGHT
        self.pages = self.height // 8
        # SSD1306 stores pixels in 8-pixel-high pages.
        self.buffer = bytearray(self.width * self.pages)
        self.framebuf = FrameBuffer(self.buffer, self.width, self.height, MONO_VLSB)

        self.spi = SPI(
            OLED_SPI_ID,
            baudrate=10_000_000,
            polarity=0,
            phase=0,
            sck=Pin(OLED_SCK_PIN),
            mosi=Pin(OLED_MOSI_PIN),
        )
        self.dc = Pin(OLED_DC_PIN, Pin.OUT)
        self.res = Pin(OLED_RES_PIN, Pin.OUT)
        self.cs = Pin(OLED_CS_PIN, Pin.OUT)

        self.cs.high()
        self.reset()
        self.init_display()

    def reset(self):
        self.res.high()
        sleep_ms(1)
        self.res.low()
        sleep_ms(10)
        self.res.high()

    def write_cmd(self, cmd):
        # DC low means the byte is a command.
        self.dc.low()
        self.cs.low()
        self.spi.write(bytearray([cmd]))
        self.cs.high()

    def write_data(self, data):
        # DC high means bytes are framebuffer data.
        self.dc.high()
        self.cs.low()
        self.spi.write(data)
        self.cs.high()

    def init_display(self):
        # Minimal SSD1306 init sequence for 128x64 SPI OLED modules.
        for cmd in (
            0xAE,
            0x20, 0x00,
            0xB0,
            0xC8,
            0x00,
            0x10,
            0x40,
            0x81, 0x7F,
            0xA1,
            0xA6,
            0xA8, self.height - 1,
            0xA4,
            0xD3, 0x00,
            0xD5, 0x80,
            0xD9, 0xF1,
            0xDA, 0x12,
            0xDB, 0x40,
            0x8D, 0x14,
            0xAF,
        ):
            self.write_cmd(cmd)
        self.fill(0)
        self.show()

    def fill(self, color):
        self.framebuf.fill(color)

    def pixel(self, x, y, color=1):
        self.framebuf.pixel(x, y, color)

    def line(self, x1, y1, x2, y2, color=1):
        self.framebuf.line(x1, y1, x2, y2, color)

    def text(self, text, x, y, color=1):
        self.framebuf.text(text, x, y, color)

    def show(self):
        # Upload the full framebuffer to the OLED.
        self.write_cmd(0x21)
        self.write_cmd(0)
        self.write_cmd(self.width - 1)
        self.write_cmd(0x22)
        self.write_cmd(0)
        self.write_cmd(self.pages - 1)
        self.write_data(self.buffer)
