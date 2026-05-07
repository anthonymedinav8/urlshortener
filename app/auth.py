from functools import wraps

from flask import current_app, jsonify, request


def require_api_key(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        configured = current_app.config.get("API_KEY")
        if configured:
            provided = request.headers.get("X-API-Key")
            if provided != configured:
                return jsonify({"error": "Unauthorized"}), 401
        return view(*args, **kwargs)

    return wrapper
