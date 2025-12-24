import os
import time

from dotenv import load_dotenv, find_dotenv
from flask import Flask, render_template, jsonify, request
from flask_basicauth import BasicAuth
from datetime import datetime

from web_helpers.auth_helper import is_authenticated
from web_helpers.database_helper import get_readings, add_reading, get_last_watered, add_water, setup_database, \
    get_setting
from web_helpers.email_helper import send_success_email, send_error_email
from web_helpers.watering_helper import set_water_enabled, is_water_enabled

# Serves web server for WALTER

# Environment variables
load_dotenv(find_dotenv(".env"))
SECRET_TOKEN  = os.getenv("SECRET_TOKEN")

setup_database()

# Initialise the value if it is not already present
INITIAL_WATER_ENABLED = os.getenv("WATER_ENABLED").lower() in ("true", "1", "yes", "on")

if not get_setting("water_enabled"):
    set_water_enabled(INITIAL_WATER_ENABLED)

# Initialise Flask App & Basic Auth

app = Flask(__name__)

app.config["BASIC_AUTH_USERNAME"] = os.getenv("BASIC_AUTH_USERNAME")
app.config["BASIC_AUTH_PASSWORD"] = os.getenv("BASIC_AUTH_PASSWORD")

basic_auth = BasicAuth(app)

# robots.txt serve on root
@app.route("/robots.txt")
def static_from_root():
    return app.send_static_file("robots.txt")

# index route
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

# Dashboard route
@app.route("/dashboard", methods=["GET"])
@basic_auth.required
def dashboard():
    return render_template("dashboard.html")

# Readings, logging and polling methods

# Fetch readings for plotting
@app.route("/reading", methods=["GET"])
def get_reading():
    # read input to get time frame required
    try:
        since_time = int(request.args.get("since", time.time()))
    except ValueError:
        return jsonify(error="Time frame since variable must be an integer in seconds")

    # get readings
    readings = get_readings(since_time)

    # return json data
    return jsonify(readings)

# Add readings from bot
@app.route("/reading", methods=["POST"])
def post_reading():
    # check if client has permission
    if not is_authenticated(request.headers.get("Authorization")):
        return jsonify(error="Authorization invalid"), 401

    # check the body is of valid format
    try:
        data = request.get_json()

        if not isinstance(data.get("soil_moisture"), (int, float)) or not isinstance(data.get("time"), int):
            return jsonify(error="Reading incorrectly formatted"), 400

    except Exception as e:
        print(e)
        return jsonify(error="Invalid data format"), 400

    # extract information from body and add reading to database
    time_stamp    = data.get("time")
    soil_moisture = data.get("soil_moisture")

    add_reading(time_stamp, soil_moisture)

    return jsonify(status="ok"), 200

# Watering, logging and polling methods


# Fetch most recent watering times
@app.route("/water", methods=["GET"])
def get_water():
    last_watered = get_last_watered()

    # check that there is an event to publish
    if not last_watered:
        return jsonify(error="No water events"), 400
    else:
        return jsonify(last_watered)

# Log water event
@app.route("/water", methods=["POST"])
def post_water():
    # check if client has permission
    if not is_authenticated(request.headers.get("Authorization")):
        return jsonify(error="Authorization invalid"), 401

    # check the body is of valid format
    try:
        data = request.get_json()

        if not isinstance(data.get("time"), int):
            return jsonify(error="Event incorrectly formatted"), 400

    except Exception as e:
        print(e)
        return jsonify(error="Invalid data format"), 400

    # extract information from body and add event to database
    time_stamp = data.get("time")

    add_water(time_stamp)

    # send success email to users
    send_success_email(time_stamp)

    return jsonify(status="ok"), 200

# Control routes for syncing with bot (timezones) and control (enabling/disabling water)

# Water enabled or disabled routes
@app.route("/water/allowed", methods=["GET"])
def water_allowed():
    return jsonify(enabled=is_water_enabled()), 200

@app.route("/water/off", methods=["POST"])
@basic_auth.required
def water_off():
    set_water_enabled(False)
    return "", 204

@app.route("/water/on", methods=["POST"])
@basic_auth.required
def water_on():
    set_water_enabled(True)
    return "", 204

# Error alerting route to send to mail list
@app.route("/alert", methods=["POST"])
def alert():
    # check if client has permission
    if not is_authenticated(request.headers.get("Authorization")):
        return jsonify(error="Authorization invalid"), 401

    # get log from body
    try:
        data = request.get_json()

        if not isinstance(data.get("time"), (int)) or not isinstance(data.get("error"), (str)):
            return jsonify(error="Event incorrectly formatted"), 400

    except Exception:
        return jsonify(error="Invalid data format"), 400

    # extract error message and send email
    time_stamp = data.get("time")
    error_msg  = data.get("error")

    send_error_email(time_stamp, error_msg)

    return jsonify(status="ok"), 200

# Time keeping routes
@app.route("/timezone", methods=["GET"])
def get_time_zone():
    dt_tz = datetime.now().astimezone()
    return jsonify(local_offset=dt_tz.utcoffset().total_seconds())

@app.route("/time", methods=["GET"])
def get_time():
    seconds = time.time()
    return jsonify(time=seconds)

# Running Server & DB configuration
if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
