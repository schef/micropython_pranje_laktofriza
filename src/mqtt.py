import asyncio
from lib_mqtt_as import MQTTClient
import wlan as lan

SUBSCRIBE = None
PUBLISH_PREFIX = None
client = None
on_message_received_cb = None

CREDENTIALS_FILENAME = "credentials.py"

username = None
password = None
server = None

def check_credentials():
    global username, password, server
    try:
        import credentials
        print("[MQTT]: credentials found")
        username = credentials.username
        password = credentials.password
        server = credentials.server
    except:
        print("[MQTT]: credentials not found, using default")
        username = ''
        password = ''
        server = '10.200.60.60'

async def conn_han(client):
    await client.subscribe(SUBSCRIBE, 1)

def on_mqtt_message_received(topic, msg, retained):
    topic = topic.decode()
    msg = msg.decode()
    if "%s/in" % (lan.mac) in topic:
        topic = "/".join(topic.split("/")[2:])
    print("[MQTT]: received [%s] -> [%s]" % (topic, msg))
    if on_message_received_cb != None:
        on_message_received_cb(topic, msg)

async def send_message(topic, msg):
    topic_out = "%s/%s" % (PUBLISH_PREFIX, topic)
    print("[MQTT]: sent [%s] -> [%s]" % (topic, msg))
    await client.publish(topic_out, msg, retain=False, qos=1)

def register_on_message_received_callback(cb):
    global on_message_received_cb
    print("[MQTT]: register on message received cb")
    on_message_received_cb = cb

def write_credentials_to_flash(server, username='', password=''):
    print("[MQTT]: write credentials server[%s], username[%s], password[%s]" % (server, username, password))
    f = open(CREDENTIALS_FILENAME, 'w')
    content = f"server = '{server}'\nusername = '{username}'\npassword = '{password}'\n"
    f.write(content)
    f.close()

def is_connected():
    return client.is_connected()

def init():
    print("[MQTT]: init")
    global SUBSCRIBE, PUBLISH_PREFIX
    #lan.init()
    SUBSCRIBE = "%s/in/#" % (lan.mac)
    PUBLISH_PREFIX = "%s/out" % (lan.mac)
    MQTTClient.DEBUG = True
    check_credentials()
    global client
    client = MQTTClient(client_id=lan.mac, subs_cb=on_mqtt_message_received, connect_coro=conn_han, server=server, user=username, password=password)

async def loop_async():
    print("[MQTT]: start loop_async")
    while True:
        try:
            print("[MQTT]: connect to MQTT")
            await client.connect()
            while True:
                print("[MQTT]: handle connection")
                await asyncio.sleep(10)
        except Exception as e:
            print("[MQTT]: error connect with %s" % (e))
            await asyncio.sleep(10)

def test_async():
    print("[MQTT]: test_async")
    init()
    asyncio.run(loop_async())
