from flask import Flask, request, jsonify, redirect
from contextlib import contextmanager
from urllib.parse import urlparse
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

@contextmanager
def get_cursor():
    """Context manager ensuring connections/cursors close and commit automatically."""
    conn = get_db()
    try:
        cur = conn.cursor()
        try:
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
    finally:
        conn.close()

def init_db():
    with get_cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS urls (
                id SERIAL PRIMARY KEY,
                original_url TEXT NOT NULL,
                short_code VARCHAR(10) UNIQUE NOT NULL,
                click_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

@app.route('/')
def index():
    return jsonify({"status": "URL Shortener running"})

@app.route('/shorten', methods=['POST'])
def shorten_url():
    data = request.get_json(silent=True)
    if not data or 'url' not in data:
        return jsonify({"error": "Missing url payload"}), 400

    raw_url = data['url'].strip()
    if not raw_url:
        return jsonify({"error": "URL cannot be empty"}), 400

    # Domain-only lowercasing (preserves path case integrity)
    try:
        processed_url = raw_url if '://' in raw_url else 'https://' + raw_url
        parsed = urlparse(processed_url)
        if not parsed.scheme or not parsed.netloc:
            return jsonify({"error": "Invalid URL structure"}), 400

        normalized_url = parsed._replace(
            scheme=parsed.scheme.lower(),
            netloc=parsed.netloc.lower()
        ).geturl().rstrip('/')
    except Exception:
        return jsonify({"error": "Failed to parse URL"}), 400

    # Idempotency check: Look for existing short code
    with get_cursor() as cur:
        cur.execute("SELECT short_code FROM urls WHERE original_url = %s", (normalized_url,))
        existing = cur.fetchone()
        if existing:
            return jsonify({
                "short_code": existing[0],
                "message": "URL already exists"
            }), 200

    short_code = None

    # Atomic INSERT loop handling UniqueViolation constraints safely
    for _ in range(10):
        candidate = ''.join(random.choices(string.ascii_letters + string.digits, k=6))

        try:
            with get_cursor() as cur:
                cur.execute(
                    "INSERT INTO urls (original_url, short_code) VALUES (%s, %s)",
                    (normalized_url, candidate)
                )
            short_code = candidate
            break
        except psycopg2.errors.UniqueViolation:
            continue

    if not short_code:
        return jsonify({"error": "Could not generate unique short code"}), 500

    return jsonify({
        "short_code": short_code,
        "short_url": f"http://localhost:5001/{short_code}"
    }), 201

@app.route('/<short_code>', methods=['GET'])
def redirect_url(short_code):
    with get_cursor() as cur:
        cur.execute("SELECT original_url FROM urls WHERE short_code = %s", (short_code,))
        result = cur.fetchone()

        if not result:
            return jsonify({"error": "Short code not found"}), 404

        original_url = result[0]

        # Atomically increment click count
        cur.execute("UPDATE urls SET click_count = click_count + 1 WHERE short_code = %s", (short_code,))

    return redirect(original_url)

@app.route('/stats/<short_code>', methods=['GET'])
def get_stats(short_code):
    with get_cursor() as cur:
        cur.execute("SELECT original_url, click_count, created_at FROM urls WHERE short_code = %s", (short_code,))
        result = cur.fetchone()

        if not result:
            return jsonify({"error": "Short code not found"}), 404

    return jsonify({
        "short_code": short_code,
        "original_url": result[0],
        "click_count": result[1],
        "created_at": str(result[2]),
        "short_url": f"http://localhost:5001/{short_code}"
    }), 200

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5001, threaded=True)
    