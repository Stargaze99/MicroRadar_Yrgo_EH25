import _thread
import utime

from config import DISPLAY_UPDATE_MS
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
from oled import SSD1306_SPI
from radar_display import draw_radar


DISPLAY_LOOP_MS = 25
DISPLAY_POLL_MS = 5


def handle_encoder_input(encoder, menu, settings):
    # Encoder rotation changes menu selection or edited settings.
    # Pressing the encoder works as Enter.
    step = encoder.read_step()
    if step:
        menu.handle_rotation(step, settings)

    button_event = encoder.read_button_event()
    if button_event == "pressed":
        menu.handle_button()


def display_loop(state):
    # UI thread: owns OLED, encoder, menu state, and runtime settings.
    # The main thread must not write to OLED directly.
    oled = SSD1306_SPI()
    encoder = RotaryEncoder()
    menu = MenuController()
    settings = RuntimeSettings()
    last_age_ms = utime.ticks_ms()
    last_draw_ms = 0

    while state.is_running():
        handle_encoder_input(encoder, menu, settings)
        state.update_settings(settings)

        now_ms = utime.ticks_ms()
        if utime.ticks_diff(now_ms, last_age_ms) >= DISPLAY_UPDATE_MS:
            state.age_scan_points()
            last_age_ms = now_ms

        # Encoder is polled every loop, but OLED rendering is throttled.
        if utime.ticks_diff(now_ms, last_draw_ms) < DISPLAY_LOOP_MS:
            utime.sleep_ms(DISPLAY_POLL_MS)
            continue
        last_draw_ms = now_ms

        # Drawing happens from a copied snapshot so OLED/SPI transfer time does
        # not block servo, sensor, or MQTT work.
        angle, scan_points, latest_data = state.get_display_snapshot()

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


def start_ui_thread(state):
    _thread.start_new_thread(display_loop, (state,))
