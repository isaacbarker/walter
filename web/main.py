import time
import os
import sqlite3
from dotenv import load_dotenv, find_dotenv
from flask import Flask, request, jsonify, render_template

load_dotenv(find_dotenv())

SECRET_TOKEN = os.getenv("SECRET_TOKEN") # pwd on pico for db updates
DB_PATH = "readings.db"

app = Flask(__name__)

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
                jsonify(error="Reading incorrectly formatted"), 400


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
                jsonify(error="Event incorrectly formatted"), 400

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

    # run app
    app.run("0.0.0.0", 5500, debug=True)