import logging
import random
import string

import psycopg2
from flask import Blueprint, current_app, jsonify, redirect, request

from .auth import require_api_key
from .db import get_db
from .validators import is_valid_short_code, normalize_and_validate_url

logger = logging.getLogger(__name__)
bp = Blueprint("urlshortener", __name__)

SHORT_CODE_LENGTH = 6
SHORT_CODE_CHARS = string.ascii_letters + string.digits
GENERATION_ATTEMPTS = 10


def _generate_short_code(cur):
    for _ in range(GENERATION_ATTEMPTS):
        candidate = "".join(random.choices(SHORT_CODE_CHARS, k=SHORT_CODE_LENGTH))
        cur.execute("SELECT 1 FROM urls WHERE short_code = %s", (candidate,))
        if not cur.fetchone():
            return candidate
    return None


@bp.route("/", methods=["GET"])
def index():
    return jsonify({"status": "ok", "service": "urlshortener"})


@bp.route("/healthz", methods=["GET"])
def healthz():
    try:
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        finally:
            conn.close()
        return jsonify({"status": "ok", "db": "ok"})
    except psycopg2.Error:
        logger.exception("Health check failed")
        return jsonify({"status": "degraded", "db": "error"}), 503


@bp.route("/shorten", methods=["POST"])
@require_api_key
def shorten_url():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a JSON object"}), 400

    url, err = normalize_and_validate_url(data.get("url"))
    if err:
        return jsonify({"error": err}), 400

    try:
        conn = get_db()
    except psycopg2.Error:
        logger.exception("DB connection failed")
        return jsonify({"error": "Service unavailable"}), 503

    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT short_code FROM urls WHERE original_url = %s", (url,)
                )
                row = cur.fetchone()
                if row:
                    short_code = row[0]
                    return (
                        jsonify(
                            {
                                "short_code": short_code,
                                "short_url": f"{current_app.config['BASE_URL']}/{short_code}",
                                "message": "URL already exists",
                            }
                        ),
                        200,
                    )

                short_code = _generate_short_code(cur)
                if not short_code:
                    logger.error("Could not generate unique short code after %d attempts", GENERATION_ATTEMPTS)
                    return jsonify({"error": "Could not generate unique short code"}), 500

                cur.execute(
                    "INSERT INTO urls (original_url, short_code) VALUES (%s, %s)",
                    (url, short_code),
                )
        return (
            jsonify(
                {
                    "short_code": short_code,
                    "short_url": f"{current_app.config['BASE_URL']}/{short_code}",
                }
            ),
            201,
        )
    except psycopg2.Error:
        logger.exception("Database error during shorten")
        return jsonify({"error": "Database error"}), 500
    finally:
        conn.close()


@bp.route("/<short_code>", methods=["GET"])
def redirect_url(short_code):
    if not is_valid_short_code(short_code):
        return jsonify({"error": "Invalid short code"}), 400

    try:
        conn = get_db()
    except psycopg2.Error:
        logger.exception("DB connection failed")
        return jsonify({"error": "Service unavailable"}), 503

    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE urls SET click_count = click_count + 1 "
                    "WHERE short_code = %s RETURNING original_url",
                    (short_code,),
                )
                row = cur.fetchone()
                if not row:
                    return jsonify({"error": "Short code not found"}), 404
                return redirect(row[0])
    except psycopg2.Error:
        logger.exception("Database error during redirect")
        return jsonify({"error": "Database error"}), 500
    finally:
        conn.close()
