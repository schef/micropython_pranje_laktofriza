import network
import asyncio

SSID = "esschef2"
PASSWORD = "babyaria123"

wlan = None
rssi = 0
on_connection_changed_callback = None

def init():
    global wlan
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

async def connect_wifi():
    global rssi
    if not wlan.isconnected():
        print(f"[W]: scan[{wlan.scan()}]")
        print("[W]: connecting")
        wlan.connect(SSID, PASSWORD)
        while not wlan.isconnected():
            await asyncio.sleep(1)
    print(f"[W]: connected[{wlan.ifconfig()}]")
    rssi = wlan.status("rssi")
    if on_connection_changed_callback is not None:
        on_connection_changed_callback()

def register_on_connection_changed_callback(func):
    global on_connection_changed_callback
    on_connection_changed_callback = func

async def loop():
    global rssi
    while True:
        if not wlan.isconnected():
            print("[W]: no connection")
            rssi = 0
            if on_connection_changed_callback is not None:
                on_connection_changed_callback()
            await connect_wifi()
        else:
            new_rssi = wlan.status("rssi")
            if rssi != new_rssi:
                rssi = new_rssi
                print(f"[W]: rssi {rssi}")
                if on_connection_changed_callback is not None:
                    on_connection_changed_callback()
        await asyncio.sleep(10)
