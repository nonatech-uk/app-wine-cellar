"""Connection pool, auth dependencies."""

from collections.abc import Generator
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request
from psycopg2.pool import ThreadedConnectionPool

from config.settings import settings

pool: ThreadedConnectionPool | None = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS app_user (
    email TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'admin'
);
INSERT INTO app_user (email, display_name, role)
VALUES ('stu@mees.st', 'Stu', 'admin')
ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS wine (
    id SERIAL PRIMARY KEY,
    producer TEXT NOT NULL,
    name TEXT NOT NULL,
    vintage INTEGER,
    region TEXT,
    country TEXT,
    wine_type TEXT,
    style TEXT,
    grape_variety TEXT,
    abv REAL,
    vivino_url TEXT,
    vivino_avg_rating REAL,
    vivino_ratings_count INTEGER,
    drinking_window TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_wine_identity
    ON wine (producer, name, COALESCE(vintage, 0));
CREATE INDEX IF NOT EXISTS idx_wine_producer ON wine(producer);
CREATE INDEX IF NOT EXISTS idx_wine_country ON wine(country);

CREATE TABLE IF NOT EXISTS wine_log (
    id SERIAL PRIMARY KEY,
    wine_id INTEGER NOT NULL REFERENCES wine(id),
    logged_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    source TEXT NOT NULL DEFAULT 'manual',
    rating REAL,
    review TEXT,
    personal_note TEXT,
    location TEXT,
    gps_lat REAL,
    gps_lng REAL,
    label_image_filename TEXT,
    pipeline_item_id TEXT
);
CREATE INDEX IF NOT EXISTS idx_wine_log_wine_id ON wine_log(wine_id);
CREATE INDEX IF NOT EXISTS idx_wine_log_logged_at ON wine_log(logged_at);

CREATE TABLE IF NOT EXISTS wine_cellar (
    id SERIAL PRIMARY KEY,
    wine_id INTEGER NOT NULL REFERENCES wine(id),
    quantity INTEGER NOT NULL DEFAULT 0,
    storage_location TEXT,
    purchase_date DATE,
    purchase_price REAL,
    purchase_currency TEXT DEFAULT 'GBP',
    notes TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(wine_id, storage_location)
);
CREATE INDEX IF NOT EXISTS idx_wine_cellar_wine_id ON wine_cellar(wine_id);

CREATE TABLE IF NOT EXISTS wine_wishlist (
    id SERIAL PRIMARY KEY,
    wine_id INTEGER NOT NULL REFERENCES wine(id),
    wishlisted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    notes TEXT,
    acquired BOOLEAN NOT NULL DEFAULT false,
    UNIQUE(wine_id)
);
"""


def init_pool() -> None:
    global pool
    pool = ThreadedConnectionPool(
        settings.db_pool_min,
        settings.db_pool_max,
        settings.dsn,
    )
    conn = pool.getconn()
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(SCHEMA)
    finally:
        pool.putconn(conn)


def close_pool() -> None:
    global pool
    if pool:
        pool.closeall()
        pool = None


def get_conn() -> Generator:
    assert pool is not None, "Connection pool not initialised"
    conn = pool.getconn()
    try:
        yield conn
    finally:
        pool.putconn(conn)


@dataclass
class CurrentUser:
    email: str
    display_name: str
    role: str


def get_current_user(request: Request, conn=Depends(get_conn)) -> CurrentUser:
    if not settings.auth_enabled:
        email = settings.dev_user_email
    else:
        email = request.headers.get("Remote-Email")
        if not email:
            raise HTTPException(401, "Not authenticated")

    cur = conn.cursor()
    cur.execute(
        "SELECT email, display_name, role FROM app_user WHERE email = %s",
        (email,),
    )
    row = cur.fetchone()
    if not row:
        raise HTTPException(403, f"User {email} is not authorised")

    display_name_header = request.headers.get("Remote-Name")
    return CurrentUser(
        email=row[0],
        display_name=display_name_header or row[1],
        role=row[2],
    )
