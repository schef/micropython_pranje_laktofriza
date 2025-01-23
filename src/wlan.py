import network
import asyncio
import credentials

wlan = None
mac = None
rssi = 0
on_connection_changed_cb = None
reboot_requested = False

def init():
    global wlan, mac
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    mac = "".join(['{:02X}'.format(x) for x in wlan.config('mac')])

async def connect_wifi():
    global rssi
    if not wlan.isconnected():
        print(f"[WLAN]: scan[{wlan.scan()}]")
        print("[WLAN]: connecting")
        wlan.connect(credentials.wifi_ssid, credentials.wifi_password)
        while not wlan.isconnected():
            await asyncio.sleep(1)
    print(f"[WLAN]: connected[{wlan.ifconfig()}]")
    rssi = wlan.status("rssi")
    if on_connection_changed_cb is not None:
        on_connection_changed_cb()

def register_on_connection_changed_cb(func):
    global on_connection_changed_cb
    on_connection_changed_cb = func

def check_link():
    return wlan.isconnected()

def request_reboot():
    print("[WLAN]: request reboot")
    global reboot_requested
    reboot_requested = True

async def loop():
    global rssi
    while True:
        if not wlan.isconnected():
            print("[WLAN]: no connection")
            rssi = 0
            if on_connection_changed_cb is not None:
                on_connection_changed_cb()
            await connect_wifi()
        else:
            new_rssi = wlan.status("rssi")
            if rssi != new_rssi:
                rssi = new_rssi
                print(f"[WLAN]: rssi {rssi}")
                if on_connection_changed_cb is not None:
                    on_connection_changed_cb()
        await asyncio.sleep(10)