import _thread
import utime
from machine import Pin

from config import (
    DISPLAY_UPDATE_MS,
    FILTER_WINDOW,
    PING_DELAY_MS,
    MAX_ANGLE,
    MIN_ANGLE,
    STEP_DEGREES,
)
from encoder import RotaryEncoder
from menu import (
    MENU_ITEMS,
    RuntimeSettings,
    VIEW_DATA,
    VIEW_EDIT_SETTING,
    VIEW_RADAR,
    VIEW_SELECT,
    VIEW_SETTINGS,
    MenuController,
    draw_data_view,
    draw_edit_setting,
    draw_menu,
    draw_settings_view,
)
from mqtt_service import (
    connect_mqtt,
    connect_wifi,
    publish_scan_point,
    publish_status,
)
from oled import SSD1306_SPI
from radar_display import age_scan_points, draw_radar, set_scan_point
from sensor import DistanceSensor
from servo import Servo, scan_angles


TOPIC_DISTANCE = b"yrgo/iot/distance_cm"
TOPIC_ANGLE = b"yrgo/iot/angle"
TOPIC_STATUS = b"yrgo/iot/status"
DISPLAY_LOOP_MS = 25
DISPLAY_POLL_MS = 5


class SettingsSnapshot:
    def __init__(self, data):
        self.step_degrees = data["step_degrees"]
        self.step_delay_ms = data["step_delay_ms"]
        self.measure_every_degrees = data["measure_every_degrees"]
        self.mqtt_every_measurements = data["mqtt_every_measurements"]

    def servo_speed_dps(self):
        if self.step_delay_ms <= 0:
            return 0
        return int(self.step_degrees * 1000 / self.step_delay_ms)


def median(values):
    ordered = values[:]
    ordered.sort()
    return ordered[len(ordered) // 2]


def update_angle_history(history, angle, distance_cm):
    if distance_cm is None:
        return None

    values = history.get(angle)
    if values is None:
        values = []
        history[angle] = values

    values.append(distance_cm)
    if len(values) > FILTER_WINDOW:
        values.pop(0)

    return median(values)


def copy_scan_points(scan_points):
    copied = {}
    for angle, point in scan_points.items():
        copied[angle] = {
            "distance_cm": point["distance_cm"],
            "age": point["age"],
        }
    return copied


def copy_latest_data(data):
    return {
        "angle": data["angle"],
        "raw_distance_cm": data["raw_distance_cm"],
        "filtered_distance_cm": data["filtered_distance_cm"],
    }


def settings_to_dict(settings):
    return {
        "step_degrees": settings.step_degrees,
        "step_delay_ms": settings.step_delay_ms,
        "measure_every_degrees": settings.measure_every_degrees,
        "mqtt_every_measurements": settings.mqtt_every_measurements,
    }


def sync_sensor_state(shared, lock, angle, latest_data):
    lock.acquire()
    try:
        shared["angle"] = angle
        shared["latest_data"] = copy_latest_data(latest_data)
    finally:
        lock.release()


def handle_encoder_input(encoder, menu, settings):
    step = encoder.read_step()
    if step:
        menu.handle_rotation(step, settings)

    button_event = encoder.read_button_event()
    if button_event == "pressed":
        menu.handle_button()


def display_loop(shared, lock):
    oled = SSD1306_SPI()
    encoder = RotaryEncoder()
    menu = MenuController()
    settings = RuntimeSettings()
    last_age_ms = utime.ticks_ms()
    last_draw_ms = 0

    while True:
        handle_encoder_input(encoder, menu, settings)

        now_ms = utime.ticks_ms()
        lock.acquire()
        try:
            if not shared["running"]:
                break
            shared["settings"] = settings_to_dict(settings)

            if utime.ticks_diff(now_ms, last_age_ms) >= DISPLAY_UPDATE_MS:
                age_scan_points(shared["scan_points"])
                last_age_ms = now_ms

            if utime.ticks_diff(now_ms, last_draw_ms) < DISPLAY_LOOP_MS:
                should_draw = False
            else:
                should_draw = True
                last_draw_ms = now_ms

            angle = shared["angle"]
            scan_points = copy_scan_points(shared["scan_points"])
            latest_data = copy_latest_data(shared["latest_data"])
        finally:
            lock.release()

        if not should_draw:
            utime.sleep_ms(DISPLAY_POLL_MS)
            continue

        if menu.view == VIEW_RADAR:
            draw_radar(oled, angle, scan_points)
        elif menu.view == VIEW_DATA:
            draw_data_view(oled, latest_data, settings)
        elif menu.view == VIEW_SELECT:
            draw_menu(oled, "Menu", MENU_ITEMS, menu.menu_index)
        elif menu.view == VIEW_SETTINGS:
            draw_settings_view(oled, menu, settings)
        elif menu.view == VIEW_EDIT_SETTING:
            draw_edit_setting(oled, menu, settings)

        utime.sleep_ms(DISPLAY_POLL_MS)


def run():
    led = Pin("LED", Pin.OUT)
    servo = None
    mqtt_client = None
    lock = _thread.allocate_lock()

    angle_history = {}
    scan_points = {}
    latest_data = {
        "angle": 0,
        "raw_distance_cm": None,
        "filtered_distance_cm": None,
    }
    measurement_count = 0
    last_ping_ms = 0

    initial_settings = RuntimeSettings()
    shared = {
        "running": True,
        "angle": 0,
        "scan_points": scan_points,
        "latest_data": copy_latest_data(latest_data),
        "settings": settings_to_dict(initial_settings),
    }

    try:
        ip_address = connect_wifi()
        mqtt_client = connect_mqtt("microradar-threaded-" + ip_address)
        publish_status(mqtt_client, TOPIC_STATUS, b"online")

        sensor = DistanceSensor()
        servo = Servo()
        _thread.start_new_thread(display_loop, (shared, lock))

        for angle in scan_angles(MIN_ANGLE, MAX_ANGLE, STEP_DEGREES):
            lock.acquire()
            try:
                settings = SettingsSnapshot(shared["settings"])
            finally:
                lock.release()

            servo.set_angle(angle)
            utime.sleep_ms(settings.step_delay_ms)

            sync_sensor_state(
                shared,
                lock,
                angle,
                latest_data,
            )

            if (angle - MIN_ANGLE) % settings.measure_every_degrees != 0:
                continue

            now_ms = utime.ticks_ms()
            if utime.ticks_diff(now_ms, last_ping_ms) < PING_DELAY_MS:
                continue
            last_ping_ms = now_ms

            distance_cm, _, _ = sensor.read_once_cm()
            filtered_distance_cm = update_angle_history(
                angle_history,
                angle,
                distance_cm,
            )
            latest_data["angle"] = angle
            latest_data["raw_distance_cm"] = distance_cm
            latest_data["filtered_distance_cm"] = filtered_distance_cm
            lock.acquire()
            try:
                set_scan_point(scan_points, angle, filtered_distance_cm)
            finally:
                lock.release()

            measurement_count += 1
            if measurement_count % settings.mqtt_every_measurements == 0:
                publish_scan_point(
                    mqtt_client,
                    TOPIC_ANGLE,
                    TOPIC_DISTANCE,
                    angle,
                    filtered_distance_cm,
                )

            sync_sensor_state(
                shared,
                lock,
                angle,
                latest_data,
            )

            print("angle={} raw={} filtered={}".format(
                angle,
                distance_cm,
                filtered_distance_cm,
            ))
            led.toggle()

    except KeyboardInterrupt:
        print("Stopping threaded display test.")

    finally:
        lock.acquire()
        try:
            shared["running"] = False
        finally:
            lock.release()
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
