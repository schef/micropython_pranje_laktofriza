import asyncio
import common_pins
import leds
import sensors
from common import get_millis, millis_passed

in_progress_status = False
start_timestamp = 0
current_state = ""
timeout = 0

mixer_timestamp = 0
mixer_periodic_timestamp = 0
delay_timestamp = 0

mixer_timeout = 15 * 60 * 1000
mixer_periodic_timeout = 15 * 60 * 1000
delay_timeout = 20 * 60 * 1000

def init():
    print("[CL]: init")
    stop()

def start():
    print("[CL]: start")
    global in_progress_status
    in_progress_status = True

def stop():
    print("[CL]: stop")
    global in_progress_status, delay_timestamp
    in_progress_status = False
    leds.set_state_by_name(common_pins.KOMPRESOR.name, 0)
    leds.set_state_by_name(common_pins.MIXER.name, 0)
    delay_timestamp = 0

def in_progress():
    return in_progress_status

def is_mixing():
    return False

def set_mixing():
    global mixer_timestamp, mixer_periodic_timestamp, delay_timestamp
    mixer_periodic_timestamp = 0
    mixer_timestamp = get_millis()
    delay_timestamp = 0

def set_delay():
    print("[CL]: set_delay")
    global delay_timestamp
    delay_timestamp = get_millis()

def get_temperature():
    temperature = sensors.environment_sensors[0].get_temperature()
    if temperature is not None:
        if temperature >= 50.0:
            return None
        if temperature <= -5.0:
            return None
    return temperature

async def loop():
    print("[CL]: loop")
    global mixer_timestamp, mixer_periodic_timestamp, delay_timestamp
    kompresor = leds.get_led_by_name(common_pins.KOMPRESOR.name)
    mixer = leds.get_led_by_name(common_pins.MIXER.name)
    while True:
        if in_progress_status:
            if delay_timestamp != 0:
                if kompresor.get_state() == 1:
                    kompresor.set_state(0)
                if mixer.get_state() == 1:
                    mixer.set_state(0)
                if millis_passed(delay_timestamp) >= delay_timeout:
                    delay_timestamp = 0
                await asyncio.sleep(1)
                continue
            temperature = get_temperature()
            if temperature is not None:
                if kompresor.get_state() == 0:
                    if temperature > 5.0:
                        kompresor.set_state(1)
                    if mixer_timestamp == 0 and mixer_periodic_timestamp == 0:
                        set_mixing()
                else:
                    set_mixing()
                    if temperature < 3.5:
                        kompresor.set_state(0)

                if mixer.get_state() == 0:
                    if mixer_timestamp != 0:
                        mixer.set_state(1)

                    if mixer_periodic_timestamp != 0 and millis_passed(mixer_periodic_timestamp) >= mixer_periodic_timeout:
                        mixer_periodic_timestamp = 0
                        set_mixing()
                else:
                    if mixer_timestamp != 0 and millis_passed(mixer_timestamp) >= mixer_timeout:
                        mixer_periodic_timestamp = get_millis()
                        mixer_timestamp = 0
                        mixer.set_state(0)
            else:
                print("[CL] Error: no valid temperature")
                if kompresor.get_state() == 1:
                    kompresor.set_state(0)
                    mixer.set_state(0)
        await asyncio.sleep(1)
