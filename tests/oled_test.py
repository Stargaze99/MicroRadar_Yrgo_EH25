from math import cos, pi, sin
from utime import sleep_ms

from oled import SSD1306_SPI


CENTER_X = 64
CENTER_Y = 63
RADIUS = 52


def point_for_angle(angle, radius):
    radians = angle * pi / 180
    x = int(CENTER_X + cos(radians) * radius)
    y = int(CENTER_Y - sin(radians) * radius)
    return x, y


def draw_radar(oled, sweep_angle):
    oled.fill(0)

    oled.line(12, CENTER_Y, 116, CENTER_Y, 1)
    for radius in (18, 35, 52):
        previous = None
        for angle in range(0, 181, 4):
            point = point_for_angle(angle, radius)
            if previous is not None:
                oled.line(previous[0], previous[1], point[0], point[1], 1)
            previous = point

    for angle in (0, 45, 90, 135, 180):
        x, y = point_for_angle(angle, RADIUS)
        oled.line(CENTER_X, CENTER_Y, x, y, 1)

    x, y = point_for_angle(sweep_angle, RADIUS)
    oled.line(CENTER_X, CENTER_Y, x, y, 1)
    oled.text("OLED OK", 0, 0, 1)
    oled.text("{} deg".format(sweep_angle), 72, 0, 1)
    oled.show()


def main():
    oled = SSD1306_SPI()
    while True:
        for angle in range(5, 176, 3):
            draw_radar(oled, angle)
            sleep_ms(35)
        for angle in range(175, 4, -3):
            draw_radar(oled, angle)
            sleep_ms(35)


if __name__ == "__main__":
    main()
