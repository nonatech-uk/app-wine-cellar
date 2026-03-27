from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.deps import CurrentUser, get_conn, get_current_user
from src.api.models import LogCreate, LogEntry, LogUpdate

router = APIRouter()


def _row_to_entry(row, cols):
    d = dict(zip(cols, row))
    return LogEntry(
        id=d["id"],
        wine_id=d["wine_id"],
        logged_at=str(d["logged_at"]),
        source=d["source"],
        rating=d.get("rating"),
        review=d.get("review"),
        personal_note=d.get("personal_note"),
        location=d.get("location"),
        gps_lat=d.get("gps_lat"),
        gps_lng=d.get("gps_lng"),
        label_image_filename=d.get("label_image_filename"),
        pipeline_item_id=d.get("pipeline_item_id"),
        wine_producer=d.get("wine_producer"),
        wine_name=d.get("wine_name"),
        wine_vintage=d.get("wine_vintage"),
    )


@router.get("/wines/{wine_id}/log", response_model=list[LogEntry])
def get_wine_log(
    wine_id: int,
    conn=Depends(get_conn),
    _user: CurrentUser = Depends(get_current_user),
):
    cur = conn.cursor()
    cur.execute("""
        SELECT wl.*, w.producer AS wine_producer, w.name AS wine_name, w.vintage AS wine_vintage
        FROM wine_log wl
        JOIN wine w ON w.id = wl.wine_id
        WHERE wl.wine_id = %s
        ORDER BY wl.logged_at DESC
    """, (wine_id,))
    cols = [desc[0] for desc in cur.description]
    return [_row_to_entry(r, cols) for r in cur.fetchall()]


@router.post("/wines/{wine_id}/log", response_model=LogEntry)
def add_log_entry(
    wine_id: int,
    body: LogCreate,
    conn=Depends(get_conn),
    _user: CurrentUser = Depends(get_current_user),
):
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM wine WHERE id = %s", (wine_id,))
    if not cur.fetchone():
        raise HTTPException(404, "Wine not found")

    cur.execute("""
        INSERT INTO wine_log (wine_id, logged_at, source, rating, review, personal_note, location)
        VALUES (%s, %s, 'manual', %s, %s, %s, %s)
        RETURNING id
    """, (wine_id, datetime.now(timezone.utc), body.rating, body.review,
          body.personal_note, body.location))
    log_id = cur.fetchone()[0]
    conn.commit()

    cur.execute("""
        SELECT wl.*, w.producer AS wine_producer, w.name AS wine_name, w.vintage AS wine_vintage
        FROM wine_log wl JOIN wine w ON w.id = wl.wine_id
        WHERE wl.id = %s
    """, (log_id,))
    cols = [desc[0] for desc in cur.description]
    return _row_to_entry(cur.fetchone(), cols)


@router.put("/log/{log_id}", response_model=LogEntry)
def update_log_entry(
    log_id: int,
    body: LogUpdate,
    conn=Depends(get_conn),
    _user: CurrentUser = Depends(get_current_user),
):
    cur = conn.cursor()
    updates = []
    params: dict = {"log_id": log_id}

    for field in ("rating", "review", "personal_note", "location"):
        val = getattr(body, field, None)
        if val is not None:
            updates.append(f"{field} = %({field})s")
            params[field] = val

    if not updates:
        raise HTTPException(400, "No fields to update")

    cur.execute(
        f"UPDATE wine_log SET {', '.join(updates)} WHERE id = %(log_id)s",
        params,
    )
    conn.commit()

    cur.execute("""
        SELECT wl.*, w.producer AS wine_producer, w.name AS wine_name, w.vintage AS wine_vintage
        FROM wine_log wl JOIN wine w ON w.id = wl.wine_id
        WHERE wl.id = %s
    """, (log_id,))
    cols = [desc[0] for desc in cur.description]
    row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Log entry not found")
    return _row_to_entry(row, cols)


@router.delete("/log/{log_id}")
def delete_log_entry(
    log_id: int,
    conn=Depends(get_conn),
    _user: CurrentUser = Depends(get_current_user),
):
    cur = conn.cursor()
    cur.execute("DELETE FROM wine_log WHERE id = %s", (log_id,))
    conn.commit()
    return {"ok": True}


@router.get("/log/recent", response_model=list[LogEntry])
def recent_log(
    limit: int = Query(20, le=100),
    conn=Depends(get_conn),
    _user: CurrentUser = Depends(get_current_user),
):
    cur = conn.cursor()
    cur.execute("""
        SELECT wl.*, w.producer AS wine_producer, w.name AS wine_name, w.vintage AS wine_vintage
        FROM wine_log wl
        JOIN wine w ON w.id = wl.wine_id
        ORDER BY wl.logged_at DESC
        LIMIT %s
    """, (limit,))
    cols = [desc[0] for desc in cur.description]
    return [_row_to_entry(r, cols) for r in cur.fetchall()]
