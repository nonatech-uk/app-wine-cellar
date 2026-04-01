#!/usr/bin/env python3
"""Import Vivino CSV exports into the wine database.

Processes full_wine_list.csv, cellar.csv, wishlisted.csv, label_scans.csv,
and optionally user_prices.csv from one or more Vivino data export directories.

Usage:
    python3 scripts/import_vivino.py /path/to/vivino_data [/path/to/vivino_data-2 ...]
    python3 scripts/import_vivino.py --dry-run /path/to/vivino_data
"""

import argparse
import csv
import hashlib
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

import psycopg2

WINE_DSN = "host=192.168.128.9 port=5432 dbname=wine user=wine password=EyJbH-omXM3U3SDq1PyYkI_nfdCQLs-q sslmode=prefer"
LABEL_DIR = Path("/zfs/Apps/AppData/wine/labels")

COUNTRY_MAP = {
    "fr": "France",
    "gb": "United Kingdom",
    "uk": "United Kingdom",
    "us": "United States",
    "it": "Italy",
    "es": "Spain",
    "de": "Germany",
    "pt": "Portugal",
    "au": "Australia",
    "ar": "Argentina",
    "cl": "Chile",
    "za": "South Africa",
    "at": "Austria",
    "ch": "Switzerland",
    "nz": "New Zealand",
}


def normalise_country(c: str) -> str | None:
    if not c:
        return None
    return COUNTRY_MAP.get(c.strip().lower(), c.strip())


def parse_vintage(v: str) -> int | None:
    v = v.strip()
    if not v:
        return None
    try:
        return int(v)
    except ValueError:
        return None


def parse_float(v: str) -> float | None:
    v = v.strip()
    if not v:
        return None
    try:
        return float(v)
    except ValueError:
        return None


def parse_datetime(v: str) -> datetime | None:
    v = v.strip()
    if not v:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            return datetime.strptime(v, fmt)
        except ValueError:
            continue
    return None


