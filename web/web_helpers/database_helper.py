import os
import sqlite3
import time
from dotenv import load_dotenv, find_dotenv
from datetime import datetime

# Database configuration and system for storing watering data

# Environment variables
load_dotenv(find_dotenv(".env"))
DB_PATH = os.getenv("DB_PATH", "readings.db")

# Database helper functions

def setup_database():
    # Connects and intialises scheme for sqlite databse
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()

        # insert readings table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time INTEGER NOT NULL,
                soil_moisture REAL NOT NULL
            )
        """)

        # insert watering log
        cur.execute("""
            CREATE TABLE IF NOT EXISTS water (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time INTEGER NOT NULL
            )
        """)

        conn.commit()

# Updaters of data

def add_reading(time, soil_moisture):
    # Inserts readings with time and soil moisture into the database
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()

        query = """
                INSERT INTO readings (time, soil_moisture) 
                VALUES (?, ?)
        """

        cur.execute(query, (time, soil_moisture))
        conn.commit()

def add_water(time):
    # Logs watering time into the database
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()

        query = """
            INSERT INTO water (time) 
            VALUES (?)
        """

        cur.execute(query, (time,))
        conn.commit()

# Getters of data

def get_readings(since):
    # Fetches readings since a certain time

    # calculate filters
    ago_time = time.time() - since

    # fetch data
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()

        rows = cur.execute("""
            SELECT * FROM readings WHERE time >= ? ORDER BY time ASC
        """, (ago_time,)).fetchall()


    # convert data to a dictionary
    return [
        {
            "time": row[1],
            "soil_moisture": row[2]
        }
        for row in rows
    ]

def get_last_watered():
    # Fetches last watered time stamp
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()

        row = cur.execute("""
            SELECT * FROM water
            ORDER BY time ASC, id DESC LIMIT 1
        """).fetchall()

    if len(row) == 0: return None

    return {"last_watered": row[0][1]}

