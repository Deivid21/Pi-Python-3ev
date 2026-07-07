#!/usr/bin/env python3
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

from enum import Enum, auto
from signal import SIGINT, SIGTERM, signal
from time import monotonic, perf_counter, sleep

import RPi.GPIO as GPIO

# BCM GPIO numbering
BUTTON_PIN = 22
BUZZER_PIN = 25
GREEN_LED_PIN = 17
RED_LED_PIN = 27
YELLOW_LED_PIN = 23
BLUE_LED_PIN = 24
POTENTIOMETER_PIN = 18

# Temperature thresholds
NORMAL_LIMIT_C = 40.0
CRITICAL_LIMIT_C = 70.0

# Button timing
LONG_PRESS_SECONDS = 3.0
DOUBLE_CLICK_SECONDS = 0.45
MAINTENANCE_TIMEOUT_SECONDS = 30.0

# Output timing
WARNING_BLINK_SECONDS = 0.50
WARNING_BUZZER_PERIOD_SECONDS = 2.0
WARNING_BUZZER_ON_SECONDS = 0.20
CRITICAL_BLINK_SECONDS = 0.20
SENSOR_ERROR_BLINK_SECONDS = 0.35

# RC potentiometer reading
# Adjust these two values after observing the raw RC time at both ends.
RC_MIN_SECONDS = 0.001
RC_MAX_SECONDS = 0.020
RC_TIMEOUT_SECONDS = 0.100
RC_DISCHARGE_SECONDS = 0.005
INVERT_POTENTIOMETER = False

SENSOR_INTERVAL_SECONDS = 0.10
DISPLAY_INTERVAL_SECONDS = 0.50
LOOP_INTERVAL_SECONDS = 0.005

class SystemState(Enum):
    OFF = auto()
    NORMAL = auto()
    WARNING = auto()
    CRITICAL = auto()
    MAINTENANCE = auto()
    SENSOR_ERROR = auto()

running = True
system_enabled = False
maintenance_mode = False
maintenance_last_activity = 0.0

current_state = SystemState.OFF
temperature_c = 0.0
raw_rc_seconds = 0.0
sensor_error = False

previous_button_state = False
press_started_at = None
long_press_handled = False
click_count = 0
last_click_released_at = 0.0

last_output_toggle_at = 0.0
output_phase = False
last_sensor_read_at = 0.0
last_display_at = 0.0
last_displayed_state = None

