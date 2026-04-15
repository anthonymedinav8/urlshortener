from flask import Flask, request, jsonify, redirect
from dotenv import load_dotenv
import psycopg2
import os
import hashlib

load_dotenv()

app = Flask(__name__)

def get_db():
    return psycopg2.connect(
        dbname="urlshortener",
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host="localhost"
    )

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            id SERIAL PRIMARY KEY,
            original_url TEXT NOT NULL,
            short_code VARCHAR(10) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

@app.route('/')
def index():
    return jsonify({"status": "URL Shortener running"})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
    