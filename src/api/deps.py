"""Connection pool, auth dependencies."""

from mees_shared.db import get_conn, init_pool as _init_pool, close_pool  # noqa: F401
from mees_shared.auth import CurrentUser, get_current_user as _make_get_user  # noqa: F401
from mees_shared.db import pool as _pool_ref
import mees_shared.db as _db_mod

from config.settings import settings

# App-specific auth dependency
get_current_user = _make_get_user(settings.auth_enabled, settings.dev_user_email)

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
    _init_pool(settings.dsn, settings.db_pool_min, settings.db_pool_max)
    conn = _db_mod.pool.getconn()
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(SCHEMA)
    finally:
        _db_mod.pool.putconn(conn)
