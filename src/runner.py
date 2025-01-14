import asyncio
from machine import Pin, reset, SPI
import network
from pico_oled_1_3_spi import OLED_1inch3, oled_demo_short
from max31865 import MAX31865
import washing_logic
import wifi_handler

PIN_OLED_SPI_MOSI = 11
PIN_OLED_SPI_SCK = 10
PIN_OLED_RST = 12
PIN_OLED_SPI_DC = 8
PIN_OLED_SPI_CS = 9

PIN_MAX_SPI_CS = 5
PIN_MAX_SPI_MOSI = 3
PIN_MAX_SPI_MISO = 4
PIN_MAX_SPI_SCK = 2

wifi = None
oled = None
spi_oled = None
spi_max = None
max_sensor = None
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
    global oled, wifi, spi_oled, spi_max, max_sensor, button_next, button_select
    print("[R]: init")
    spi_oled = SPI(1, 20_000_000, polarity = 0, phase = 0, sck = Pin(PIN_OLED_SPI_SCK), mosi = Pin(PIN_OLED_SPI_MOSI), miso = None)
    oled = OLED_1inch3(spi = spi_oled, dc = Pin(PIN_OLED_SPI_DC, Pin.OUT), cs = Pin(PIN_OLED_SPI_CS, Pin.OUT), rst = Pin(PIN_OLED_RST, Pin.OUT))
    spi_max = SPI(0, baudrate=5_000_000, phase = 1, sck = Pin(PIN_MAX_SPI_SCK), mosi = Pin(PIN_MAX_SPI_MOSI), miso = Pin(PIN_MAX_SPI_MISO))
    max_sensor = MAX31865(spi = spi_max, cs = Pin(PIN_MAX_SPI_CS, Pin.OUT))

    if oled.rotate == 0:
        BUTTON_NEXT_PIN = 15
        BUTTON_SELECT_PIN = 17
    else:
        BUTTON_NEXT_PIN = 17
        BUTTON_SELECT_PIN = 15

    button_next = Pin(BUTTON_NEXT_PIN, Pin.IN, Pin.PULL_UP)
    button_select = Pin(BUTTON_SELECT_PIN, Pin.IN, Pin.PULL_UP)
    washing_logic.register_on_washing_callback(on_washing_callback)
    washing_logic.init()
    wifi_handler.register_on_connection_changed_callback(on_connection_changed_callback)
    wifi_handler.init()
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
    washing_status = ["OFF", "ON"][washing_logic.in_progress()]
    wifi_status = ["no conn", wifi_handler.SSID][wifi_handler.wlan.isconnected()]
    oled.text(f"PRANJE: {washing_status}", 4, 0, 0xFFFF)
    oled.text(f" {washing_logic.current_state}", 4, 14, 0xFFFF)
    oled.text("TEMP: {:.2f} C".format(max_sensor.temperature), 4, 28, 0xFFFF)
    oled.text(f"WIFI: {wifi_status}", 4, 42, 0xFFFF)
    if wifi_handler.wlan.isconnected():
        oled.text(f" RSSI: {wifi_handler.rssi}", 4, 56, 0xFFFF)
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
                if not washing_logic.in_progress():
                    washing_logic.start()
                else:
                    washing_logic.stop()
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

def on_washing_callback():
    if current_position == "":
        display_home()

def on_connection_changed_callback():
    if current_position == "":
        display_home()

async def main():
    init()
    tasks = []
    tasks.append(asyncio.create_task(handle_input()))
    tasks.append(asyncio.create_task(washing_logic.loop()))
    tasks.append(asyncio.create_task(wifi_handler.loop()))
    for task in tasks:
        await task
    print("[R]: error loop task finished!")

def run():
    asyncio.run(main())
