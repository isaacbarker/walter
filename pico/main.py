import time

from machine import Pin, I2C, ADC
from sh1106 import SH1106_I2C

import config

# PICO logic for WALTER
# Communicates with API to log watering and monitor soil moisture sensors

# Display System

# Initialise I2C panel

# Pin setup
sda = Pin(config.DISPLAY_SDA_PIN)
scl = Pin(config.DISPLAY_SCL_PIN)
i2c = I2C(sda=sda, scl=scl, freq=400_000)

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

# Initialise GPIO pins for watering system

# Soil Moisture
soil_sensor = ADC(config.SOIL_SENSOR_PIN)

# Pump switch
pump = Pin(config.PUMP_PIN, Pin.OUT)
pump.value(0)

