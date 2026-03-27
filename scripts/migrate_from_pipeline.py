#!/usr/bin/env python3
"""Migrate wine data from pipeline database to wine database.

Usage:
    python3 scripts/migrate_from_pipeline.py [PIPELINE_DSN] [WINE_DSN]
"""

import re
import sys

import psycopg2

PIPELINE_DSN = sys.argv[1] if len(sys.argv) > 1 else "host=localhost port=5432 dbname=pipeline user=pipeline password=xiAsvijVRs3WME6UbpDbfspt sslmode=prefer"
WINE_DSN = sys.argv[2] if len(sys.argv) > 2 else "host=localhost port=5432 dbname=wine user=wine password=EyJbH-omXM3U3SDq1PyYkI_nfdCQLs-q sslmode=prefer"


def extract_filename(url: str | None) -> str | None:
    """Extract filename from a wine.mees.st URL or Vivino URL."""
    if not url:
        return None
    # Already a filename
    if "/" not in url:
        return url
    # Extract last path segment
    parts = url.rstrip("/").split("/")
    return parts[-1] if parts else None


def main():
    src = psycopg2.connect(PIPELINE_DSN)
    dst = psycopg2.connect(WINE_DSN)
    src.autocommit = True
    dst.autocommit = False

    try:
        sc = src.cursor()
        dc = dst.cursor()

        # --- wine table ---
        print("Migrating wine table...")
        sc.execute("SELECT * FROM wine ORDER BY id")
        cols = [desc[0] for desc in sc.description]
        rows = sc.fetchall()
        for row in rows:
            d = dict(zip(cols, row))
            dc.execute("""
                INSERT INTO wine (id, producer, name, vintage, region, country, wine_type, style,
                                  grape_variety, abv, vivino_url, vivino_avg_rating, vivino_ratings_count,
                                  drinking_window, created_at, updated_at)
                VALUES (%(id)s, %(producer)s, %(name)s, %(vintage)s, %(region)s, %(country)s,
                        %(wine_type)s, %(style)s, %(grape_variety)s, %(abv)s, %(vivino_url)s,
                        %(vivino_avg_rating)s, %(vivino_ratings_count)s, %(drinking_window)s,
                        %(created_at)s, %(updated_at)s)
                ON CONFLICT (producer, name, COALESCE(vintage, 0)) DO NOTHING
            """, d)
        print(f"  {len(rows)} wine rows")

        # --- wine_log table ---
        print("Migrating wine_log table...")
        sc.execute("SELECT * FROM wine_log ORDER BY id")
        cols = [desc[0] for desc in sc.description]
        rows = sc.fetchall()
        for row in rows:
            d = dict(zip(cols, row))
            # Convert label_image_url to filename
            url_col = d.get("label_image_url") or d.get("label_image_filename")
            d["label_image_filename"] = extract_filename(url_col)
            dc.execute("""
                INSERT INTO wine_log (id, wine_id, logged_at, source, rating, review, personal_note,
                                      location, gps_lat, gps_lng, label_image_filename, pipeline_item_id)
                VALUES (%(id)s, %(wine_id)s, %(logged_at)s, %(source)s, %(rating)s, %(review)s,
                        %(personal_note)s, %(location)s, %(gps_lat)s, %(gps_lng)s,
                        %(label_image_filename)s, %(pipeline_item_id)s)
                ON CONFLICT DO NOTHING
            """, d)
        print(f"  {len(rows)} wine_log rows")

        # --- wine_cellar table ---
        print("Migrating wine_cellar table...")
        sc.execute("SELECT * FROM wine_cellar ORDER BY id")
        cols = [desc[0] for desc in sc.description]
        rows = sc.fetchall()
        for row in rows:
            d = dict(zip(cols, row))
            dc.execute("""
                INSERT INTO wine_cellar (id, wine_id, quantity, storage_location, purchase_date,
                                         purchase_price, purchase_currency, notes, updated_at)
                VALUES (%(id)s, %(wine_id)s, %(quantity)s, %(storage_location)s, %(purchase_date)s,
                        %(purchase_price)s, %(purchase_currency)s, %(notes)s, %(updated_at)s)
                ON CONFLICT DO NOTHING
            """, d)
        print(f"  {len(rows)} wine_cellar rows")

        # --- wine_wishlist table ---
        print("Migrating wine_wishlist table...")
        sc.execute("SELECT * FROM wine_wishlist ORDER BY id")
        cols = [desc[0] for desc in sc.description]
        rows = sc.fetchall()
        for row in rows:
            d = dict(zip(cols, row))
            dc.execute("""
                INSERT INTO wine_wishlist (id, wine_id, wishlisted_at, notes, acquired)
                VALUES (%(id)s, %(wine_id)s, %(wishlisted_at)s, %(notes)s, %(acquired)s)
                ON CONFLICT DO NOTHING
            """, d)
        print(f"  {len(rows)} wine_wishlist rows")

        # Reset sequences
        for table in ("wine", "wine_log", "wine_cellar", "wine_wishlist"):
            dc.execute(f"SELECT setval('{table}_id_seq', COALESCE(max(id), 0) + 1, false) FROM {table}")

        dst.commit()
        print("\nMigration complete!")

        # Summary
        for table in ("wine", "wine_log", "wine_cellar", "wine_wishlist"):
            dc.execute(f"SELECT count(*) FROM {table}")
            print(f"  {table}: {dc.fetchone()[0]} rows")

    finally:
        src.close()
        dst.close()


if __name__ == "__main__":
    main()
