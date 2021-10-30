from machine import Pin, Timer
from time import sleep_ms
import ubluetooth
from time import sleep
from ntptime import settime
from machine import RTC, Pin, UART
try:
    import struct
except ImportError:
    import ustruct as struct




class BLE():


    def __init__(self, name):
        
        self.name = name
        self.ble = ubluetooth.BLE()
        self.ble.active(True)
    
        self.led = Pin(2, Pin.OUT)
        self.timer1 = Timer(0)
        self.timer2 = Timer(1)
        
        self.disconnected()
        self.ble.irq(self.ble_irq)
        self.register()
        self.advertiser()
        self.start_receiving = False


    def connected(self):
        
        self.timer1.deinit()
        self.timer2.deinit()


    def disconnected(self):
        
        self.timer1.init(period=1000, mode=Timer.PERIODIC, callback=lambda t: self.led(1))
        sleep_ms(200)
        self.timer2.init(period=1000, mode=Timer.PERIODIC, callback=lambda t: self.led(0))
    

    def ble_irq(self, event, data):

        if event == 1:
            '''Central connected'''
            self.connected()
            self.led(1)
        
        elif event == 2:
            '''Central disconnected'''
            self.advertiser()
            self.disconnected()
        
        elif event == 3:
            '''New message received'''
            
            buffer = self.ble.gatts_read(self.rx)
            message = buffer.decode('UTF-8')[:-1]
            self.start_receiving = not self.start_receiving
            

            
    def register(self):
        
        # Nordic UART Service (NUS)
        NUS_UUID = '6E400001-B5A3-F393-E0A9-E50E24DCCA9E'
        RX_UUID = '6E400002-B5A3-F393-E0A9-E50E24DCCA9E'
        TX_UUID = '6E400003-B5A3-F393-E0A9-E50E24DCCA9E'
            
        BLE_NUS = ubluetooth.UUID(NUS_UUID)
        BLE_RX = (ubluetooth.UUID(RX_UUID), ubluetooth.FLAG_WRITE)
        BLE_TX = (ubluetooth.UUID(TX_UUID), ubluetooth.FLAG_NOTIFY)
            
        BLE_UART = (BLE_NUS, (BLE_TX, BLE_RX,))
        SERVICES = (BLE_UART, )
        ((self.tx, self.rx,), ) = self.ble.gatts_register_services(SERVICES)

    def send(self, data):
        self.ble.gatts_notify(0, self.tx, data + '\n')


    def advertiser(self):
        name = bytes(self.name, 'UTF-8')
        self.ble.gap_advertise(100, bytearray('\x02\x01\x02') + bytearray((len(name) + 1, 0x09)) + name)
        
# test
blue_led = Pin(2, Pin.OUT)
ble = BLE("ESP32")



uart = UART(1, baudrate=9600, tx=12, rx=13, timeout=2000)


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




skip_reading(1)

while True:
    sleep(0.5)

    val = read_data()
    if val:             
        pm10_standard, pm25_standard, pm100_standard,pm10_env, pm25_env, pm100_env = val
        if ble.start_receiving:
            ble.send("PM2.5: "+ str(pm25_standard))
    else:
        print(val)
        uart = UART(1, baudrate=9600, tx=12, rx=13, timeout=2000)
   
    



# visible in app "Serial Bluetooth Terminal"
