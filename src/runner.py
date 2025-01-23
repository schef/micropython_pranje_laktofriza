import asyncio
import common
import buttons
import leds
import phy_interface
import sensors
import washing_logic
import wlan
import mqtt
import cli
import heartbeat
import things
import oled_display
import lan_reboot
import version

async def process_time_measure(timeout=20):
    print("[RUNNER]: start process_time_measure")
    timestamp = common.get_millis()
    bigest = 0
    while True:
        await asyncio.sleep(0)
        timepassed = common.millis_passed(timestamp)
        if timepassed >= timeout:
            if timepassed > bigest:
                bigest = timepassed
            print("[RUNNER]: timeout warning %d ms with bigest %d" % (timepassed, bigest))
        timestamp = common.get_millis()

def send_on_boot():
    print("[RUNNER]: send_on_boot")
    t = things.get_thing_from_path("version")
    t.data = version.VERSION
    t.dirty_out = True

def init():
    global spi_max, max_sensor
    print("[RUNNER]: init")

    buttons.init()
    buttons.action()
    leds.init()
    phy_interface.init()
    sensors.init()
    washing_logic.init()
    wlan.init()
    mqtt.init()
    cli.init()
    things.init()
    oled_display.init()
    send_on_boot()

async def main():
    init()
    tasks = []
    tasks.append(asyncio.create_task(common.loop_async("BUTTONS", buttons.action)))
    tasks.append(asyncio.create_task(common.loop_async("LEDS", leds.action)))
    tasks.append(asyncio.create_task(phy_interface.action()))
    tasks.append(asyncio.create_task(sensors.realtime_sensors_action()))
    tasks.append(asyncio.create_task(sensors.environment_sensors_action()))
    tasks.append(asyncio.create_task(washing_logic.loop()))
    tasks.append(asyncio.create_task(wlan.loop()))
    tasks.append(asyncio.create_task(mqtt.loop_async()))
    tasks.append(asyncio.create_task(common.loop_async("CLI", cli.action)))
    tasks.append(asyncio.create_task(heartbeat.action()))
    tasks.append(asyncio.create_task(things.loop_async()))
    tasks.append(asyncio.create_task(lan_reboot.action()))
    tasks.append(asyncio.create_task(process_time_measure()))
    for task in tasks:
        await task
    print("[RUNNER]: Error: loop task finished!")

def run():
    asyncio.run(main())