def load_label_scans(data_dir: Path) -> dict[str, tuple[float | None, float | None]]:
    """Load GPS coords from label_scans.csv, keyed by label image URL."""
    scans_file = data_dir / "label_scans.csv"
    if not scans_file.exists():
        return {}
    gps = {}
    with open(scans_file, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            url = row.get("Label Photo", "").strip()
            loc = row.get("Client Location", "").strip()
            if url and loc and "," in loc:
                parts = loc.split(",", 1)
                try:
                    lat, lng = float(parts[0]), float(parts[1])
                    gps[url] = (lat, lng)
                except ValueError:
                    pass
    return gps


def load_user_prices(data_dir: Path) -> dict[tuple[str, str, int | None], float]:
    """Load purchase prices from user_prices.csv, keyed by (producer, name, vintage)."""
    prices_file = data_dir / "user_prices.csv"
    if not prices_file.exists():
        return {}
    prices = {}
    with open(prices_file, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            producer = row.get("Winery", "").strip()
            name = row.get("Wine name", "").strip()
            vintage = parse_vintage(row.get("Vintage", ""))
            price_str = row.get("Wine price", "").strip()
            if producer and name and price_str:
                # Format: "GBP 137.4" — extract numeric part
                parts = price_str.split()
                if len(parts) >= 2:
                    try:
                        prices[(producer, name, vintage)] = float(parts[1])
                    except ValueError:
                        pass
    return prices


def download_image(url: str, wine_id: int) -> str | None:
    """Download a Vivino label image, return filename or None."""
    if not url:
        return None
    url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
    filename = f"vivino-{wine_id}-{url_hash}.jpg"
    dest = LABEL_DIR / filename
    if dest.exists():
        return filename
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
            if len(data) < 100:
                return None
            dest.write_bytes(data)
        return filename
    except Exception as e:
        print(f"  WARNING: Failed to download {url}: {e}", file=sys.stderr)
        return None


def process_export(cur, data_dir: Path, existing_timestamps: set, dry_run: bool):
    """Process a single Vivino export directory."""
    stats = {
        "wines_created": 0,
        "wines_updated": 0,
        "logs_added": 0,
        "logs_skipped": 0,
        "cellar_added": 0,
        "wishlist_added": 0,
        "images_downloaded": 0,
        "blank_skipped": 0,
    }

    gps_map = load_label_scans(data_dir)
    prices_map = load_user_prices(data_dir)

    # --- full_wine_list.csv ---
    wine_list = data_dir / "full_wine_list.csv"
    if wine_list.exists():
        with open(wine_list, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                producer = row.get("Winery", "").strip()
                name = row.get("Wine name", "").strip()

                if not producer and not name:
                    stats["blank_skipped"] += 1
                    continue

                vintage = parse_vintage(row.get("Vintage", ""))
                scan_date = parse_datetime(row.get("Scan date", ""))

                # Deduplicate by timestamp
                if scan_date:
                    ts_key = scan_date.strftime("%Y-%m-%d %H:%M:%S")
                    if ts_key in existing_timestamps:
                        stats["logs_skipped"] += 1
                        continue
                    existing_timestamps.add(ts_key)

                region = row.get("Region", "").strip() or None
                country = normalise_country(row.get("Country", ""))
                wine_type = row.get("Wine type", "").strip() or None
                style = row.get("Regional wine style", "").strip() or None
                avg_rating = parse_float(row.get("Average rating", ""))
                vivino_url = row.get("Link to wine", "").strip() or None
                drinking_window = row.get("Drinking Window", "").strip() or None
                user_rating = parse_float(row.get("Your rating", ""))
                review = row.get("Your review", "").strip() or None
                personal_note = row.get("Personal Note", "").strip() or None
                label_url = row.get("Label image", "").strip() or None

                # GPS from label_scans
                gps_lat, gps_lng = None, None
                if label_url and label_url in gps_map:
                    gps_lat, gps_lng = gps_map[label_url]

                if dry_run:
                    print(f"  WINE: {producer} - {name} ({vintage or 'NV'}) [{wine_type}]")
                    if scan_date:
                        print(f"    LOG: {scan_date} rating={user_rating} gps={gps_lat},{gps_lng}")
                    stats["logs_added"] += 1
                    continue

                # Upsert wine
                cur.execute("""
                    INSERT INTO wine (producer, name, vintage, region, country, wine_type,
                                      style, vivino_url, vivino_avg_rating, drinking_window)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (producer, name, COALESCE(vintage, 0)) DO UPDATE
                        SET region = COALESCE(wine.region, EXCLUDED.region),
                            country = COALESCE(wine.country, EXCLUDED.country),
                            wine_type = COALESCE(wine.wine_type, EXCLUDED.wine_type),
                            style = COALESCE(wine.style, EXCLUDED.style),
                            vivino_url = COALESCE(wine.vivino_url, EXCLUDED.vivino_url),
                            vivino_avg_rating = COALESCE(EXCLUDED.vivino_avg_rating, wine.vivino_avg_rating),
                            drinking_window = COALESCE(wine.drinking_window, EXCLUDED.drinking_window),
                            updated_at = now()
                    RETURNING id, (xmax = 0) AS inserted
                """, (producer, name, vintage, region, country, wine_type,
                      style, vivino_url, avg_rating, drinking_window))
                wine_id, was_inserted = cur.fetchone()
                if was_inserted:
                    stats["wines_created"] += 1
                else:
                    stats["wines_updated"] += 1

                # Download label image
                label_filename = download_image(label_url, wine_id)
                if label_filename:
                    stats["images_downloaded"] += 1

                # Create wine_log entry (use now() if no scan date)
                cur.execute("""
                    INSERT INTO wine_log (wine_id, logged_at, source, rating, review,
                                          personal_note, gps_lat, gps_lng, label_image_filename)
                    VALUES (%s, COALESCE(%s, now()), 'vivino', %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (wine_id, scan_date, user_rating, review, personal_note,
                      gps_lat, gps_lng, label_filename))
                stats["logs_added"] += 1

    # --- cellar.csv ---
    cellar_file = data_dir / "cellar.csv"
    if cellar_file.exists():
        with open(cellar_file, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                producer = row.get("Winery", "").strip()
                name = row.get("Wine name", "").strip()
                if not producer and not name:
                    continue

                vintage = parse_vintage(row.get("Vintage", ""))
                quantity = int(row.get("User cellar count", "0") or "0")
                country = normalise_country(row.get("Country", ""))
                region = row.get("Region", "").strip() or None
                wine_type = row.get("Wine type", "").strip() or None
                style = row.get("Regional wine style", "").strip() or None
                avg_rating = parse_float(row.get("Average rating", ""))
                vivino_url = row.get("Link to wine", "").strip() or None

                if dry_run:
                    print(f"  CELLAR: {producer} - {name} ({vintage or 'NV'}) x{quantity}")
                    continue

                # Upsert wine first
                cur.execute("""
                    INSERT INTO wine (producer, name, vintage, region, country, wine_type,
                                      style, vivino_url, vivino_avg_rating)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (producer, name, COALESCE(vintage, 0)) DO UPDATE
                        SET region = COALESCE(wine.region, EXCLUDED.region),
                            country = COALESCE(wine.country, EXCLUDED.country),
                            wine_type = COALESCE(wine.wine_type, EXCLUDED.wine_type),
                            style = COALESCE(wine.style, EXCLUDED.style),
                            vivino_url = COALESCE(wine.vivino_url, EXCLUDED.vivino_url),
                            vivino_avg_rating = COALESCE(EXCLUDED.vivino_avg_rating, wine.vivino_avg_rating),
                            updated_at = now()
                    RETURNING id
                """, (producer, name, vintage, region, country, wine_type,
                      style, vivino_url, avg_rating))
                wine_id = cur.fetchone()[0]

                # Look up purchase price if available
                price = prices_map.get((producer, name, vintage))

                # Upsert cellar entry (no storage_location from Vivino)
                cur.execute("""
                    INSERT INTO wine_cellar (wine_id, quantity, storage_location, purchase_price)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (wine_id, storage_location) DO UPDATE
                        SET quantity = EXCLUDED.quantity,
                            purchase_price = COALESCE(EXCLUDED.purchase_price, wine_cellar.purchase_price),
                            updated_at = now()
                """, (wine_id, quantity, None, price))
                stats["cellar_added"] += 1

    # --- wishlisted.csv ---
    wishlist_file = data_dir / "wishlisted.csv"
    if wishlist_file.exists():
        with open(wishlist_file, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                producer = row.get("Winery", "").strip()
                name = row.get("Wine name", "").strip()
                if not producer and not name:
                    continue

                vintage = parse_vintage(row.get("Vintage", ""))
                country = normalise_country(row.get("Country", ""))
                region = row.get("Region", "").strip() or None
                wine_type = row.get("Wine type", "").strip() or None
                vivino_url = row.get("Link to wine", "").strip() or None

                if dry_run:
                    print(f"  WISHLIST: {producer} - {name} ({vintage or 'NV'})")
                    continue

                # Upsert wine
                cur.execute("""
                    INSERT INTO wine (producer, name, vintage, region, country, wine_type,
                                      vivino_url)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (producer, name, COALESCE(vintage, 0)) DO UPDATE
                        SET region = COALESCE(wine.region, EXCLUDED.region),
                            country = COALESCE(wine.country, EXCLUDED.country),
                            wine_type = COALESCE(wine.wine_type, EXCLUDED.wine_type),
                            vivino_url = COALESCE(wine.vivino_url, EXCLUDED.vivino_url),
                            updated_at = now()
                    RETURNING id
                """, (producer, name, vintage, region, country, wine_type, vivino_url))
                wine_id = cur.fetchone()[0]

                cur.execute("""
                    INSERT INTO wine_wishlist (wine_id)
                    VALUES (%s)
                    ON CONFLICT (wine_id) DO NOTHING
                """, (wine_id,))
                if cur.rowcount > 0:
                    stats["wishlist_added"] += 1

    return stats


def main():
    parser = argparse.ArgumentParser(description="Import Vivino CSV exports into wine DB")
    parser.add_argument("data_dirs", nargs="+", type=Path, help="Vivino export directories")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be imported without writing")
    parser.add_argument("--dsn", default=WINE_DSN, help="PostgreSQL DSN")
    args = parser.parse_args()

    conn = psycopg2.connect(args.dsn)
    conn.autocommit = False

    try:
        cur = conn.cursor()

        # Load existing wine_log timestamps for dedup
        cur.execute("SELECT to_char(logged_at, 'YYYY-MM-DD HH24:MI:SS') FROM wine_log")
        existing_timestamps = {r[0] for r in cur.fetchall()}
        print(f"Existing wine_log entries: {len(existing_timestamps)}")

        LABEL_DIR.mkdir(parents=True, exist_ok=True)

        for data_dir in args.data_dirs:
            data_dir = data_dir.resolve()
            if not data_dir.is_dir():
                print(f"ERROR: {data_dir} is not a directory", file=sys.stderr)
                continue

            # Identify owner from user_profile.csv
            profile = data_dir / "user_profile.csv"
            owner = data_dir.name
            if profile.exists():
                with open(profile, newline="", encoding="utf-8") as f:
                    for row in csv.DictReader(f):
                        first = row.get("First Name", "").strip()
                        last = row.get("Last Name", "").strip()
                        if first:
                            owner = f"{first} {last}".strip()
                        break

            print(f"\n{'=' * 60}")
            print(f"Processing: {data_dir} (owner: {owner})")
            print(f"{'=' * 60}")

            stats = process_export(cur, data_dir, existing_timestamps, args.dry_run)

            print(f"\n  Results for {owner}:")
            for k, v in stats.items():
                print(f"    {k}: {v}")

        if args.dry_run:
            print("\nDRY RUN — no changes committed")
            conn.rollback()
        else:
            conn.commit()
            print("\nAll changes committed.")

            # Print final counts
            cur.execute("SELECT count(*) FROM wine")
            print(f"  Total wines: {cur.fetchone()[0]}")
            cur.execute("SELECT count(*) FROM wine_log")
            print(f"  Total wine_log: {cur.fetchone()[0]}")
            cur.execute("SELECT count(*) FROM wine_cellar")
            print(f"  Total cellar: {cur.fetchone()[0]}")
            cur.execute("SELECT count(*) FROM wine_wishlist")
            print(f"  Total wishlist: {cur.fetchone()[0]}")

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
