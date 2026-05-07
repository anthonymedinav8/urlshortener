from flask import Flask, request, jsonify, redirect
from dotenv import load_dotenv
import psycopg2
import os
import random
import string

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
            click_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

@app.route('/')
def index():
    return jsonify({"status": "URL Shortener running"})

@app.route('/shorten', methods=['POST'])
def shorten_url():
    data = request.get_json()
    url = data.get('url')

    url = url.strip()
    url = url.lower()
    if not url.startswith('http'):
        url = 'https://' + url
    url = url.rstrip('/')

    if not url:
        return jsonify({"error": "URL is required"}), 400

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT short_code FROM urls WHERE original_url = %s", (url,))
    existing = cur.fetchone()

    if existing:
        cur.close()
        conn.close()
        return jsonify({"short_code": existing[0], "message": "URL already exists"}), 200

    short_code = None
    for _ in range(10):
        candidate = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        cur.execute("SELECT id FROM urls WHERE short_code = %s", (candidate,))
        if not cur.fetchone():
            short_code = candidate
            break

    if not short_code:
        cur.close()
        conn.close()
        return jsonify({"error": "Could not generate unique short code"}), 500

    cur.execute(
        "INSERT INTO urls (original_url, short_code) VALUES (%s, %s)",
        (url, short_code)
    )
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"short_code": short_code, "short_url": f"http://localhost:5001/{short_code}"}), 201

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5001)
    