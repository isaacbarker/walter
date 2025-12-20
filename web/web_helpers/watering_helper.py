import os

from web.web_helpers.database_helper import set_setting, get_setting

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

# Initialise the value if it is not already present
INITIAL_WATER_ENABLED = os.getenv("WATER_ENABLED").lower() in ("true", "1", "yes", "on")

if not get_setting("water_enabled"):
    set_water_enabled(INITIAL_WATER_ENABLED)

