#!/usr/bin/env python3
"""Backfill wine_log.location from GPS coordinates using Nominatim reverse geocoding.

Rounds GPS to 0.01 degrees (~1km) for caching to minimize API calls.
Also cross-references against the mylocation gps_points table to find the
nearest known location by timestamp if the wine's own GPS is missing.

Usage:
    pip install geopy psycopg2-binary
    python3 scripts/backfill_locations.py [WINE_DSN] [MYLOCATION_DSN]
"""

import sys
import time

import psycopg2
from geopy.geocoders import Nominatim

WINE_DSN = sys.argv[1] if len(sys.argv) > 1 else "host=localhost port=5432 dbname=wine user=wine password=EyJbH-omXM3U3SDq1PyYkI_nfdCQLs-q sslmode=prefer"
MYLOCATION_DSN = sys.argv[2] if len(sys.argv) > 2 else "host=localhost port=5432 dbname=mylocation user=mcp_readonly sslmode=prefer"

geolocator = Nominatim(user_agent="wine-cellar-backfill", timeout=10)
geocode_cache: dict[str, str] = {}


def reverse_geocode(lat: float, lon: float) -> str | None:
    """Reverse geocode with rounding cache. Returns 'City, Country' or None."""
    key = f"{round(lat, 2)},{round(lon, 2)}"
    if key in geocode_cache:
        return geocode_cache[key]

    try:
        time.sleep(1.5)  # Nominatim rate limit
        result = geolocator.reverse(f"{lat}, {lon}", exactly_one=True, language="en")
        if result and result.raw.get("address"):
            addr = result.raw["address"]
            city = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("municipality") or addr.get("county", "")
            country = addr.get("country", "")
            location = f"{city}, {country}" if city else country
            geocode_cache[key] = location
            return location
    except Exception as e:
        print(f"  Geocode error for ({lat}, {lon}): {e}")

    return None


def main():
    wine_conn = psycopg2.connect(WINE_DSN)
    loc_conn = psycopg2.connect(MYLOCATION_DSN)
    wine_conn.autocommit = True

    wc = wine_conn.cursor()
    lc = loc_conn.cursor()

    # Step 1: Get all wine_log entries without a location
    wc.execute("""
        SELECT id, wine_id, logged_at, gps_lat, gps_lng
        FROM wine_log
        WHERE location IS NULL
        ORDER BY logged_at
    """)
    entries = wc.fetchall()
    print(f"Found {len(entries)} log entries without location")

    updated = 0
    gps_found = 0

    for log_id, wine_id, logged_at, gps_lat, gps_lng in entries:
        lat, lng = gps_lat, gps_lng

        # If no GPS on the wine log, try to find from mylocation gps_points
        if lat is None or lng is None:
            lc.execute("""
                SELECT lat, lon FROM gps_points
                WHERE ts BETWEEN %s - interval '2 hours' AND %s + interval '2 hours'
                ORDER BY ABS(EXTRACT(EPOCH FROM (ts - %s)))
                LIMIT 1
            """, (logged_at, logged_at, logged_at))
            row = lc.fetchone()
            if row:
                lat, lng = row[0], row[1]
                # Also save the GPS to the wine_log
                wc.execute("UPDATE wine_log SET gps_lat = %s, gps_lng = %s WHERE id = %s",
                           (lat, lng, log_id))
                gps_found += 1

        if lat is None or lng is None:
            continue

        location = reverse_geocode(lat, lng)
        if location:
            wc.execute("UPDATE wine_log SET location = %s WHERE id = %s", (location, log_id))
            updated += 1
            print(f"  [{updated}] {location}")

    print(f"\nDone: {updated} locations set, {gps_found} GPS coords from mylocation")
    wine_conn.close()
    loc_conn.close()


if __name__ == "__main__":
    main()
