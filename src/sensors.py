import uasyncio as asyncio
from machine import SPI, Pin
import common
import common_pins
import struct
import driver_max31865

environment_sensors = []
realtime_sensors = []
on_state_change_cb = None

class TempReader:
    def __init__(self, alias):
        self.alias = alias
        self.spi_max = SPI(0,
                           baudrate=5_000_000,
                           phase = 1,
                           sck = Pin(common_pins.MAX_SPI_SCK.id),
                           mosi = Pin(common_pins.MAX_SPI_MOSI.id),
                           miso = Pin(common_pins.MAX_SPI_MISO.id))
        self.max_sensor = driver_max31865.MAX31865(spi = self.spi_max,
                                   cs = Pin(common_pins.MAX_SPI_CS.id,
                                            Pin.OUT))
        self.dirty = False
        self.data = None
        self.last_data = None
        self.error_msg = None
        self.timestamp = None
        self.timeout = 60 * 1000

    async def action(self):
        try:
            self.data = self.max_sensor.temperature()
            self.last_data = self.data
            self.dirty = True
        except Exception as e:
            print("[SENSORS]: ERROR @ %s read with %s" % (self.alias, e))
            self.error_msg = e

    def get_temperature(self):
        return self.last_data

def register_on_state_change_callback(cb):
    global on_state_change_cb
    print("[SENSORS]: register on state change cb")
    on_state_change_cb = cb

def init():
    print("[SENSORS]: init")
    global environment_sensors, realtime_sensors
    environment_sensors.append(TempReader(alias="TEMP"))

async def environment_sensors_action():
    print("[SENSORS]: environment_sensors_action")
    while True:
        for sensor in environment_sensors:
            if sensor.timestamp is None or common.millis_passed(sensor.timestamp) >= sensor.timeout:
                sensor.timestamp = common.get_millis()
                await sensor.action()
                if sensor.dirty:
                    sensor.dirty = False
                    if on_state_change_cb is not None:
                        on_state_change_cb(sensor.alias, sensor.data)

                if sensor.error_msg is not None:
                    if on_state_change_cb is not None:
                        on_state_change_cb(f"{sensor.alias}_ERROR", sensor.error_msg)
                    sensor.error_msg = None
            await asyncio.sleep_ms(0)

async def realtime_sensors_action():
    print("[SENSORS]: realtime_sensors_action")
    while True:
        for sensor in realtime_sensors:
            sensor.action()
            if sensor.dirty:
                sensor.dirty = False
                if on_state_change_cb is not None:
                    on_state_change_cb(sensor.alias, sensor.data)
        await asyncio.sleep_ms(0)

def on_data_request(thing):
    print("[SENSORS]: on_data_request[%s][%s]" % (thing.alias, thing.data))
    for sensor in environment_sensors:
        if sensor.alias == thing.alias:
            if thing.data == "request":
                print(f"[SENSORS]: request {sensor.alias} data")
                sensor.timestamp = None
            elif "timeout" in thing.data:
                try:
                    sensor.timeout = int(thing.data.split(" ")[1])
                except Exception as e:
                    print("[SENSORS]: Error: timeout with %s" % (e))

def test_print(alias, data):
    print("[SENSORS]: CB -- alias[%s], data[%s]" % (alias, data))

async def test_add_tasks():
    print("[SENSORS]: test_add_tasks")
    tasks = []
    tasks.append(asyncio.create_task(realtime_sensors_action()))
    tasks.append(asyncio.create_task(environment_sensors_action()))
    for task in tasks:
        await task
        print("[SENSORS]: Error: loop task finished!")

def test_start():
    print("[SENSORS]: test_start")
    init()
    register_on_state_change_callback(test_print)
    asyncio.run(test_add_tasks())
