import asyncio
from machine import Pin
from time import ticks_ms

RELAY_PINS = [18, 19, 20, 21, 22, 26, 27, 28]
BUTTON_LED_PIN = 2
BUTTON_INPUT_DRIVE_PIN = 4
BUTTON_INPUT_PIN = 5

VENTIL_HLADNA = 1
VENTIL_TOPLA = 2
MOTOR = 3
VENTIL_ISPUST = 4
DOZIRANJE_LUZINA = 6
DOZIRANJE_KISELINA = 7

relays = []
washing_start = False
start_timestamp = 0
current_state = ""
timeout = 0
on_washing_calback = None

def get_millis():
    return ticks_ms()

def millis_passed(timestamp):
    return get_millis() - timestamp

def get_seconds():
    return int(get_millis() / 1000)

def seconds_passed(timestamp):
    return get_seconds() - timestamp

def init():
    print("[WL]: init")
    global relays
    for pin in RELAY_PINS:
        relays.append(Pin(pin, Pin.OUT))
        relays[-1].on()

def register_on_washing_callback(func):
    global on_washing_calback
    on_washing_calback = func

def get_relay_state(num):
    if num <= 0 or num > len(RELAY_PINS):
        return None
    return int(not relays[num - 1].value())

def set_relay_state(num, state):
    global current_state
    if num <= 0 or num > len(RELAY_PINS):
        return
    print("[WL]: set_relay_state %d %s" % (num, str(state)))
    relays[num - 1].value(int(not state))
    if num == 1:
        current_state = f"VNT_HLADNA {int(state)}"
    elif num == 2:
        current_state = f"VNT_TOPLA {int(state)}"
    elif num == 3:
        current_state = f"MOTOR {int(state)}"
    elif num == 4:
        current_state = f"VNT_ISPUST {int(state)}"
    elif num == 6:
        current_state = f"DOZ_LUZ {int(state)}"
    elif num == 7:
        current_state = f"DOZ_KISL {int(state)}"
    if on_washing_calback is not None:
        on_washing_calback()

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
    if get_relay_state(VENTIL_HLADNA) != state:
        set_relay_state(VENTIL_HLADNA, state)

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
    if get_relay_state(VENTIL_TOPLA) != state:
        set_relay_state(VENTIL_TOPLA, state)

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
    if get_relay_state(MOTOR) != state:
        set_relay_state(MOTOR, state)

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
    if get_relay_state(VENTIL_ISPUST) != state:
        set_relay_state(VENTIL_ISPUST, state)

def check_doziranje_luzina():
    state = None
    if check_action(440, 60):
        state = 1
    else:
        state = 0
    if get_relay_state(DOZIRANJE_LUZINA) != state:
        set_relay_state(DOZIRANJE_LUZINA, state)

def check_doziranje_kiselina():
    state = None
    if check_action(1390, 60):
        state = 1
    else:
        state = 0
    if get_relay_state(DOZIRANJE_KISELINA) != state:
        set_relay_state(DOZIRANJE_KISELINA, state)

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
    global washing_start, start_timestamp, current_state
    washing_start = True
    start_timestamp = get_seconds()

def stop():
    print("[WL]: stop")
    global washing_start, start_timestamp, current_state
    washing_start = False
    start_timestamp = 0
    for i in range(len(relays)):
        if get_relay_state(i) != 0:
            set_relay_state(i, 0)
    current_state = ""

def in_progress():
    return washing_start

async def loop():
    print("[WL]: loop")
    while True:
        if washing_start and start_timestamp > 0:
            await washing_loop()
        await asyncio.sleep(1)
