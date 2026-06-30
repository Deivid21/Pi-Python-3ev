## 3

from gpiozero import LED, Button
from time import sleep, monotonic

# LEDs - BCM numbering
green = LED(17)
red = LED(27)
yellow = LED(23)

# Button connected between GPIO 22 and GND
button = Button(
    22,
    pull_up=False,
    bounce_time=0.05
)

def turn_off_leds():
    green.off()
    yellow.off()
    red.off()

def wait_while_pressed(seconds):
    end_time = monotonic() + seconds

    while monotonic() < end_time:
        if not button.is_pressed:
            turn_off_leds()
            return False

        sleep(0.02)
    return True

while True:
    # Wait until the button is pressed
    button.wait_for_press()

    while button.is_pressed:
        # Green ON
        turn_off_leds()
        green.on()

        if not wait_while_pressed(1):
            break

        # Yellow ON
        turn_off_leds()
        yellow.on()

        if not wait_while_pressed(1):
            break

        # Red ON
        turn_off_leds()
        red.on()

        if not wait_while_pressed(1):
            break

    # Button released
    turn_off_leds()
