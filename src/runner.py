import asyncio
from machine import Pin, reset
import network
from pico_oled_1_3_spi import OLED_1inch3, oled_demo_short

wifi = None
oled = None
button_next = None
button_select = None
current_position = ""
current_selection = 0
current_mode = 0
modes_options = ["OFF", "ON", "AUTO"]

class MenuItem:
    def __init__(self, name = "", items = [], func = None):
        self.name = name
        self.items = items
        self.func = func

def init():
    global oled, button_next, button_select, wifi
    print("[R]: init")
    oled = OLED_1inch3()

    if oled.rotate == 0:
        BUTTON_NEXT_PIN = 15
        BUTTON_SELECT_PIN = 17
    else:
        BUTTON_NEXT_PIN = 17
        BUTTON_SELECT_PIN = 15
    button_next = Pin(BUTTON_NEXT_PIN, Pin.IN, Pin.PULL_UP)
    button_select = Pin(BUTTON_SELECT_PIN, Pin.IN, Pin.PULL_UP)

    wifi = network.WLAN(network.STA_IF)
    wifi.active(True)

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
        oled.fill_rect(42, 4, 15, 15, oled.white)
    else:
        oled.rect(42, 4, 15, 15, oled.white)

def display_home():
    oled.fill(0x0000)
    mode = modes_options[current_mode]
    if mode == "OFF":
        draw_heater([0, 0, 0])
    elif mode == "ON":
        draw_heater([1, 1, 1])
    elif mode == "AUTO":
        draw_heater([1, 0, 1])
    else:
        print("[R]: display_home not implemented")

    oled.text(f"cur temp:  23.1 C", 4, 24, 0xFFFF)
    oled.text(f"max temp: 100.0 C", 4, 24 + 8 + 4, 0xFFFF)
    oled.text(f"mode: {mode}", 4, 24 + (8 + 4) * 2, 0xFFFF)
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

async def wait_for_select():
    while True:
        if button_select.value() == 0:
            await asyncio.sleep(0.2)
            break
        await asyncio.sleep(0.01)

async def handle_input():
    print("[R]: handle_input")
    global current_position, current_selection, current_mode
    while True:
        if button_next.value() == 0:
            current_menu = get_menu_by_position()
            if current_menu is not None:
                current_selection = (current_selection + 1) % len(current_menu.items)
                handle_display()
            else:
                current_mode = (current_mode + 1) % len(modes_options)
                handle_display()
            await asyncio.sleep(0.2)

        if button_select.value() == 0:
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
            await asyncio.sleep(0.2)
        await asyncio.sleep(0.01)

async def display_wireless_status():
    oled.fill(0x0000)
    if wifi.isconnected():
        ssid = wifi.config('ssid')
        rssi = wifi.status('rssi')  # Get RSSI value if supported
        oled.text("Connected", 0, 0, 0xFFFF)
        oled.text(f"SSID: {ssid}", 0, 12, 0xFFFF)
        oled.text(f"RSSI: {rssi} dBm", 0, 24, 0xFFFF)
    else:
        oled.text("Not Connected", 0, 0, 0xFFFF)
    oled.show()
    await wait_for_select()

async def menu_call_jump_back():
    change_position()

async def menu_call_oled_demo():
    await oled_demo_short(oled)

async def menu_call_wifi_status():
    await display_wireless_status()

async def menu_call_reboot():
    oled.fill(0x0000)
    oled.text(f"REBOOT", int(128 / 2) - int(8 * 6 / 2), int(64 / 2) - int(8 / 2), 0xFFFF)
    oled.show()
    reset()

menu = MenuItem(items = [
    MenuItem(name = "main", items = [
        MenuItem(name = "demo", func = menu_call_oled_demo),
        MenuItem(name = "settings", items = [
            MenuItem(name = "reboot", func = menu_call_reboot),
            MenuItem(name = "wifi", func = menu_call_wifi_status),
            MenuItem(name = "back", func = menu_call_jump_back),
        ]),
        MenuItem(name = "back", func = menu_call_jump_back), # display home screen
    ])])

async def main():
    init()
    tasks = []
    tasks.append(asyncio.create_task(handle_input()))
    for task in tasks:
        await task
    print("[R]: error loop task finished!")

def run():
    asyncio.run(main())
