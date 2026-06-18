import _thread

from config import DOT_MAX_AGE
from menu import RuntimeSettings


class SettingsSnapshot:
    # Immutable copy of UI-controlled settings used by the main thread.
    # The UI thread owns RuntimeSettings. The main thread copies settings once
    # per servo step so values cannot change halfway through one iteration.
    def __init__(self, data):
        self.step_degrees = data["step_degrees"]
        self.step_delay_ms = data["step_delay_ms"]
        self.measure_every_degrees = data["measure_every_degrees"]
        self.mqtt_every_measurements = data["mqtt_every_measurements"]

    def servo_speed_dps(self):
        if self.step_delay_ms <= 0:
            return 0
        return int(self.step_degrees * 1000 / self.step_delay_ms)


def settings_to_dict(settings):
    # Only plain dictionaries are shared between threads. This avoids sharing
    # mutable class instances across cores and keeps locking predictable.
    return {
        "step_degrees": settings.step_degrees,
        "step_delay_ms": settings.step_delay_ms,
        "measure_every_degrees": settings.measure_every_degrees,
        "mqtt_every_measurements": settings.mqtt_every_measurements,
    }


def copy_latest_data(data):
    return {
        "angle": data["angle"],
        "raw_distance_cm": data["raw_distance_cm"],
        "filtered_distance_cm": data["filtered_distance_cm"],
    }


def copy_scan_points(scan_points):
    # The display thread works on a copy to avoid holding the shared lock while
    # drawing to the OLED. SPI drawing is slow compared to dictionary copying.
    copied = {}
    for angle, point in scan_points.items():
        copied[angle] = {
            "distance_cm": point["distance_cm"],
            "age": point["age"],
        }
    return copied


class AppState:
    # Thread-safe shared state between:
    # - main thread: servo, sensor, MQTT
    # - UI thread: OLED, encoder, menu, settings
    def __init__(self):
        self.lock = _thread.allocate_lock()
        self.running = True
        self.angle = 0
        self.scan_points = {}
        self.latest_data = {
            "angle": 0,
            "raw_distance_cm": None,
            "filtered_distance_cm": None,
        }
        self.settings = settings_to_dict(RuntimeSettings())

    def stop(self):
        self.lock.acquire()
        try:
            self.running = False
        finally:
            self.lock.release()

    def is_running(self):
        self.lock.acquire()
        try:
            return self.running
        finally:
            self.lock.release()

    def get_settings(self):
        self.lock.acquire()
        try:
            return SettingsSnapshot(self.settings)
        finally:
            self.lock.release()

    def update_settings(self, settings):
        self.lock.acquire()
        try:
            self.settings = settings_to_dict(settings)
        finally:
            self.lock.release()

    def update_angle(self, angle):
        self.lock.acquire()
        try:
            self.angle = angle
        finally:
            self.lock.release()

    def update_measurement(self, angle, raw_distance_cm, filtered_distance_cm):
        self.lock.acquire()
        try:
            self.angle = angle
            self.latest_data = {
                "angle": angle,
                "raw_distance_cm": raw_distance_cm,
                "filtered_distance_cm": filtered_distance_cm,
            }
            if filtered_distance_cm is not None:
                self.scan_points[angle] = {
                    "distance_cm": filtered_distance_cm,
                    "age": DOT_MAX_AGE,
                }
        finally:
            self.lock.release()

    def age_scan_points(self):
        # Called by the UI thread once per display update interval. Expired
        # keys are collected first because deleting while iterating is unsafe.
        self.lock.acquire()
        try:
            expired_angles = []
            for angle, point in self.scan_points.items():
                point["age"] -= 1
                if point["age"] <= 0:
                    expired_angles.append(angle)

            for angle in expired_angles:
                del self.scan_points[angle]
        finally:
            self.lock.release()

    def get_display_snapshot(self):
        # Copy all data needed for one OLED draw while holding the lock briefly.
        self.lock.acquire()
        try:
            return (
                self.angle,
                copy_scan_points(self.scan_points),
                copy_latest_data(self.latest_data),
            )
        finally:
            self.lock.release()
