import asyncio
import buttons
import sensors
import mqtt
import version
import leds
import phy_interface
import wlan
import oled_display

class Thing:
    def __init__(self, path=None, alias=None, ignore_duplicates_out=False, ignore_duplicates_in=False, cb_out=None, cb_in=None):
        self.path = path
        self.alias = alias
        self.ignore_duplicates_out = ignore_duplicates_out
        self.ignore_duplicates_in = ignore_duplicates_in
        self.data = None
        self.dirty_out = False
        self.dirty_in = False
        self.cb_out = cb_out
        self.cb_in = cb_in

things = [
    # sensors
    Thing("s/maxtemp", alias="MAX_TEMP", cb_in=sensors.on_data_request),
    Thing("s/maxtemp_error", alias="MAX_TEMP_ERROR"),

    # phy outputs
    Thing("test/led", alias="ONBOARD_LED", cb_in=leds.on_relay_direct),
    Thing("r/ventil_hladna", alias="VENTIL_HLADNA", cb_in=leds.on_relay_direct),
    Thing("r/ventil_topla", alias="VENTIL_TOPLA", cb_in=leds.on_relay_direct),
    Thing("r/motor", alias="MOTOR", cb_in=leds.on_relay_direct),
    Thing("r/ventil_ispust", alias="VENTIL_ISPUST", cb_in=leds.on_relay_direct),
    Thing("r/doziranje_luzina", alias="DOZIRANJE_LUZINA", cb_in=leds.on_relay_direct),
    Thing("r/doziranje_kiselina", alias="DOZIRANJE_KISELINA", cb_in=leds.on_relay_direct),
    Thing("r/kompresor", alias="KOMPRESOR", cb_in=leds.on_relay_direct),
    Thing("r/mixer", alias="MIXER", cb_in=leds.on_relay_direct),

    # logic
    Thing("version", cb_in=version.req_version),
    Thing("washing", cb_in=phy_interface.on_data_received),
    Thing("cooling", cb_in=phy_interface.on_data_received),
    Thing("mixing", cb_in=phy_interface.on_data_received),
    Thing("b/washing", alias="BUTTON_WASHING"),
    Thing("b/cooling", alias="BUTTON_COOLING"),
    Thing("b/mixing", alias="BUTTON_MIXING"),
    Thing("heartbeat"),
]

def get_thing_from_path(path):
    for thing in things:
        if path == thing.path:
            return thing
    return None

def get_thing_from_alias(alias):
    for thing in things:
        if alias == thing.alias:
            return thing
    return None

def send_msg_req(t, data):
    if t.ignore_duplicates_out:
        if data != t.data:
            t.dirty_out = True
    else:
        t.dirty_out = True
    t.data = data

def on_sensor_state_change_callback(alias, data):
    oled_display.refresh_screen()
    t = get_thing_from_alias(alias)
    if t is not None:
        send_msg_req(t, data)
        return

    t = get_thing_from_path(alias)
    if t is not None:
        send_msg_req(t, data)
        return

def on_mqtt_message_received_callback(path, msg):
    t = get_thing_from_path(path)
    if t is not None:
        if t.ignore_duplicates_in:
            if msg != t.data:
                t.dirty_in = True
        else:
            t.dirty_in = True
        t.data = msg

def on_button_state_change_callback(alias, data):
    if data == 1:
        t = get_thing_from_alias(alias)
        if t is not None:
            send_msg_req(t, data)
            phy_interface.handle_buttons(t)

def on_phy_interface_advertise_state_callback(alias, state):
    t = get_thing_from_alias(alias)
    if t is not None:
        send_msg_req(t, state)

def on_leds_advertise_state_callback(alias, state):
    t = get_thing_from_alias(alias)
    if t is not None:
        send_msg_req(t, state)

def on_wlan_connection_changed_callback():
    oled_display.refresh_screen()

def init():
    print("[THINGS]: init")
    sensors.register_on_state_change_callback(on_sensor_state_change_callback)
    mqtt.register_on_message_received_callback(on_mqtt_message_received_callback)
    buttons.register_on_state_change_callback(on_button_state_change_callback)
    phy_interface.register_advertise_state_callback(on_phy_interface_advertise_state_callback)
    leds.register_advertise_state_callback(on_leds_advertise_state_callback)
    wlan.register_on_connection_changed_callback(on_wlan_connection_changed_callback)

async def handle_msg_reqs():
    for t in things:
        if t.dirty_out:
            t.dirty_out = False
            if t.cb_out is not None:
                t.cb_out(t)
            await mqtt.send_message(t.path, str(t.data))
        if t.dirty_in:
            t.dirty_in = False
            if t.cb_in is not None:
                t.cb_in(t)

async def loop_async():
    print("[SYNC]: loop async")
    while True:
        await handle_msg_reqs()
        await asyncio.sleep(0)
