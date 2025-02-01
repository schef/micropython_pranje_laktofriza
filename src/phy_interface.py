import asyncio
import common_pins
import oled_display
import washing_logic
import cooling_logic

class Mode:
    WASHING = "washing"
    COOLING = "cooling"
    MIXING = "mixing"

advertise_state_callback = None

def register_advertise_state_callback(callback):
    global advertise_state_callback
    advertise_state_callback = callback

def advertise_state(mode, state):
    if advertise_state_callback is not None:
        advertise_state_callback(mode, str(state))

def set_washing(state):
    if state == 1:
        if cooling_logic.in_progress():
            print("ERROR: mode mixing, request washing while cooling")
        else:
            if washing_logic.in_progress():
                print("ERROR: washing already in progress")
            else:
                washing_logic.start()
                oled_display.set_current_mode("SPAL")
                advertise_state(Mode.WASHING.upper(), 1)
    else:
        if washing_logic.in_progress():
            washing_logic.stop()
            oled_display.set_current_mode("")
            advertise_state(Mode.WASHING.upper(), 0)

def set_cooling(state, delay = False):
    if state == 1:
        if washing_logic.in_progress():
            print("ERROR: mode mixing, request cooling while washing")
        else:
            if cooling_logic.in_progress():
                print("ERROR: cooling already in progress")
            else:
                if delay:
                        cooling_logic.set_delay()
                cooling_logic.start()
                oled_display.set_current_mode("FRIG")
                advertise_state(Mode.COOLING.upper(), 1)
    else:
        if cooling_logic.in_progress():
            cooling_logic.stop()
            oled_display.set_current_mode("")
            advertise_state(Mode.COOLING.upper(), 0)

def set_mixing(state):
    if state == 1:
        cooling_logic.set_mixing()
        advertise_state(Mode.MIXING.upper(), 1)

def handle_buttons(thing):
    if thing.alias == common_pins.BUTTON_WASHING.name:
        if not washing_logic.in_progress():
            if cooling_logic.in_progress():
                set_cooling(0)
            set_washing(1)
        else:
            set_washing(0)
    elif thing.alias == common_pins.BUTTON_COOLING.name:
        if not cooling_logic.in_progress():
            if washing_logic.in_progress():
                set_washing(0)
            set_cooling(1, delay = True)
        else:
            set_cooling(0)
    elif thing.alias == common_pins.BUTTON_MIXING.name:
        if cooling_logic.in_progress():
            set_mixing(1)

def handle_request(thing):
    if thing.data == "request":
        state = None
        if thing.alias == Mode.WASHING:
            state = washing_logic.in_progress()
        if thing.alias == Mode.COOLING:
            state = cooling_logic.in_progress()
        if thing.alias == Mode.MIXING:
            state = cooling_logic.is_mixing()
        if state is not None:
            thing.data = state
            thing.dirty_out = True

def on_data_received(thing):
    handle_request(thing)

    if thing.path == Mode.COOLING:
        if thing.data == "1":
            set_cooling(1)
        elif thing.data == "0":
            set_cooling(0)

    elif thing.path == Mode.WASHING:
        if thing.data == "1":
            set_washing(1)
        elif thing.data == "0":
            set_washing(0)

    elif thing.path == Mode.MIXING:
        if thing.data == "1":
            set_mixing(1)

def force_advertise_states():
    if advertise_state_callback is not None:
        advertise_state(Mode.WASHING.upper(), int(washing_logic.in_progress()))
        advertise_state(Mode.COOLING.upper(), int(cooling_logic.in_progress()))

def init():
    print("[PHY]: init")

async def action():
    while True:
        await asyncio.sleep(0.1)
