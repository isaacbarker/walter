import time
import os
import sqlite3
import smtplib
import datetime
from pathlib import Path
from email.utils import formataddr
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv, find_dotenv
from flask import Flask, request, jsonify, render_template, send_from_directory

load_dotenv(find_dotenv())

SECRET_TOKEN = os.getenv("SECRET_TOKEN") # pwd on pico for db updates
DB_PATH = "readings.db"

def str_to_bool(value: str) -> bool:
    return value.lower() in ("true", "1", "yes", "on")

WATER_ENABLED = str_to_bool(os.getenv("WATER_ENABLED", "false"))

app = Flask(__name__)

"""Set up email notifications"""
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", 0))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PWD = os.getenv("SMTP_PWD", "")
DOMAIN = os.getenv("DOMAIN")
EMAIL_NAME = os.getenv("EMAIL_NAME")
EMAIL_ADDR = os.getenv("EMAIL_ADDR")

""" robots.txt serve on root"""
@app.route('/robots.txt')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])

"""Root UI with polling system for data fetching"""
@app.route("/", methods=["GET"])
def root():
    return render_template("index.html")

"""Reading logging and polling methods"""
@app.route("/reading", methods=["GET", "POST"])
def reading():
    if request.method == "POST":
        """Record data and store in db"""
        auth_header = request.headers.get("Authorization")

        # check if client has permission to update readings
        if auth_header != f"Bearer {SECRET_TOKEN}":
            return jsonify(error="Authorization invalid"), 401

        # get reading from body
        try:
            data = request.get_json()

            if not isinstance(data.get("soil_moisture"), (int, float)) or not isinstance(data.get("time"), (int)):
                return jsonify(error="Reading incorrectly formatted"), 400


            time_stamp = data.get("time")
            soil_moisture = data.get("soil_moisture")

            # insert data into SQL db
            with sqlite3.connect(DB_PATH) as conn:
                cur = conn.cursor()

                insert_query = """
                INSERT INTO readings (time, soil_moisture)
                VALUES (?, ?);
                """
                reading_data = (time_stamp, soil_moisture)

                cur.execute(insert_query, reading_data)
                conn.commit()

        except Exception:
            return jsonify(error="Invalid data format"), 400

        return jsonify(status="ok"), 200

    elif request.method == "GET":
        """Return readings for ui display"""
        now = time.time()
        
        # get since value from request or default to all values
        try:
            since = int(request.args.get("since", now))
        except ValueError:
            return jsonify(error="Since must be an integer in seconds")
        
        ago_time = now - since

        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()

            rows = cur.execute(
                "SELECT * FROM readings WHERE time >= ? ORDER BY time ASC", 
                (ago_time,)
            ).fetchall()

        data = [
            {
                "time": row[1],
                "soil_moisture": row[2]
            }
            for row in rows
        ]

        return jsonify(data)
    
"""Watering logging and polling methods"""
@app.route("/water", methods=["POST", "GET"])
def water():
    if request.method == "POST":
        """Update watering logs"""
        auth_header = request.headers.get("Authorization")

        # check if client has permission to update water logs
        if auth_header != f"Bearer {SECRET_TOKEN}":
            return jsonify(error="Authorization invalid"), 401

        # get log from body
        try:
            data = request.get_json()

            if not isinstance(data.get("time"), (int)):
                return jsonify(error="Event incorrectly formatted"), 400

            time_stamp = data.get("time")

            # insert data into SQL db
            with sqlite3.connect(DB_PATH) as conn:
                cur = conn.cursor()

                insert_query = """
                INSERT INTO water (time)
                VALUES (?);
                """
                water_data = (time_stamp,)

                cur.execute(insert_query, water_data)
                conn.commit()

        except Exception:
            return jsonify(error="Invalid data format"), 400
                
        # import html template
        BASE_DIR = Path(__file__).parent
        template_path = BASE_DIR / "templates" / "email.html"
        html_template = template_path.read_text(encoding="utf-8")
        
        # format time
        dt = datetime.datetime.fromtimestamp(time_stamp)
        time_str = dt.strftime("%H:%M")
        html_body = html_template.replace("{{ time }}", time_str).replace("{{ domain }}", DOMAIN)

        # send email to notify of watering
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"WALTER WATERED {time_str}"
        msg["From"] = formataddr((EMAIL_NAME, EMAIL_ADDR))

        msg.attach(MIMEText(html_body, "html", "utf-8"))

        recipients = os.getenv("NOTIFY_EMAILS", "").split(",")
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(SMTP_USERNAME, SMTP_PWD)
            for address in recipients:
                msg["To"] = address
                smtp.sendmail(
                    "walter@isaacbarker.net",
                    address,
                    msg.as_string()
                )
        return jsonify(status="ok"), 200
    
    elif request.method == "GET":
        """Return most recent water event"""
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()

            row = cur.execute("""
                SELECT * FROM water
                ORDER BY id DESC
                LIMIT 1;
            """).fetchall()

        if len(row) == 0:
            return jsonify(error="No water events"), 400

        time_stamp = row[0][1]
        data = {"last_watered": time_stamp}

        return jsonify(data)
    
""" Water enabled or disabled route """
@app.route("/can-water", methods=["GET"])
def can_water():
    return jsonify(enabled=WATER_ENABLED, status="ok"), 200

if __name__ == "__main__":
    # init db and insert suitable table to log readings
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()

        # insert readings table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,      
                time INTEGER NOT NULL,          -- Epoch seconds
                soil_moisture REAL NOT NULL      
            )
        """)

        # insert watering log
        cur.execute("""
            CREATE TABLE IF NOT EXISTS water (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time INTEGER NOT NULL           -- Epoch seconds
            )         
        """)

        conn.commit()

if __name__ == "__main__":
    app.run()