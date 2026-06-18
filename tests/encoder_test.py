from utime import sleep_ms

from encoder import ENC_A_PIN, ENC_B_PIN, ENC_SW_PIN, RotaryEncoder


def main():
    encoder = RotaryEncoder()
    position = 0
    last_button_value = encoder.button_value()

    print("Rotary encoder test")
    print("A GP{}, B GP{}, SW GP{}".format(ENC_A_PIN, ENC_B_PIN, ENC_SW_PIN))
    print("Turn encoder or press button. Press Ctrl+C to stop.")

    try:
        while True:
            step = encoder.read_step()
            if step:
                position += step
                print("position={} step={}".format(position, step))

            event = encoder.read_button_event()
            if event is not None:
                print("button={}".format(event))

            button_value = encoder.button_value()
            if button_value != last_button_value:
                print("raw SW={}".format(button_value))
                last_button_value = button_value

            sleep_ms(2)

    except KeyboardInterrupt:
        print("Encoder test stopped.")


if __name__ == "__main__":
    main()
