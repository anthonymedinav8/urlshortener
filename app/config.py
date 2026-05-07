import os


class Config:
    DB_NAME = os.getenv("DB_NAME", "urlshortener")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "5432"))

    BASE_URL = os.getenv("BASE_URL", "http://localhost:5001").rstrip("/")
    API_KEY = os.getenv("API_KEY") or None

    RATE_LIMIT_SHORTEN = os.getenv("RATE_LIMIT_SHORTEN", "20 per minute")
    RATE_LIMIT_REDIRECT = os.getenv("RATE_LIMIT_REDIRECT", "120 per minute")
    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"

    DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"


class TestConfig(Config):
    RATE_LIMIT_ENABLED = False
    API_KEY = None
    BASE_URL = "http://test.local"
    TESTING = True
