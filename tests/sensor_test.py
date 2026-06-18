from config import (
    ECHO_PIN,
    PING_DELAY_MS,
    SAMPLES,
    TRIG_PIN,
)
from sensor import DistanceSensor


def main():
    sensor = DistanceSensor()

    print("HY-SRF05 sensor test")
    print("TRIG GP{}, ECHO GP{} via voltage divider".format(TRIG_PIN, ECHO_PIN))
    print("{} samples, {}ms between pings".format(SAMPLES, PING_DELAY_MS))
    print("Press Ctrl+C to stop.")

    while True:
        try:
            distance, duration_us, idle_before = sensor.read_distance_debug()
            if distance is None:
                print("invalid duration={} idle={}".format(duration_us, idle_before))
            else:
                print("{:.1f} cm  source={} valid_samples={}".format(
                    distance,
                    duration_us,
                    idle_before,
                ))
        except KeyboardInterrupt:
            break

    print("Sensor test stopped.")


if __name__ == "__main__":
    main()
