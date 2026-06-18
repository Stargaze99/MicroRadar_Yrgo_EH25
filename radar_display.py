from math import cos, pi, sin

from config import DOT_MAX_AGE, MAX_DISTANCE_CM


CENTER_X = 64
CENTER_Y = 63
RADIUS = 52
# Display scale is limited to 200 cm so useful points are visible on 64 px.
DISPLAY_MAX_DISTANCE_CM = min(MAX_DISTANCE_CM, 200)


def point_for_angle(angle, radius):
    # 0 degrees is right, 90 degrees is up, 180 degrees is left.
    radians = angle * pi / 180
    x = int(CENTER_X + cos(radians) * radius)
    y = int(CENTER_Y - sin(radians) * radius)
    return x, y


def distance_to_radius(distance_cm):
    # Clamp far readings to the outer ring. The sensor may measure farther than
    # the display scale, but drawing beyond the semicircle would be misleading.
    if distance_cm is None:
        return None

    if distance_cm < 0:
        return None

    distance_cm = min(distance_cm, DISPLAY_MAX_DISTANCE_CM)
    return int(distance_cm * RADIUS / DISPLAY_MAX_DISTANCE_CM)


def draw_dot(oled, x, y, age):
    # Monochrome OLED cannot fade brightness, so point age is shown by size.
    if age >= 4:
        for dx, dy in (
            (-1, -2), (0, -2),
            (-2, -1), (-1, -1), (0, -1), (1, -1),
            (-2, 0), (-1, 0), (0, 0), (1, 0),
            (-1, 1), (0, 1),
        ):
            oled.pixel(x + dx, y + dy, 1)
    elif age == 3:
        for dx, dy in (
            (0, -1),
            (-1, 0), (0, 0), (1, 0),
            (0, 1),
        ):
            oled.pixel(x + dx, y + dy, 1)
    elif age == 2:
        oled.pixel(x, y, 1)
        oled.pixel(x + 1, y, 1)
        oled.pixel(x, y + 1, 1)
    elif age == 1:
        oled.pixel(x, y, 1)


def age_scan_points(scan_points):
    # Called once per display update interval to make old detections shrink.
    # Expired keys are collected first because deleting from a dictionary while
    # iterating over it is unsafe.
    expired_angles = []
    for angle, point in scan_points.items():
        point["age"] -= 1
        if point["age"] <= 0:
            expired_angles.append(angle)

    for angle in expired_angles:
        del scan_points[angle]


def set_scan_point(scan_points, angle, distance_cm):
    # New detections start at full dot size and fade over later updates.
    if distance_cm is None:
        return
    scan_points[angle] = {
        "distance_cm": distance_cm,
        "age": DOT_MAX_AGE,
    }


def draw_radar(oled, sweep_angle, scan_points):
    # Redraw the whole radar frame. This is simpler and reliable for SSD1306.
    # Partial redraw would be faster, but the full-frame buffer is small enough
    # and avoids stale pixels from old sweep lines.
    oled.fill(0)

    oled.line(12, CENTER_Y, 116, CENTER_Y, 1)

    for radius in (17, 35, 52):
        previous = None
        for angle in range(0, 181, 4):
            point = point_for_angle(angle, radius)
            if previous is not None:
                oled.line(previous[0], previous[1], point[0], point[1], 1)
            previous = point

    for angle in (0, 45, 90, 135, 180):
        x, y = point_for_angle(angle, RADIUS)
        oled.line(CENTER_X, CENTER_Y, x, y, 1)

    for angle, point in scan_points.items():
        distance_cm = point["distance_cm"]
        radius = distance_to_radius(distance_cm)
        if radius is None:
            continue
        x, y = point_for_angle(angle, radius)
        draw_dot(oled, x, y, point["age"])

    x, y = point_for_angle(sweep_angle, RADIUS)
    oled.line(CENTER_X, CENTER_Y, x, y, 1)
    oled.show()
