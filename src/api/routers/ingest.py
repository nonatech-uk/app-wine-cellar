"""Pipeline ingest endpoint — receives wine labels from the pipeline."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from config.settings import settings
from src.api.deps import get_conn
from src.api.models import IngestResult

log = logging.getLogger(__name__)
router = APIRouter()


@router.post("/ingest", response_model=IngestResult)
def ingest(
    request: Request,
    metadata: str = Form(...),
    label: UploadFile | None = File(None),
):
    # Validate pipeline secret
    secret = request.headers.get("X-Pipeline-Secret", "")
    if not settings.pipeline_secret or secret != settings.pipeline_secret:
        raise HTTPException(403, "Invalid pipeline secret")

    data = json.loads(metadata)
    producer = data.get("producer", "").strip()
    wine_name = data.get("wine_name", "").strip()
    if not producer or not wine_name:
        raise HTTPException(400, "Missing producer or wine_name")

    vintage = None
    if data.get("vintage"):
        try:
            vintage = int(str(data["vintage"]).strip())
        except ValueError:
            pass

    abv = None
    if data.get("abv"):
        try:
            abv = float(str(data["abv"]).strip().rstrip("%"))
        except ValueError:
            pass

    # Save label image
    label_filename = None
    if label and label.filename:
        label_dir = Path(settings.label_storage_path)
        label_dir.mkdir(parents=True, exist_ok=True)
        label_filename = label.filename
        (label_dir / label_filename).write_bytes(label.file.read())

    # Get a connection from the pool
    conn_gen = get_conn()
    conn = next(conn_gen)
    try:
        cur = conn.cursor()

        # Upsert wine
        cur.execute("""
            INSERT INTO wine (producer, name, vintage, region, country, grape_variety, abv)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (producer, name, COALESCE(vintage, 0)) DO UPDATE
                SET region = COALESCE(wine.region, EXCLUDED.region),
                    country = COALESCE(wine.country, EXCLUDED.country),
                    grape_variety = COALESCE(wine.grape_variety, EXCLUDED.grape_variety),
                    abv = COALESCE(wine.abv, EXCLUDED.abv),
                    updated_at = now()
            RETURNING id
        """, (producer, wine_name, vintage,
              data.get("region"), data.get("country"),
              data.get("grape_variety"), abv))
        wine_id = cur.fetchone()[0]

        # Create log entry
        logged_at = datetime.now(timezone.utc)
        if data.get("logged_at"):
            try:
                logged_at = datetime.fromisoformat(data["logged_at"])
            except ValueError:
                pass

        cur.execute("""
            INSERT INTO wine_log (wine_id, logged_at, source, gps_lat, gps_lng,
                                  label_image_filename, pipeline_item_id)
            VALUES (%s, %s, 'pipeline', %s, %s, %s, %s)
            RETURNING id
        """, (wine_id, logged_at, data.get("gps_lat"), data.get("gps_lng"),
              label_filename, data.get("pipeline_item_id")))
        log_id = cur.fetchone()[0]
        conn.commit()

        log.info("Ingested wine: %s %s (id=%d, log=%d)", producer, wine_name, wine_id, log_id)
        return IngestResult(wine_id=wine_id, log_id=log_id)
    finally:
        try:
            next(conn_gen, None)
        except StopIteration:
            pass
