import asyncio
import common_pins
import leds
import sensors

in_progress_status = False
start_timestamp = 0
current_state = ""
timeout = 0
on_state_change_cb = None

pin_relays = [
    common_pins.KOMPRESOR,
    common_pins.MOTOR,
]

def init():
    print("[CL]: init")
    stop()

def register_on_state_change_cb(func):
    global on_state_change_cb
    on_state_change_cb = func

def start():
    print("[CL]: start")
    global in_progress_status
    in_progress_status = True
    set_currert_state("ON")

def stop():
    print("[CL]: stop")
    global in_progress_status
    in_progress_status = False
    for pin in pin_relays:
        led = leds.get_led_by_name(pin)
        if led is not None:
            if led.get_state() != 0:
                led.set_state(0)
    set_currert_state("OFF")

def in_progress():
    return in_progress_status

def set_currert_state(state):
    global current_state
    current_state = state
    if on_state_change_cb is not None:
        on_state_change_cb(state)

async def loop():
    print("[CL]: loop")
    while True:
        if in_progress_status:
            temperature = sensors.environment_sensors[0].get_temperature()
            if temperature is not None:
                if temperature > 5.0 and temperature < 50.0:
                    kompresor = leds.get_led_by_name(common_pins.KOMPRESOR.name)
                    mixer = leds.get_led_by_name(common_pins.MIXER.name)
                    if kompresor is not None:
                        if kompresor.get_state() == 0:
                            kompresor.set_state(1)
                            if mixer is not None:
                                mixer.set_state(1)
                            set_currert_state("COMPRESSOR ON")
                elif temperature < 3.5 or temperature >= 50.0:
                    kompresor = leds.get_led_by_name(common_pins.KOMPRESOR.name)
                    mixer = leds.get_led_by_name(common_pins.MIXER.name)
                    if kompresor is not None:
                        if kompresor.get_state() == 1:
                            kompresor.set_state(0)
                            if mixer is not None:
                                mixer.set_state(0)
                            set_currert_state("COMPRESSOR OFF")
        await asyncio.sleep(1)
