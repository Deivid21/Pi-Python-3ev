from gpiozero import LED, Button
from signal import pause

led1 = LED(17)
led2 = LED(27)
led3 = LED(23)

button = Button(
    22,
    pull_up=False,
    bounce_time=0.3
)

def toggle_leds():
    led1.toggle()
    led2.toggle()
    led3.toggle()

button.when_pressed = toggle_leds

pause()
