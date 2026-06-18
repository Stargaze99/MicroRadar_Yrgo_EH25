from config import MEASURE_EVERY_DEGREES, STEP_DELAY_MS, STEP_DEGREES


VIEW_RADAR = 0
VIEW_DATA = 1
VIEW_SELECT = 2
VIEW_SETTINGS = 3
VIEW_EDIT_SETTING = 4

MENU_ITEMS = ("Radar view", "Data list", "Settings")
SETTING_SERVO_DELAY = 0
SETTING_MEASURE_EVERY = 1
SETTING_MQTT_EVERY = 2
SETTING_BACK = 3
SETTING_ITEMS = ("Servo speed", "Measure every", "MQTT every", "Back")


class RuntimeSettings:
    # Settings are changed from the UI thread and read by the main thread.
    # These values are runtime-only; they are not written back to config.py.
    def __init__(self):
        self.step_degrees = STEP_DEGREES
        self.step_delay_ms = STEP_DELAY_MS
        self.measure_every_degrees = MEASURE_EVERY_DEGREES
        self.mqtt_every_measurements = 1

    def servo_speed_dps(self):
        if self.step_delay_ms <= 0:
            return 0
        return int(self.step_degrees * 1000 / self.step_delay_ms)


class MenuController:
    # Small state machine for top-level views, settings list, and edit mode.
    #
    # VIEW_RADAR / VIEW_DATA:
    #   Encoder rotation opens the top-level menu.
    # VIEW_SELECT:
    #   Rotation chooses Radar view, Data list, or Settings.
    # VIEW_SETTINGS:
    #   Rotation chooses which setting to edit.
    # VIEW_EDIT_SETTING:
    #   Rotation changes the selected setting value.
    def __init__(self):
        self.view = VIEW_RADAR
        self.previous_view = VIEW_RADAR
        self.menu_index = 0
        self.setting_index = 0
        self.edit_index = 0

    def handle_rotation(self, step, settings):
        # Rotation either opens the top menu, moves a cursor, or changes the
        # currently edited value.
        # The same encoder is reused for navigation and editing based on state.
        if step == 0:
            return

        if self.view == VIEW_RADAR or self.view == VIEW_DATA:
            self.previous_view = self.view
            self.view = VIEW_SELECT
            self.menu_index = self.previous_view
            self.menu_index = self._wrap(self.menu_index + step, len(MENU_ITEMS))
        elif self.view == VIEW_SELECT:
            self.menu_index = self._wrap(self.menu_index + step, len(MENU_ITEMS))
        elif self.view == VIEW_SETTINGS:
            self.setting_index = self._wrap(self.setting_index + step, len(SETTING_ITEMS))
        elif self.view == VIEW_EDIT_SETTING:
            self._change_setting(step, settings)

    def handle_button(self):
        # The encoder button works as Enter. Back is represented as a normal
        # selectable settings item.
        # Pressing while editing confirms the value and returns to settings.
        if self.view == VIEW_SELECT:
            if self.menu_index == 0:
                self.view = VIEW_RADAR
            elif self.menu_index == 1:
                self.view = VIEW_DATA
            else:
                self.view = VIEW_SETTINGS
                self.setting_index = 0
        elif self.view == VIEW_SETTINGS:
            if self.setting_index == SETTING_BACK:
                self.view = VIEW_SELECT
            else:
                self.edit_index = self.setting_index
                self.view = VIEW_EDIT_SETTING
        elif self.view == VIEW_EDIT_SETTING:
            self.view = VIEW_SETTINGS
        elif self.view == VIEW_DATA:
            self.view = VIEW_SELECT

    def _change_setting(self, step, settings):
        # Positive step means higher displayed servo speed, so the underlying
        # delay is reduced.
        # Values are clamped to avoid unusable extremes, for example a delay so
        # high that the radar appears frozen or so low that the servo is pushed
        # too aggressively.
        if self.edit_index == SETTING_SERVO_DELAY:
            settings.step_delay_ms = self._clamp(
                settings.step_delay_ms - step * 5,
                10,
                100,
            )
        elif self.edit_index == SETTING_MEASURE_EVERY:
            settings.measure_every_degrees = self._clamp(
                settings.measure_every_degrees + step,
                1,
                10,
            )
        elif self.edit_index == SETTING_MQTT_EVERY:
            settings.mqtt_every_measurements = self._clamp(
                settings.mqtt_every_measurements + step,
                1,
                20,
            )

    def _wrap(self, value, count):
        return value % count

    def _clamp(self, value, minimum, maximum):
        return max(minimum, min(maximum, value))


def draw_menu(oled, title, items, selected_index):
    # Generic compact list view for the 128x64 OLED.
    oled.fill(0)
    oled.text(title, 0, 0, 1)
    y = 14
    for index, item in enumerate(items):
        prefix = ">" if index == selected_index else " "
        oled.text(prefix + item, 0, y, 1)
        y += 12
    oled.show()


def draw_data_view(oled, data, settings):
    # Live data view for current angle, raw distance, filtered distance,
    # servo speed, and MQTT publish rate.
    oled.fill(0)
    oled.text("Data list", 0, 0, 1)
    oled.text("Angle: {} deg".format(data["angle"]), 0, 12, 1)
    oled.text("Raw:   {}".format(format_cm(data["raw_distance_cm"])), 0, 24, 1)
    oled.text("Filt:  {}".format(format_cm(data["filtered_distance_cm"])), 0, 36, 1)
    oled.text("Spd:{} Mqtt:{}".format(
        settings.servo_speed_dps(),
        settings.mqtt_every_measurements,
    ), 0, 48, 1)
    oled.show()


def draw_settings_view(oled, controller, settings):
    # Settings are shown as a list with the live value next to each item.
    # Text is truncated to 16 characters because the OLED font is 8 px wide.
    oled.fill(0)
    oled.text("Settings", 0, 0, 1)
    y = 14
    for index, item in enumerate(SETTING_ITEMS):
        prefix = ">" if index == controller.setting_index else " "
        if index == SETTING_SERVO_DELAY:
            text = "{}{} {}d/s".format(prefix, item, settings.servo_speed_dps())
        elif index == SETTING_MEASURE_EVERY:
            text = "{}{} {}deg".format(prefix, item, settings.measure_every_degrees)
        elif index == SETTING_MQTT_EVERY:
            text = "{}{} {}".format(prefix, item, settings.mqtt_every_measurements)
        else:
            text = prefix + item
        oled.text(text[:16], 0, y, 1)
        y += 12
    oled.show()


def draw_edit_setting(oled, controller, settings):
    # Edit view uses the full screen for one value so it is readable while the
    # encoder is being rotated.
    oled.fill(0)
    oled.text("Edit setting", 0, 0, 1)
    if controller.edit_index == SETTING_SERVO_DELAY:
        oled.text("Servo speed", 0, 18, 1)
        oled.text("{} deg/s".format(settings.servo_speed_dps()), 0, 34, 1)
        oled.text("delay {}ms".format(settings.step_delay_ms), 0, 50, 1)
    elif controller.edit_index == SETTING_MEASURE_EVERY:
        oled.text("Measure every", 0, 18, 1)
        oled.text("{} deg".format(settings.measure_every_degrees), 0, 34, 1)
    elif controller.edit_index == SETTING_MQTT_EVERY:
        oled.text("MQTT every", 0, 18, 1)
        oled.text("{} samples".format(settings.mqtt_every_measurements), 0, 34, 1)
    oled.show()


def format_cm(value):
    if value is None:
        return "--"
    return "{:.1f}cm".format(value)
