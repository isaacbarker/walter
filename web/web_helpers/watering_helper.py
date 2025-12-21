import os

from web_helpers.database_helper import set_setting, get_setting

# Manages if watering is permitted by the web server

# Get state
def is_water_enabled():
    return get_setting("water_enabled") == '1'

# Set state
def set_water_enabled(value):
    if value:
        set_setting("water_enabled", 1)
    else:
        set_setting("water_enabled", 0)

