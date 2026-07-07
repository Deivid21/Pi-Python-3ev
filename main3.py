##
## For more Support see: https://t.me/Deivid21Hub
##
## Copyright (C) 1996 - 2026 INACAP
## Copyright (C) 2017 - 2026 Deivid Ignacio Parra (Deivid21)
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
##
##      http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.
##

from gpiozero import LED, Button
from time import sleep, monotonic

# GPIO LEDs
green = LED(17)
red = LED(27)
yellow = LED(23)

# GPIO Button
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
