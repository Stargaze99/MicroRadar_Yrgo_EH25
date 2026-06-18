# =========================
# WiFi settings
# =========================
SSID = "YOUR_WIFI_SSID"
PASSWORD = "YOUR_WIFI_PASSWORD"

# =========================
# MQTT settings
# =========================
MQTT_SERVER = "YOUR_MQTT_BROKER_IP"
MQTT_PORT = 1883

MQTT_USERNAME = "YOUR_MQTT_USERNAME"
MQTT_PASSWORD = "YOUR_MQTT_PASSWORD"

# =========================
# Sensor settings
# =========================
TRIG_PIN = 2
ECHO_PIN = 3

TRIGGER_US = 10
ECHO_TIMEOUT_US = 30_000
MIN_DISTANCE_CM = 2
MAX_DISTANCE_CM = 450
PING_DELAY_MS = 35
SAMPLES = 3
FILTER_WINDOW = 3

# =========================
# Servo settings
# =========================
SERVO_PIN = 4

# Conservative MG90S pulse range for first hardware tests.
# If the servo buzzes at the ends, narrow these values.
SERVO_MIN_US = 500
SERVO_MAX_US = 2500

MIN_ANGLE = 0
MAX_ANGLE = 180
STEP_DEGREES = 1
STEP_DELAY_MS = 40
MEASURE_EVERY_DEGREES = 1
DISPLAY_UPDATE_MS = 1000
DOT_MAX_AGE = 4

# =========================
# OLED SPI settings
# =========================
OLED_WIDTH = 128
OLED_HEIGHT = 64
OLED_SPI_ID = 0
OLED_SCK_PIN = 6
OLED_MOSI_PIN = 7
OLED_RES_PIN = 8
OLED_DC_PIN = 9
OLED_CS_PIN = 10

# =========================
# Rotary encoder settings
# =========================
ENC_A_PIN = 20
ENC_B_PIN = 21
ENC_SW_PIN = 22
