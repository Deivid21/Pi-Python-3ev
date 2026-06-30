## 2

from gpiozero import LED, Button
from signal import pause

green = LED(17)
red = LED(27)
yellow = LED(23)

button = Button(
    22,
    pull_up=False,
    bounce_time=0.3
)

def toggle_leds():
    green.toggle()
    red.toggle()
    yellow.toggle()

button.when_pressed = toggle_leds

pause()
