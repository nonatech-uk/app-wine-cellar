from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.deps import CurrentUser, get_conn, get_current_user
from src.api.models import WineDetail, WineItem, WineList, WineUpdate

router = APIRouter()


def _row_to_item(row, cols):
    d = dict(zip(cols, row))
    return WineItem(
        id=d["id"],
        producer=d["producer"],
        name=d["name"],
        vintage=d.get("vintage"),
        region=d.get("region"),
        country=d.get("country"),
        wine_type=d.get("wine_type"),
        style=d.get("style"),
        grape_variety=d.get("grape_variety"),
        abv=d.get("abv"),
        vivino_avg_rating=d.get("vivino_avg_rating"),
        avg_personal_rating=d.get("avg_personal_rating"),
        last_tasted=str(d["last_tasted"]) if d.get("last_tasted") else None,
        tasting_count=d.get("tasting_count", 0),
    )


@router.get("/wines", response_model=WineList)
def list_wines(
    q: str | None = Query(None),
    country: str | None = Query(None),
    wine_type: str | None = Query(None),
    sort: str = Query("name"),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    conn=Depends(get_conn),
    _user: CurrentUser = Depends(get_current_user),
):
    cur = conn.cursor()
    conditions = []
    params: dict = {}

    if q:
        conditions.append("(w.producer ILIKE %(q)s OR w.name ILIKE %(q)s)")
        params["q"] = f"%{q}%"
    if country:
        conditions.append("w.country = %(country)s")
        params["country"] = country
    if wine_type:
        conditions.append("w.wine_type = %(wine_type)s")
        params["wine_type"] = wine_type

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    sort_map = {
        "name": "w.producer, w.name",
        "rating": "avg_personal_rating DESC NULLS LAST, w.producer",
        "recent": "last_tasted DESC NULLS LAST, w.producer",
        "country": "w.country, w.producer, w.name",
    }
    order = sort_map.get(sort, "w.producer, w.name")

    # Count
    cur.execute(f"SELECT count(*) FROM wine w {where}", params)
    total = cur.fetchone()[0]

    # Fetch with aggregates
    cur.execute(f"""
        SELECT w.*, avg(wl.rating) AS avg_personal_rating,
               max(wl.logged_at) AS last_tasted,
               count(wl.id) AS tasting_count
        FROM wine w
        LEFT JOIN wine_log wl ON wl.wine_id = w.id
        {where}
        GROUP BY w.id
        ORDER BY {order}
        LIMIT %(limit)s OFFSET %(offset)s
    """, {**params, "limit": limit + 1, "offset": offset})

    cols = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    has_more = len(rows) > limit
    items = [_row_to_item(r, cols) for r in rows[:limit]]

    return WineList(items=items, total=total, has_more=has_more)


@router.get("/wines/{wine_id}", response_model=WineDetail)
def get_wine(
    wine_id: int,
    conn=Depends(get_conn),
    _user: CurrentUser = Depends(get_current_user),
):
    cur = conn.cursor()
    cur.execute("""
        SELECT w.*,
               avg(wl.rating) AS avg_personal_rating,
               max(wl.logged_at) AS last_tasted,
               count(wl.id) AS tasting_count
        FROM wine w
        LEFT JOIN wine_log wl ON wl.wine_id = w.id
        WHERE w.id = %s
        GROUP BY w.id
    """, (wine_id,))
    cols = [desc[0] for desc in cur.description]
    row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Wine not found")

    d = dict(zip(cols, row))

    # Cellar status
    cur.execute("""
        SELECT COALESCE(sum(quantity), 0), string_agg(storage_location, ', ')
        FROM wine_cellar WHERE wine_id = %s AND quantity > 0
    """, (wine_id,))
    cellar_row = cur.fetchone()

    # Wishlist status
    cur.execute("SELECT 1 FROM wine_wishlist WHERE wine_id = %s AND NOT acquired", (wine_id,))
    is_wishlisted = cur.fetchone() is not None

    return WineDetail(
        id=d["id"],
        producer=d["producer"],
        name=d["name"],
        vintage=d.get("vintage"),
        region=d.get("region"),
        country=d.get("country"),
        wine_type=d.get("wine_type"),
        style=d.get("style"),
        grape_variety=d.get("grape_variety"),
        abv=d.get("abv"),
        vivino_url=d.get("vivino_url"),
        vivino_avg_rating=d.get("vivino_avg_rating"),
        vivino_ratings_count=d.get("vivino_ratings_count"),
        drinking_window=d.get("drinking_window"),
        created_at=str(d["created_at"]),
        updated_at=str(d["updated_at"]),
        avg_personal_rating=d.get("avg_personal_rating"),
        last_tasted=str(d["last_tasted"]) if d.get("last_tasted") else None,
        tasting_count=d.get("tasting_count", 0),
        cellar_quantity=cellar_row[0] if cellar_row else 0,
        cellar_location=cellar_row[1] if cellar_row else None,
        is_wishlisted=is_wishlisted,
    )


@router.put("/wines/{wine_id}", response_model=WineDetail)
def update_wine(
    wine_id: int,
    body: WineUpdate,
    conn=Depends(get_conn),
    _user: CurrentUser = Depends(get_current_user),
):
    cur = conn.cursor()
    updates = []
    params: dict = {"wine_id": wine_id}

    for field in ("producer", "name", "vintage", "region", "country", "wine_type",
                  "style", "grape_variety", "abv", "drinking_window"):
        val = getattr(body, field, None)
        if val is not None:
            updates.append(f"{field} = %({field})s")
            params[field] = val

    if not updates:
        raise HTTPException(400, "No fields to update")

    updates.append("updated_at = now()")
    cur.execute(
        f"UPDATE wine SET {', '.join(updates)} WHERE id = %(wine_id)s",
        params,
    )
    conn.commit()

    return get_wine(wine_id, conn, _user)
