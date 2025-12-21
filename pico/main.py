import time

from machine import Pin, I2C, ADC
from sh1106 import SH1106_I2C
import network
import rp2
import framebuf
import ntptime
import urequests as requests
import ujson as json
import uasyncio as asyncio
import gc

import config

## PICO logic for WALTER
# Communicates with API to log watering and monitor soil moisture sensors

## Configuration

# ensure API_ROUTE has trailing /
if not config.API_ROUTE.endswith("/"):
    config.API_ROUTE += "/"

## Display System

# Initialise I2C panel

# Pin setup
sda = Pin(config.DISPLAY_SDA_PIN)
scl = Pin(config.DISPLAY_SCL_PIN)
i2c = I2C(0, sda=sda, scl=scl, freq=400_000)

# Initialisation and clearing
display = SH1106_I2C(
    config.DISPLAY_WIDTH,
    config.DISPLAY_HEIGHT,
    i2c,
    rotate=180
)

time.sleep(0.1)
display.fill(0)
display.show()

# Load logo template for display
with open("oled_template.bin", "rb") as f:
    template_buffer = f.read()

## Initialise GPIO pins for watering system

# Soil Moisture
soil_sensor = ADC(config.SOIL_SENSOR_PIN)

# Pump switch
pump = Pin(config.PUMP_PIN, Pin.OUT)
pump.value(0)

## WLAN configuration & connection
def connect(ssid: str, psk: str, country="GB", max_wait=30) -> network.WLAN:
    # configuration
    rp2.country(country)
    wlan = network.WLAN(network.STA_IF)

    # connect
    wlan.active(True)
    wlan.connect(ssid, psk)

    # await connection
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        time.sleep(1)

    if wlan.status() != 3:
        return None # connection not successful

    # calibrate RTC
    ntptime.settime()

    return wlan

## API communications

def get_headers(data_length):
    return {
        "Authorization": f"Bearer {config.SECRET_TOKEN}",
        "Content-Type": "application/json",
        "Content-Length": str(data_length)
    }

def sanitize_reading(value):
    if value is None or not isinstance(value, (int, float)):
        return 0.0
    if value != value:  # checks for NaN
        return 0.0
    if value < 0:
        return 0.0
    if value > 100:
        return 100.0
    return float(value)

# Timezone offsets
def get_tz_offset() -> float:
    response = requests.get(f"{config.API_ROUTE}timezone")
    offset   = response.json().get("local_offset", 0.0)
    response.close()
    gc.collect()
    return offset

# Log Reading
def post_reading(soil_moisture):
    data = {
        "time": time.time(),
        "soil_moisture": round(soil_moisture, 2)
    }
    
    json_data = json.dumps(data)
    
    response = requests.post(f"{config.API_ROUTE}reading", data=json_data, headers=get_headers(len(json_data)))
    response.close()
    gc.collect()
    
# Log Watering
def post_watering():
    data = {
        "time": time.time()
    }
    
    json_data = json.dumps(data)

    response = requests.post(f"{config.API_ROUTE}water", data=json_data, headers=get_headers(len(json_data)))
    response.close()
    gc.collect()

# Get last watered
def get_last_watered():
    response     = requests.get(f"{config.API_ROUTE}water")
    last_watered = response.json().get("last_watered", 0)
    response.close()
    gc.collect()
    return last_watered

# Check if water is allowed by server
def is_water_allowed():
    response  = requests.get(f"{config.API_ROUTE}water/allowed")
    can_water = response.json().get("enabled")
    response.close()
    gc.collect()
    return can_water

# Sends alert if an error occurs
def alert(error_msg):
    data = {
        "time": time.time(),
        "error": error_msg
    }
    
    json_data = json.dumps(data)

    response = requests.post(f"{config.API_ROUTE}alert", data=json_data, headers=get_headers(len(json_data)))
    response.close()
    gc.collect()

## Sensors, Pump and Screen logic

# Read soil moisture from sensor
def get_reading():
    pd = soil_sensor.read_u16() * 3.3 / 65535
    relative_moisture = 100 - (
                (pd - config.SOIL_WET_BOUNDARY) / (config.SOIL_DRY_BOUNDARY - config.SOIL_WET_BOUNDARY) * 100)
    return sanitize_reading(relative_moisture)

# Turn on pump for duration to water plant
async def water():
    pump.value(1)

    await asyncio.sleep_ms(config.WATER_DURATION)

    pump.value(0)

# Update display OLED
def update_display(soil_moisture, last_watered, local_offset):
    # add logo template to display
    template = framebuf.FrameBuffer(bytearray(template_buffer), config.DISPLAY_WIDTH, config.DISPLAY_HEIGHT, framebuf.MONO_HLSB)
    display.blit(template, 0, 0)

    # update soil moisture value and last watered on display
    display.text(f"Moisture {round(soil_moisture)}%", 8, 32)

    if (time.time() - last_watered) > 24 * 60 * 60:  # display no. days since watering
        delta_t = time.time() - last_watered
        days    = round(delta_t // (24 * 60 * 60))
        display.text(f"Watered: {days}d", 8, 48)
    else:  # display time since watering
        _, _, _, hour, minute, _, _, _ = time.localtime(last_watered + int(local_offset))
        display.text(f"Watered: {(hour):02}:{minute:02}", 8, 48)

    # commit changes
    display.show()

## Run time loop
async def loop():
    
    wlan = connect(config.SSID, config.PSK, config.COUNTRY)

    while True:
        # connect to network
        print(f"Connecting to network {config.SSID}")
                
        if not wlan:
            print(f"Connection timeout, skipping this reading!")
            continue
        
        if wlan.status() != 3:
            wlan = connect(config.SSID, config.PSK, config.COUNTRY)
        
        last_watered = get_last_watered()

        # take soil moisture reading
        print("Taking reading")
        relative_moisture = get_reading()
        print(relative_moisture)

        # determine time
        local_offset = get_tz_offset()
        _, _, _, hour, _, _, _, _ = time.localtime(time.time() + int(local_offset))
        
        # water is soil moisture is below threshold, the time is day and the api allows it
        if relative_moisture <= config.SOIL_THRESHOLD_MIN and hour >= 7 and hour <= 21 and is_water_allowed():
            print("Soil moisture below threshold and watering enabled, enabling pump")
            await water() # turn on pump
        
            # update moisture reading
            new_relative_moisture = get_reading()

            # check watering has been effective if not trigger error
            if int(new_relative_moisture) >= int(relative_moisture):
                print("Recording watering")
                last_watered = time.time()
                post_watering() # record watering
            else:
                alert("Watering unsuccessful, please check reseviour and/or the pump is attached.")
            
            relative_moisture = new_relative_moisture
            
        # save reading
        print(f"Saving reading {round(relative_moisture)}% to API")
        post_reading(relative_moisture)
        
        # update display
        print("Updating Display")
        update_display(relative_moisture, last_watered, local_offset)

        # sleep for interval
        await asyncio.sleep_ms(config.SAMPLE_INTERVAL)

if __name__ == "__main__":
    asyncio.run(loop())



