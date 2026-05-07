import psycopg2

from .config import Config


def get_db():
    return psycopg2.connect(
        dbname=Config.DB_NAME,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        host=Config.DB_HOST,
        port=Config.DB_PORT,
    )


def init_db():
    conn = get_db()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS urls (
                        id SERIAL PRIMARY KEY,
                        original_url TEXT NOT NULL,
                        short_code VARCHAR(10) UNIQUE NOT NULL,
                        click_count INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                    """
                )
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_urls_short_code ON urls(short_code)"
                )
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_urls_original_url ON urls(original_url)"
                )
    finally:
        conn.close()
