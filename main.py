# Forked from Adafruit/PMS5003_Air_Quality_Sensor/PMS5003_CircuitPython/PMS5003_example.py
import utime
import urequests
import CONSTANTS
from time import sleep
from ntptime import settime
from machine import RTC, Pin, UART
try:
    import struct
except ImportError:
    import ustruct as struct

HEADER = {"authorization": 'Token {0}'.format(CONSTANTS.INFLUX_DB_TOKEN)}
INFLUX_URL = "https://us-east-1-1.aws.cloud2.influxdata.com/api/v2/write?org={0}&bucket={1}&precision=s".format(CONSTANTS.INFLUX_ORG,CONSTANTS.INFLUX_BUCKET)

uart = UART(1, baudrate=9600, tx=12, rx=13, timeout=2000)

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
            print("Frame Length Mismatched")
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

def string_gen(pm10_standard, pm10_env, pm25_standard, pm25_env, pm100_standard, pm100_env, timestamp, sensor_reading, new_line):
    sensor_reading += 'aqi,host={0} pm1.0_standard={1} {2} \n'.format('room',pm10_standard,timestamp)
    sensor_reading += 'aqi,host={0} pm1.0_env={1} {2} \n'.format('room',pm10_env,timestamp)
    sensor_reading += 'aqi,host={0} pms2.5_standard={1} {2} \n'.format('room',pm25_standard,timestamp)
    sensor_reading += 'aqi,host={0} pms2.5_env={1} {2} \n'.format('room',pm25_env,timestamp)
    sensor_reading += 'aqi,host={0} pm10_standard={1} {2} \n'.format('room',pm100_standard,timestamp)
    if new_line == True:
        sensor_reading += 'aqi,host={0} pm10_env={1} {2} \n'.format('room',pm100_env,timestamp)
    else:
        sensor_reading += 'aqi,host={0} pm10_env={1} {2}'.format('room',pm100_env,timestamp)
    return sensor_reading










data_push_indicator = True
        
do_connect()
rtc = RTC() # initialize the RTC
settime() # set the RTC's time using ntptime

epoch_offset = 946684800
led = Pin(2, Pin.OUT)
interval = 4
index = 0
sensor_reading = ''
skip = 20
skip_index = 0

skip_reading(1)

while True:
    if data_push_indicator == True:
        led.value(not led.value())
    else:
        led.value(0)
    sleep(0.5)
    if (data_push_indicator == True) and (skip_index < skip):
        skip_index = skip_index + 1
        continue
    else:
        skip_index = 0
        val = read_data()
        if val:             
            pm10_standard, pm25_standard, pm100_standard,pm10_env, pm25_env, pm100_env = val
            print("Reading: {0}, PM2.5: {1}".format(index, pm25_standard))
            print("---------------------------------------")
            timestamp = utime.time() + epoch_offset
            if index < interval:
                index = index + 1
                string_gen(pm10_standard, pm10_env, pm25_standard, pm25_env, pm100_standard, pm100_env, timestamp, sensor_reading, True)
            else:
                string_gen(pm10_standard, pm10_env, pm25_standard, pm25_env, pm100_standard, pm100_env, timestamp, sensor_reading, False)
                index = 0
                data_push_indicator = push_data(sensor_reading)
                sensor_reading = ""
        else:
            data_push_indicator = False
            print(val)
            uart = UART(1, baudrate=9600, tx=12, rx=13, timeout=2000)
   
    
