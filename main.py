# Forked from Adafruit/PMS5003_Air_Quality_Sensor/PMS5003_CircuitPython/PMS5003_example.py
import urequests
import utime
from ntptime import settime
from machine import RTC, Pin, UART
from time import sleep

try:
    import struct
except ImportError:
    import ustruct as struct


uart = UART(1, baudrate=9600, tx=12, rx=13, timeout=2000)
token = 'INFLUX_DB_TOKEN'
INFLUX_ORG = 'INFLUX_ORG'
INFLUX_BUCKET = 'aqi'
headers = {"authorization": 'Token {1}'.format(token)}
url = "https://us-east-1-1.aws.cloud2.influxdata.com/api/v2/write?org={1}&bucket={2}&precision=s".format(INFLUX_ORG,INFLUX_BUCKET)
data_push_indicator = True

# 
def do_connect():
    import network
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect('WIFI_NAME', 'WIFI_PASS')
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())
    
def push_data(resp_data):
    # POST data to influxdb
    try:
        resp = urequests.post(url, data=resp_data, headers=headers)
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
skip_first_reading = True

while skip_first_reading:
    val = read_data()
    if val:
        skip_first_reading = False

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
            x = utime.time() + epoch_offset
            
            if index < interval:
                index = index + 1
                sensor_reading += 'aqi,host={0} pms2.5_standard={1} {2} \n'.format('room',pm25_standard,x)
                sensor_reading += 'aqi,host={0} pms2.5_env={1} {2} \n'.format('room',pm25_env,x)
            else:
                sensor_reading += 'aqi,host={0} pms2.5_standard={1} {2} \n'.format('room',pm25_standard,x)
                sensor_reading += 'aqi,host={0} pms2.5_env={1} {2}'.format('room',pm25_env,x)
                index = 0
                data_push_indicator = push_data(sensor_reading)
                sensor_reading = ""
        else:
            data_push_indicator = False
            print(val)
            uart = UART(1, baudrate=9600, tx=12, rx=13, timeout=2000)
   
    