# network configuration
TZ = 1 # e.g. BST (+1) or GMT (0)
SSID = "BT-NJCMTH"
PSK = "HK9fu3MVQ6Ky9u"
SECRET_TOKEN = "2E6FA4DDED67DC4EA2CCB8F4C1333"
COUNTRY = "GB"
API_ROUTE = "http://192.168.1.1:5678/"

# oled display I2C configuration
DISPLAY_WIDTH = 128 # px
DISPLAY_HEIGHT = 64 # px
DISPLAY_SDA_PIN = 4
DISPLAY_SCL_PIN = 5

# soil moisture sensor
SOIL_SENSOR_PIN = 26
SOIL_DRY_BOUNDARY = 2.8 # V
SOIL_WET_BOUNDARY = 1.0 # V
SOIL_THRESHOLD_MIN = 45 # soil moisture % to trigger watering
WATER_DURATION = 6_000 # ms

# pump 
PUMP_PIN = 16

# general
SAMPLE_INTERVAL = 30 * 60000 # ms

