import network
import utime
from umqtt.simple import MQTTClient

from config import MQTT_PASSWORD, MQTT_PORT, MQTT_SERVER, MQTT_USERNAME, PASSWORD, SSID


def connect_wifi():
    # WiFi is connected once during startup before MQTT is used.
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(SSID, PASSWORD)

        while not wlan.isconnected():
            print(".", end="")
            utime.sleep(0.5)

    ip_address = wlan.ifconfig()[0]
    print()
    print("WiFi connected")
    print("IP address:", ip_address)
    return ip_address


def connect_mqtt(client_id):
    # MQTT credentials are configured in config.py.
    print("Connecting to MQTT...")
    mqtt_client = MQTTClient(
        client_id=client_id,
        server=MQTT_SERVER,
        port=MQTT_PORT,
        user=MQTT_USERNAME,
        password=MQTT_PASSWORD,
    )
    mqtt_client.connect()
    print("MQTT connected")
    return mqtt_client


def publish_status(mqtt_client, topic, status):
    # Retained status lets the dashboard see the latest online/offline state.
    mqtt_client.publish(topic, status, retain=True)


def publish_scan_point(mqtt_client, angle_topic, distance_topic, angle, distance_cm):
    # Angle is always published. Distance is skipped when the sensor reading
    # was invalid.
    mqtt_client.publish(angle_topic, str(angle))

    if distance_cm is not None:
        mqtt_client.publish(distance_topic, "{:.1f}".format(distance_cm))
