import common_pins
import uasyncio as asyncio
import buttons
import oled_display
import washing_logic
import cooling_logic

async def on_button_state_change_callback(alias, data):
    if alias == common_pins.OLED_BUTTON_NEXT.name:
        if data == 1:
            await oled_display.handle_button_next()
    elif alias == common_pins.OLED_BUTTON_SELECT.name:
        if data == 1:
            await oled_display.handle_button_select()

def on_data_received(thing):
    if thing.path == "cooling":
        if thing.data == "1" and not washing_logic.in_progress():
            cooling_logic.start()
            if on_state_change_cb is not None:
                on_state_change_cb(thing.path, "1")
            oled_display.set_current_mode("cooling")
        elif thing.data == "0":
            cooling_logic.stop()
            if on_state_change_cb is not None:
                on_state_change_cb(thing.path, "0")
            oled_display.set_current_mode("")
        elif thing.data == "":
            if on_state_change_cb is not None:
                on_state_change_cb(thing.path, str(int(cooling_logic.in_progress())))
    elif thing.path == "washing":
        if thing.data == "1" and not cooling_logic.in_progress():
            washing_logic.start()
            if on_state_change_cb is not None:
                on_state_change_cb(thing.path, "1")
            oled_display.set_current_mode("washing")
        elif thing.data == "0":
            washing_logic.stop()
            if on_state_change_cb is not None:
                on_state_change_cb(thing.path, "0")
            oled_display.set_current_mode("")
        elif thing.data == "":
            if on_state_change_cb is not None:
                on_state_change_cb(thing.path, str(int(washing_logic.in_progress())))

def register_on_state_change_callback(cb):
    global on_state_change_cb
    print("[PHY]: register on state change cb")
    on_state_change_cb = cb

def init():
    print("[PHY]: init")
    buttons.register_on_state_change_callback(on_button_state_change_callback)

async def action():
    while True:
        await asyncio.sleep(0.1)
