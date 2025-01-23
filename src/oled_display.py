
import asyncio
from machine import Pin, reset, SPI
from pico_oled_1_3_spi import OLED_1inch3, oled_demo_short
import common_pins
import wlan
import sensors

oled = None
spi_oled = None
current_position = ""
current_selection = 0
modes_options = ["OFF", "ON", "AUTO"]

##### CALLBACKS #####
callbacks = {}
current_mode = ""

class MenuItem:
    def __init__(self, name = "", items = [], func = None):
        self.name = name
        self.items = items
        self.func = func

def init():
    global oled, spi_oled
    print("[OLED]: init")
    spi_oled = SPI(1, 20_000_000, polarity = 0, phase = 0, sck = Pin(common_pins.OLED_SPI_SCK.id), mosi = Pin(common_pins.OLED_SPI_MOSI.id), miso = None)
    oled = OLED_1inch3(spi = spi_oled, dc = Pin(common_pins.OLED_SPI_DC.id, Pin.OUT), cs = Pin(common_pins.OLED_SPI_CS.id, Pin.OUT), rst = Pin(common_pins.OLED_RST.id, Pin.OUT))
    wlan.register_on_connection_changed_cb(on_connection_state_change_cb)
    handle_display()

def draw_heater(status):
    if status[0]:
        oled.fill_rect(4, 4, 15, 15, oled.white)
    else:
        oled.rect(4, 4, 15, 15, oled.white)
    if status[1]:
        oled.fill_rect(24, 4, 15, 15, oled.white)
    else:
        oled.rect(24, 4, 15, 15, oled.white)
    if status[2]:
        oled.fill_rect(44, 4, 15, 15, oled.white)
    else:
        oled.rect(44, 4, 15, 15, oled.white)

def display_home():
    oled.fill(0x0000)
    wifi_status = ["no conn", wlan.credentials.wifi_ssid][wlan.wlan.isconnected()]
    oled.text(f"MODE: {current_mode}", 4, 0, 0xFFFF)
    temperature = sensors.environment_sensors[0].get_temperature()
    if temperature:
        oled.text("TEMP: {:.2f} C".format(temperature), 4, 28, 0xFFFF)
    else:
        oled.text("TEMP: None", 4, 28, 0xFFFF)
    oled.text(f"WIFI: {wifi_status}", 4, 42, 0xFFFF)
    if wlan.wlan.isconnected():
        oled.text(f" RSSI: {wlan.rssi}", 4, 56, 0xFFFF)
    oled.show()

def get_parts():
    return list(filter(None, current_position.split("/")))

def change_position(position = None):
    global current_position
    old_position = current_position
    if position is None:
        current_position = "/".join(get_parts()[:-1])
    else:
        current_position = "/".join(get_parts() + [position])
    print(f"[R]: change_position[{old_position} -> {current_position}]")

def jump_back():
    change_position()

def jump_to(position):
    change_position(position)

def get_menu_by_position():
    print(f"[R]: get_menu_by_position[{repr(current_position)}]")
    current_menu = menu
    parts = get_parts()
    print(f"[parts] = {parts}")
    if not parts:
        return None
    for part in parts:
        for item in current_menu.items:
            if part == item.name:
                current_menu = item
    return current_menu

def handle_display():
    print(f"[R]: handle_display[{repr(current_position)} : {current_selection}]")
    current_menu = get_menu_by_position()
    if current_menu is None:
        display_home()
    else:
        # MENU
        oled.fill(0x0000)
        oled.text(f"{current_menu.name}", 0, 0, 0xFFFF)  # Highlight selected item
        for i, item in enumerate(current_menu.items):
            if i == current_selection:
                oled.text(f"> {item.name}", 0, (1 + i) * 12, 0xFFFF)  # Highlight selected item
            else:
                oled.text(f"  {item.name}", 0, (1 + i) * 12, 0xFFFF)
        oled.show()

async def handle_button_next():
    global current_selection
    current_menu = get_menu_by_position()
    if current_menu is not None:
        current_selection = (current_selection + 1) % len(current_menu.items)
        handle_display()
    else:
        if washing_logic_in_progress_cb is not None:
            if washing_logic_in_progress_cb() == False:
                if washing_logic_start_cb is not None:
                    washing_logic_start_cb()
            else:
                if washing_logic_stop_cb is not None:
                    washing_logic_stop_cb()
            handle_display()

async def handle_button_select():
    current_menu = get_menu_by_position()
    if current_menu is None:
        jump_to("main")
        handle_display()
    else:
        if current_menu.items[current_selection].func != None:
            await current_menu.items[current_selection].func()
            current_selection = 0
            handle_display()
        else:
            jump_to(current_menu.items[current_selection].name)
            current_selection = 0
            handle_display()

##### MENU #####

async def menu_call_oled_demo():
    await oled_demo_short(oled)

async def menu_call_reboot():
    oled.fill(0x0000)
    oled.text(f"REBOOT", int(128 / 2) - int(8 * 6 / 2), int(64 / 2) - int(8 / 2), 0xFFFF)
    oled.show()
    reset()

async def menu_call_jump_back():
    change_position()

menu = MenuItem(items = [
    MenuItem(name = "main", items = [
        MenuItem(name = "demo", func = menu_call_oled_demo),
        MenuItem(name = "settings", items = [
            MenuItem(name = "reboot", func = menu_call_reboot),
            MenuItem(name = "wifi"),
            MenuItem(name = "back", func = menu_call_jump_back),
        ]),
        MenuItem(name = "back", func = menu_call_jump_back), # display home screen
    ])])

def set_current_mode(mode):
    global current_mode
    current_mode = mode
    refresh_screen()

##### CALLBACKS #####

def on_connection_state_change_cb():
    refresh_screen()

def refresh_screen():
    if current_position == "":
        display_home()
