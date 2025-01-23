import uasyncio as asyncio
import time
import common
import common_pins

relays = []
leds = []

relay_pins = [
    common_pins.VENTIL_HLADNA,
    common_pins.VENTIL_TOPLA,
    common_pins.MOTOR,
    common_pins.VENTIL_ISPUST,
    common_pins.DOZIRANJE_LUZINA,
    common_pins.DOZIRANJE_KISELINA,
    common_pins.KOMPRESOR,
    common_pins.MJESANJE,
]

led_pins = [
    common_pins.ONBOARD_LED,
]

class Led:
    def __init__(self, id, name, active_high=False):
        self.output = common.create_output(id)
        self.active_high = active_high
        self.state = None
        self.set_state(0)
        self.name = name

    def set_state(self, state):
        if self.active_high:
            if state:
                self.output.off()
            else:
                self.output.on()
        else:
            if state:
                self.output.on()
            else:
                self.output.off()
        self.state = state

def set_state_by_name(name, state):
    print("[LEDS]: set_state_by_name(%s, %s)" % (name, state))
    for relay in relays:
        if relay.name == name:
            relay.set_state(state)
    for led in leds:
        if led.name == name:
            led.set_state(state)

def get_state_by_name(name):
    for relay in relays:
        if relay.name == name:
            return relay.state
    for led in leds:
        if led.name == name:
            return led.state
    return None

def on_relay_direct(thing):
    state = int(thing.data) if thing.data in ("0", "1", 0, 1) else None
    if state is not None:
        set_state_by_name(thing.alias, state)
    if thing.data == "request":
        state = get_state_by_name(thing.alias)
        print(thing.alias, thing.data)
        if state is not None:
            thing.data = state
            thing.dirty_out = True

def test_relays():
    global relays
    relays = []
    init_relays()
    for relay in relays:
        print("[LEDS]: testing %s" % (relay.name))
        relay.set_state(1)
        time.sleep_ms(1000)
        relay.set_state(0)
        time.sleep_ms(1000)

def test_leds():
    global leds
    leds = []
    init_leds()
    for led in leds:
        print("[LEDS]: testing %s" % (led.name))
        led.set_state(1)
        time.sleep_ms(1000)
        led.set_state(0)
        time.sleep_ms(1000)

def init_relays():
    for pin in relay_pins:
        relays.append(Led(pin.id, pin.name, active_high = True))

def init_leds():
    for pin in led_pins:
        if "ONBOARD" in pin.name:
            leds.append(Led(pin.id, pin.name))
        else:
            leds.append(Led(pin.id, pin.name, active_high = True))

def init():
    print("[LEDS]: init")
    init_relays()
    init_leds()
    action()

def action():
    pass

def test():
    print("[LEDS]: test")
    init()
    while True:
        action()

def test_async():
    print("[LEDS]: test_async")
    init()
    asyncio.run(common.loop_async("LEDS", action))