def configure_gpio():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    GPIO.setup(GREEN_LED_PIN, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(RED_LED_PIN, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(YELLOW_LED_PIN, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(BLUE_LED_PIN, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(BUZZER_PIN, GPIO.OUT, initial=GPIO.LOW)

    # Button connected between GPIO22 and 3.3 V.
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

def set_outputs(
    green=False,
    red=False,
    yellow=False,
    blue=False,
    sound=False,
):
    GPIO.output(GREEN_LED_PIN, GPIO.HIGH if green else GPIO.LOW)
    GPIO.output(RED_LED_PIN, GPIO.HIGH if red else GPIO.LOW)
    GPIO.output(YELLOW_LED_PIN, GPIO.HIGH if yellow else GPIO.LOW)
    GPIO.output(BLUE_LED_PIN, GPIO.HIGH if blue else GPIO.LOW)
    GPIO.output(BUZZER_PIN, GPIO.HIGH if sound else GPIO.LOW)

def stop_program(_signal_number=None, _frame=None):
    global running
    running = False

def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))

def measure_rc_charge_time():
    """
    Measure the charge time of the capacitor connected to GPIO16.

    Circuit:
      3.3 V -> potentiometer -> 4.7 kOhm resistor -> GPIO16
      GPIO16 -> 1 uF capacitor -> GND

    The Raspberry Pi has no analog input. This RC method estimates the
    potentiometer position from the capacitor charge time.
    """
    GPIO.setup(POTENTIOMETER_PIN, GPIO.OUT, initial=GPIO.LOW)
    sleep(RC_DISCHARGE_SECONDS)

    GPIO.setup(POTENTIOMETER_PIN, GPIO.IN)

    started_at = perf_counter()

    while GPIO.input(POTENTIOMETER_PIN) == GPIO.LOW:
        elapsed = perf_counter() - started_at

        if elapsed >= RC_TIMEOUT_SECONDS:
            return None

    return perf_counter() - started_at

def update_temperature(now):
    global last_sensor_read_at
    global temperature_c
    global raw_rc_seconds
    global sensor_error

    if now - last_sensor_read_at < SENSOR_INTERVAL_SECONDS:
        return

    last_sensor_read_at = now
    measured_time = measure_rc_charge_time()

    if measured_time is None:
        sensor_error = True
        return

    raw_rc_seconds = measured_time

    normalized = (
        measured_time - RC_MIN_SECONDS
    ) / (
        RC_MAX_SECONDS - RC_MIN_SECONDS
    )

    normalized = clamp(normalized, 0.0, 1.0)

    if INVERT_POTENTIOMETER:
        normalized = 1.0 - normalized

    new_temperature = normalized * 100.0

    # Light filtering to prevent LED flickering near thresholds.
    temperature_c = (temperature_c * 0.70) + (new_temperature * 0.30)
    sensor_error = False

def reset_system():
    global system_enabled
    global maintenance_mode
    global current_state
    global click_count
    global output_phase

    system_enabled = False
    maintenance_mode = False
    current_state = SystemState.OFF
    click_count = 0
    output_phase = False

    set_outputs()

    print("\nSYSTEM RESET")
    print("System returned to OFF state.")

def execute_single_click(now):
    global system_enabled
    global maintenance_mode
    global maintenance_last_activity

    system_enabled = not system_enabled
    maintenance_mode = False
    maintenance_last_activity = now

    print(f"\nSystem: {'ON' if system_enabled else 'OFF'}")

def execute_double_click(now):
    global system_enabled
    global maintenance_mode
    global maintenance_last_activity

    system_enabled = True
    maintenance_mode = not maintenance_mode
    maintenance_last_activity = now

    print(f"\nMaintenance mode: {'ON' if maintenance_mode else 'OFF'}")

def update_button(now):
    global previous_button_state
    global press_started_at
    global long_press_handled
    global click_count
    global last_click_released_at
    global maintenance_last_activity

    is_pressed = GPIO.input(BUTTON_PIN) == GPIO.HIGH

    if is_pressed and not previous_button_state:
        press_started_at = now
        long_press_handled = False
        maintenance_last_activity = now

    if (
        is_pressed
        and press_started_at is not None
        and not long_press_handled
        and now - press_started_at >= LONG_PRESS_SECONDS
    ):
        reset_system()
        long_press_handled = True
        click_count = 0

    if not is_pressed and previous_button_state:
        if not long_press_handled:
            click_count += 1
            last_click_released_at = now

        press_started_at = None
        long_press_handled = False

    if (
        click_count > 0
        and not is_pressed
        and now - last_click_released_at >= DOUBLE_CLICK_SECONDS
    ):
        if click_count >= 2:
            execute_double_click(now)
        else:
            execute_single_click(now)

        click_count = 0

    previous_button_state = is_pressed

def update_state(now):
    global current_state
    global maintenance_mode

    if not system_enabled:
        current_state = SystemState.OFF
        return

    if sensor_error:
        current_state = SystemState.SENSOR_ERROR
        return

    if maintenance_mode:
        if now - maintenance_last_activity >= MAINTENANCE_TIMEOUT_SECONDS:
            maintenance_mode = False
            print("\nMaintenance timeout: returning to automatic operation.")
        else:
            current_state = SystemState.MAINTENANCE
            return

    if temperature_c < NORMAL_LIMIT_C:
        current_state = SystemState.NORMAL
    elif temperature_c <= CRITICAL_LIMIT_C:
        current_state = SystemState.WARNING
    else:
        current_state = SystemState.CRITICAL

def update_outputs(now):
    global last_output_toggle_at
    global output_phase

    if current_state == SystemState.OFF:
        set_outputs()
        return

    if current_state == SystemState.NORMAL:
        set_outputs(green=True)
        return

    if current_state == SystemState.MAINTENANCE:
        set_outputs(blue=True)
        return

    if current_state == SystemState.WARNING:
        if now - last_output_toggle_at >= WARNING_BLINK_SECONDS:
            output_phase = not output_phase
            last_output_toggle_at = now

        buzzer_position = now % WARNING_BUZZER_PERIOD_SECONDS

        set_outputs(
            yellow=output_phase,
            sound=buzzer_position < WARNING_BUZZER_ON_SECONDS,
        )
        return

    if current_state == SystemState.CRITICAL:
        if now - last_output_toggle_at >= CRITICAL_BLINK_SECONDS:
            output_phase = not output_phase
            last_output_toggle_at = now

        set_outputs(
            red=output_phase,
            sound=True,
        )
        return

    if current_state == SystemState.SENSOR_ERROR:
        if now - last_output_toggle_at >= SENSOR_ERROR_BLINK_SECONDS:
            output_phase = not output_phase
            last_output_toggle_at = now

        set_outputs(
            red=output_phase,
            yellow=not output_phase,
            sound=output_phase,
        )

def update_terminal(now):
    global last_display_at
    global last_displayed_state

    state_changed = current_state != last_displayed_state
    interval_elapsed = now - last_display_at >= DISPLAY_INTERVAL_SECONDS

    if not state_changed and not interval_elapsed:
        return

    print(
        f"\rTemperature: {temperature_c:6.2f} C | "
        f"RC: {raw_rc_seconds * 1000:7.3f} ms | "
        f"State: {current_state.name:<12}",
        end="",
        flush=True,
    )

    last_display_at = now
    last_displayed_state = current_state

def main():
    configure_gpio()

    signal(SIGINT, stop_program)
    signal(SIGTERM, stop_program)

    print("Industrial monitoring system")
    print("Single click: turn system ON/OFF")
    print("Double click: toggle maintenance mode")
    print("Hold for 3 seconds: reset system")
    print("Potentiometer input: RC timing on GPIO16\n")

    try:
        while running:
            now = monotonic()

            update_button(now)
            update_temperature(now)
            update_state(now)
            update_outputs(now)
            update_terminal(now)

            sleep(LOOP_INTERVAL_SECONDS)

    finally:
        set_outputs()
        GPIO.cleanup()
        print("\nProgram stopped. GPIO outputs are OFF.")

if __name__ == "__main__":
    main()
