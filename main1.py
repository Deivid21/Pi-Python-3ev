## 1

from gpiozero import LED
from time import sleep

# GPIO usando numeración BCM
green = LED(17)
red = LED(27)
yellow = LED(23)

while True:
    # Green ON
    green.on()
    sleep(1)

    # Green OFF, yellow ON
    green.off()
    yellow.on()
    sleep(1)

    # Yellow OFF, red ON
    yellow.off()
    red.on()
    sleep(1)

    # Red OFF, yellow ON
    red.off()
    yellow.on()
    sleep(1)

    # Yellow OFF, red ON
    yellow.off()
    green.on()
    sleep(1)

    # Red OFF, yellow ON
    green.off()
