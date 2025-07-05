from machine import Pin, I2C, ADC, 
import time
import framebuf
import uasyncio as asyncio
import ntptime
import network
import urequests as requests
import ujson as json
import rp2
from sh1106 import SH1106_I2C
import config

# initialise I2C panel
sda = Pin(config.DISPLAY_SDA_PIN)
scl = Pin(config.DISPLAY_SCL_PIN)
i2c = I2C(0, sda=sda, scl=scl, freq=400000)

display = SH1106_I2C(config.DISPLAY_WIDTH, config.DISPLAY_HEIGHT, i2c, rotate=180)
time.sleep(0.1)
display.fill(0)
display.show()

# load in logo template for display
with open("oled_template.bin", "rb") as f:
    buf = f.read()

# initialise soil moisture sensor
soil_sensor = ADC(config.SOIL_SENSOR_PIN)

# initialise pump switch
pump = Pin(config.PUMP_PIN, Pin.OUT)
pump.value(0)

# connect to network with WIFI
def connect(ssid: str, psk: str, country="GB", max_wait=30) -> network.WLAN:
    rp2.country(country)
    
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, psk)

    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print(f"Waiting for connection to {ssid}...")
        time.sleep(1)
    
    if wlan.status() != 3:
        raise RuntimeError(f"Network connection to {ssid} failed")
    else:
        print(f"Connected to {ssid} as {wlan.ifconfig()[0]}")
        
    return wlan

connect(config.SSID, config.PSK, config.COUNTRY) # connect to network
ntptime.settime() # calibrate RTC

"""Reading Update System"""
def get_reading() -> int:
    # return relative soil moisture
    pd = soil_sensor.read_u16() * 3.3 / 65535
    relative_moisture = 100 - (pd - config.SOIL_WET_BOUNDARY) / (config.SOIL_DRY_BOUNDARY - config.SOIL_WET_BOUNDARY) * 100
    return relative_moisture

def save_reading(soil_moisture: int) -> None:
    headers = {
        "Authorization": f"Bearer {config.SECRET_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "time": time.time(),
        "soil_moisture": round(soil_moisture)
    }

    print("Sending reading data to server: " + str(data))
    
    # send request to server
    response = requests.post("http://192.168.1.218:5500/reading", data=json.dumps(data), headers=headers)
    response.close()

"""Watering System"""
def get_last_watered() -> int:
    response = requests.get("http://192.168.1.218:5500/water")
    last_watered = response.json().get("last_watered", 0)
    return last_watered

def save_watering() -> None:
    headers = {
        "Authorization": f"Bearer {config.SECRET_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "time": time.time(),
    }

    print("Sending water data to server: " + str(data))
    
    # send request to server
    response = requests.post("http://192.168.1.218:5500/water", data=json.dumps(data), headers=headers)
    response.close()

def water() -> None:
    # water plant until moisture reaches target
    print("Watering plant...")
    pump.value(1)
    
    while True:
        relative_moisture = get_reading()
        if relative_moisture > config.SOIL_TARGET:
            break

        time.sleep_ms(100)

    pump.value(0)
    print("Plant watering complete!")

"""OLED Display System"""
def update_display(soil_moisture: int, last_watered: int) -> None:
    # add logo template to display
    template = framebuf.FrameBuffer(bytearray(buf), config.DISPLAY_WIDTH, config.DISPLAY_HEIGHT, framebuf.MONO_HLSB)
    display.blit(template, 0, 0)

    # update soil moisture value and last watered on display
    display.text(f"Moisture {round(soil_moisture)}%", 8, 32)
    _, _, _, hour, minute, _, _, _ = time.localtime(last_watered + (60 * 60 * config.TZ))
    display.text(f"Watered: {(hour):02}:{minute:02}", 8, 48)

    # commit changes
    display.show()

"""Run time loop"""
async def loop() -> None:

    last_watered = get_last_watered()

    while True:
        # take soil moisture reading and interpret whether watering should occur
        relative_moisture = get_reading()

        if relative_moisture <= config.SOIL_THRESHOLD:
            water()
            last_watered = time.time()
            relative_moisture = get_reading() # update new moisture level
            save_watering()

        # update displays
        save_reading(relative_moisture)
        update_display(relative_moisture, last_watered)

        await asyncio.sleep_ms(config.SAMPLE_INTERVAL)

if __name__ == "__main__":
    asyncio.run(loop())
    

