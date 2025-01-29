import asyncio
from common import get_seconds, seconds_passed
import common_pins
import leds

in_progress_status = False
start_timestamp = 0
current_state = ""
timeout = 0

pin_relays = [
    common_pins.VENTIL_HLADNA,
    common_pins.VENTIL_TOPLA,
    common_pins.MOTOR,
    common_pins.VENTIL_ISPUST,
    common_pins.DOZIRANJE_LUZINA,
    common_pins.DOZIRANJE_KISELINA
]

def init():
    print("[WL]: init")
    stop()

def get_relay_state(pin):
    return leds.get_state_by_name(pin.name)

def set_relay_state(pin, state):
    global current_state
    leds.set_state_by_name(pin.name, state)

def check_action(start, timeout):
    if seconds_passed(start_timestamp) >= start:
        if seconds_passed(start_timestamp) < (start + timeout):
            return True
    return False

def check_ventil_hladna():
    state = None
    if check_action(0, 60):
        state = 1
    else:
        state = 0
    if get_relay_state(common_pins.VENTIL_HLADNA) != state:
        set_relay_state(common_pins.VENTIL_HLADNA, state)

def check_ventil_topla():
    state = None
    if check_action(60, 120):
        state = 1
    elif check_action(380, 100):
        state = 1
    elif check_action(1090, 100):
        state = 1
    elif check_action(1330, 100):
        state = 1
    elif check_action(1750, 120):
        state = 1
    else:
        state = 0
    if get_relay_state(common_pins.VENTIL_TOPLA) != state:
        set_relay_state(common_pins.VENTIL_TOPLA, state)

def check_motor():
    state = None
    if check_action(60, 200):
        state = 1
    elif check_action(440, 560):
        state = 1
    elif check_action(1150, 100):
        state = 1
    elif check_action(1390, 280):
        state = 1
    elif check_action(1810, 120):
        state = 1
    else:
        state = 0
    if get_relay_state(common_pins.MOTOR) != state:
        set_relay_state(common_pins.MOTOR, state)

def check_ventil_ispust():
    state = None
    if check_action(180, 200):
        state = 1
    elif check_action(940, 150):
        state = 1
    elif check_action(1210, 120):
        state = 1
    elif check_action(1630, 120):
        state = 1
    elif check_action(1870, 180):
        state = 1
    else:
        state = 0
    if get_relay_state(common_pins.VENTIL_ISPUST) != state:
        set_relay_state(common_pins.VENTIL_ISPUST, state)

def check_doziranje_luzina():
    state = None
    if check_action(440, 60):
        state = 1
    else:
        state = 0
    if get_relay_state(common_pins.DOZIRANJE_LUZINA) != state:
        set_relay_state(common_pins.DOZIRANJE_LUZINA, state)

def check_doziranje_kiselina():
    state = None
    if check_action(1390, 60):
        state = 1
    else:
        state = 0
    if get_relay_state(common_pins.DOZIRANJE_KISELINA) != state:
        set_relay_state(common_pins.DOZIRANJE_KISELINA, state)

def check_stop():
    if check_action(2050, 60):
        stop()

async def washing_loop():
    check_ventil_hladna()
    check_ventil_topla()
    check_motor()
    check_ventil_ispust()
    check_doziranje_luzina()
    check_doziranje_kiselina()
    check_stop()
    await asyncio.sleep(1)

def start():
    print("[WL]: start")
    global in_progress_status, start_timestamp, current_state
    in_progress_status = True
    start_timestamp = get_seconds()

def stop():
    print("[WL]: stop")
    global in_progress_status, start_timestamp, current_state
    in_progress_status = False
    start_timestamp = 0
    for pin in pin_relays:
        if get_relay_state(pin) != 0:
            set_relay_state(pin, 0)

def in_progress():
    return in_progress_status

async def loop():
    print("[WL]: loop")
    while True:
        if in_progress_status and start_timestamp > 0:
            await washing_loop()
        await asyncio.sleep(1)
