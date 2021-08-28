# AQI_Experiment

  

This is micro python script that measures AQI values (PM2.5 PM1.0 PM10) and uploads them on influx DB.

  

**Hardware Requirements:**

  

1) PMS5003

2) Connector Wire (8 pin Molex Connector)

3) ESP32

3) Male-Female Connector Wire

4) USB 2.0 Connector

5) 5v USB Charger

  
  

**Software Requirements:**

  

1) MicroPython (Language)

2) Thonny (IDE)

3) Influx DB (Signed up on Influx Cloud with bucket retention policy of 6 hrs to stay within free tier)

  
  

## How to Use this code:

  

For running code, it is preferable to use updated documentation, but below are step that were used to run

1) Setup Circuit with proper connection wires.

2) Download and open Thonny IDE

3) Open Run and Select Interpreter.

4) Select ESP32

5) Port should appear on dropdown if ESP32 is attached. Select Port.

6) Install Firmware, (Might have to search more links on deploying firmware. But I had to press Boot button while deploying. Also attaching firmware used in repo)

7) Copy main.py and Select File, Save As. Choose Micropython if asked for saving device.

8) Replace ENV variables.

9) Press Run.

  
  

You should be able to see print values on thonne console !!!

  
  
  

## Reference Link:

  

PMS5003 DataSheet:

https://www.aqmd.gov/docs/default-source/aq-spec/resources-page/plantower-pms5003-manual_v2-3.pdf

  
  

## Circuit Reference:

  

**PMS5003:**

  

1. -> (+5v) Input

2. -> GND

4. -> RX Serial port receiving pin/TTL level@3.3V

5. -> TX Serial port sending pin/TTL level@3.3V

  
  
  

**ESP32:**

1. VIN -> (+5v Input)

2. -> GND

3. -> D13 -> RX

4. -> D12 -> TX

  
  ```mermaid
graph LR
A[ESP32] -- VIN -- PIN 1 +ve --> B(Sensor)
A -- GND -- PIN 2 --> B
A -- 12 -- PIN 5 TX --> B
A -- 13 -- PIN 4 RX --> B
```
  

## Other Ways:

**Arduino Code:**

  

https://github.com/adafruit/Adafruit_PM25AQI/blob/master/examples/PM25_test/PM25_test.ino

  
  

**Micropython Links:**

  

- https://randomnerdtutorials.com/getting-started-micropython-esp32-esp8266/

- https://github.com/martonz/pms5003-MicroPython

- https://randomnerdtutorials.com/getting-started-thonny-micropython-python-ide-esp32-esp8266/

- https://microcontrollerslab.com/getting-started-thonny-micropython-ide-esp32-esp8266/



