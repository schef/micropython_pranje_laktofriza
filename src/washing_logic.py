from machine import Pin, reset
from time import ticks_ms, sleep_ms

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
button_drive = None
button_led = None
button_input = None
button_state = None
washing_start = False
start_timestamp = 0


def get_millis():
    return ticks_ms()


def millis_passed(timestamp):
    return get_millis() - timestamp


def get_seconds():
    return int(get_millis() / 1000)


def seconds_passed(timestamp):
    return get_seconds() - timestamp


def init():
    print("init")
    global button_led, relays, button_drive, button_input
    button_led = Pin(BUTTON_LED_PIN, Pin.OUT)
    button_led.off()
    for pin in RELAY_PINS:
        relays.append(Pin(pin, Pin.OUT))
        relays[-1].on()
    button_drive = Pin(BUTTON_INPUT_DRIVE_PIN, Pin.OUT)
    button_drive.off()
    button_input = Pin(BUTTON_INPUT_PIN, Pin.IN, Pin.PULL_UP)


def get_relay_state(num):
    if num <= 0 or num > len(RELAY_PINS):
        return None
    return int(not relays[num - 1].value())


def set_relay_state(num, state):
    if num <= 0 or num > len(RELAY_PINS):
        return
    print("set_relay_state %d %s" % (num, str(state)))
    relays[num - 1].value(int(not state))


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


def check_reset():
    if check_action(2050, 60):
        reset()

def washing_loop():
    check_ventil_hladna()
    check_ventil_topla()
    check_motor()
    check_ventil_ispust()
    check_doziranje_luzina()
    check_doziranje_kiselina()
    check_reset()


def on_button_callback(state):
    print("button %s" % (("released", "pressed")[state]))
    global washing_start, start_timestamp
    if state and not washing_start:
        washing_start = True
        start_timestamp = get_seconds()
        button_led.on()


def check_button():
    global button_state
    state = button_input.value()
    if state != button_state:
        button_state = state
        on_button_callback(not button_state)


def loop():
    print("loop")
    while True:
        check_button()
        if washing_start:
            washing_loop()


def run():
    init()
    loop()
