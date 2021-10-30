import utime
import usocket as socket
import urequests
import CONSTANTS
from time import sleep
from ntptime import settime
from machine import RTC, Pin, UART
try:
    import struct
except ImportError:
    import ustruct as struct

OFFLINE_MODE=True
HEADER = {"authorization": 'Token {0}'.format(CONSTANTS.INFLUX_DB_TOKEN)}
INFLUX_URL = "https://us-east-1-1.aws.cloud2.influxdata.com/api/v2/write?org={0}&bucket={1}&precision=s".format(CONSTANTS.INFLUX_ORG,CONSTANTS.INFLUX_BUCKET)

uart = UART(1, baudrate=9600, tx=12, rx=13, timeout=2000)
interval = 4
epoch_offset = 946684800

def do_connect():
    import network
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect(CONSTANTS.WIFI_NAME, CONSTANTS.WIFI_PASS)
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())
    
def do_offline_connect():
    import network
    
    ssid = 'AQI'
    password = '123456789'

    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=ssid, password=password)
    while ap.active() == False:
        pass

    print('Connection successful')
    print(ap.ifconfig())

    print('network config:', ap.ifconfig())
    
def push_data(resp_data):
    # POST data to influxdb
    try:
        resp = urequests.post(INFLUX_URL, data=resp_data, headers=HEADER)
        resp.close()
        print('response: {}'.format(resp.status_code))
        return True
    except Exception as e:
        print('Error: {}'.format(e))
        return False
    
def read_data():
    data = uart.read(32)  # read up to 32 bytes
    buffer = []
    if data:
        data = list(data)
        buffer += data

        while buffer and buffer[0] != 0x42:
            buffer.pop(0)

        if len(buffer) > 200:
            buffer = []  # avoid an overrun if all bad data
        if len(buffer) < 32:
            print("buffer less than 32, contains {0}".format(len(buffer)))
            return None

        if buffer[1] != 0x4d:
            buffer.pop(0)
            print("Not found 0x4d on 1st index")
            return None

        frame_len = struct.unpack(">H", bytes(buffer[2:4]))[0]
        if frame_len != 28:
            buffer = []
            print("Frame Length Mismatched " + str(frame_len))
            return None

        frame = struct.unpack(">HHHHHHHHHHHHHH", bytes(buffer[4:]))

        pm10_standard, pm25_standard, pm100_standard, pm10_env, \
            pm25_env, pm100_env, particles_03um, particles_05um, particles_10um, \
            particles_25um, particles_50um, particles_100um, skip, checksum = frame

        check = sum(buffer[0:30])

        if check != checksum:
            buffer = []
            print("checksum failed")
            return None
        buffer = buffer[32:]
        return [pm10_standard, pm25_standard, pm100_standard,pm10_env, pm25_env, pm100_env]

def skip_reading(n):
    index = 0
    while index < n:
        val = read_data()
        if val:
            index = index + 1
        else:
            uart = UART(1, baudrate=9600, tx=12, rx=13, timeout=2000)

def string_gen(pm10_standard, pm10_env, pm25_standard, pm25_env, pm100_standard, pm100_env, timestamp, sensor_reading, new_line):
    sensor_reading += 'aqi,host={0} pm1.0_standard={1} {2} \n'.format('room',pm10_standard,timestamp)
    sensor_reading += 'aqi,host={0} pm1.0_env={1} {2} \n'.format('room',pm10_env,timestamp)
    sensor_reading += 'aqi,host={0} pms2.5_standard={1} {2} \n'.format('room',pm25_standard,timestamp)
    sensor_reading += 'aqi,host={0} pms2.5_env={1} {2} \n'.format('room',pm25_env,timestamp)
    sensor_reading += 'aqi,host={0} pm10_standard={1} {2} \n'.format('room',pm100_standard,timestamp)
    sensor_reading += 'aqi,host={0} pm10_env={1} {2}'.format('room',pm100_env,timestamp)
    if new_line == True:
        sensor_reading += ' \n'

    return sensor_reading

