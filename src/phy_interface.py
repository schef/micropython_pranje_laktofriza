import common_pins
import uasyncio as asyncio
import buttons
import oled_display
import washing_logic

async def on_button_state_change_callback(alias, data):
    if alias == common_pins.OLED_BUTTON_NEXT.name:
        if data == 1:
            await oled_display.handle_button_next()
    elif alias == common_pins.OLED_BUTTON_SELECT.name:
        if data == 1:
            await oled_display.handle_button_select()

def on_data_received(thing):
    if thing.path == "cooling":
        pass
    elif thing.path == "cleaning":
        if thing.data == "1":
            washing_logic.start()
            if on_state_change_cb is not None:
                on_state_change_cb(thing.path, "1")
        elif thing.data == "0":
            washing_logic.stop()
            if on_state_change_cb is not None:
                on_state_change_cb(thing.path, "0")
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
