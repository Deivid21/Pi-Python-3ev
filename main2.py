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
from signal import pause

# GPIO LEDs
green = LED(17)
red = LED(27)
yellow = LED(23)

# GPIO Button
button = Button(
    22,
    pull_up=False,
    bounce_time=0.3
)

# Toggle LEDs function
def toggle_leds():
    green.toggle()
    red.toggle()
    yellow.toggle()

button.when_pressed = toggle_leds

pause()