def html_string_gen(pm10_standard, pm10_env, pm25_standard, pm25_env, pm100_standard, pm100_env):
    sensor_reading = ""
    sensor_reading += 'pm1.0_standard={0} \n'.format(pm10_standard)
    sensor_reading += 'pm1.0_env={0} \n'.format(pm10_env)
    sensor_reading += 'pms2.5_standard={0} \n'.format(pm25_standard)
    sensor_reading += 'pms2.5_env={0}\n'.format(pm25_env)
    sensor_reading += 'pm10_standard={0}\n'.format(pm100_standard)
    sensor_reading += 'pm10_env={0} \n'.format(pm100_env)


    return sensor_reading


def web_page():
  html = """<html><head><meta name="viewport" content="width=device-width, initial-scale=1"</head><body><h1>Hello, World!</h1></body></html>"""
  return html

def aqi_page(values):
  html = '<html><head><meta name="viewport" content="width=device-width, initial-scale=1"</head><body><h1>AQI Values</h1>{0}</body></html>'.format(values)
  return html


def sensor_push_at_interval(pm10_standard, pm10_env, pm25_standard, pm25_env, pm100_standard, pm100_env, sensor_reading, index, data_push_indicator):
    timestamp = utime.time() + epoch_offset
    if index < interval:
        index = index + 1
        sensor_reading = string_gen(pm10_standard, pm10_env, pm25_standard, pm25_env, pm100_standard, pm100_env, timestamp, sensor_reading, True)
    else:
        sensor_reading = string_gen(pm10_standard, pm10_env, pm25_standard, pm25_env, pm100_standard, pm100_env, timestamp, sensor_reading, False)
        index = 0
        data_push_indicator = push_data(sensor_reading)
        print(sensor_reading)
        sensor_reading = ""
    return [index, data_push_indicator, sensor_reading]

def led_toggle(data_push_indicator):
    if data_push_indicator == True:
        led.value(not led.value())
    else:
        led.value(0)

def safe_read():
    while True:
        val = read_data()
        if val:
            return val
        else:
            uart = UART(1, baudrate=9600, tx=12, rx=13, timeout=2000)


data_push_indicator = True

if OFFLINE_MODE == False:
    do_connect()
    rtc = RTC() # initialize the RTC
    settime() # set the RTC's time using ntptime
else:
    do_offline_connect()
led = Pin(2, Pin.OUT)

index = 0
sensor_reading = ''
skip = 30
skip_index = 0

skip_reading(1)
print("Skipped first reading ")

if OFFLINE_MODE == True:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', 80))
    s.listen(5)
    
    while True:
        conn, addr = s.accept()
        request = conn.recv(1024)
        val = safe_read()
        pm10_standard, pm25_standard, pm100_standard,pm10_env, pm25_env, pm100_env = val
        response = aqi_page(html_string_gen(pm10_standard, pm25_standard, pm100_standard,pm10_env, pm25_env, pm100_env))
        conn.send(response)
        conn.close()
    s.close()
else:       
    while True:
        led_toggle(data_push_indicator)
        sleep(0.5)
        if (data_push_indicator == True) and (skip_index < skip):
            skip_index = skip_index + 1
            continue
        else:
            skip_index = 0
            val = read_data()
            if val:             
                pm10_standard, pm25_standard, pm100_standard,pm10_env, pm25_env, pm100_env = val
                print("Reading: {0}, PM2.5: {1}".format(index, pm25_env))
                print("---------------------------------------")
                index, data_push_indicator, sensor_reading = sensor_push_at_interval(pm10_standard, pm10_env, pm25_standard, pm25_env, pm100_standard, pm100_env, sensor_reading, index, data_push_indicator)
            else:
                data_push_indicator = False
                print(val)
                uart = UART(1, baudrate=9600, tx=12, rx=13, timeout=2000)
   


