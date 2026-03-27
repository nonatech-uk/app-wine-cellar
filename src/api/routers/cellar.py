from fastapi import APIRouter, Depends, HTTPException

from src.api.deps import CurrentUser, get_conn, get_current_user
from src.api.models import CellarCreate, CellarItem, CellarUpdate

router = APIRouter()


def _row_to_item(row, cols):
    d = dict(zip(cols, row))
    return CellarItem(
        id=d["id"],
        wine_id=d["wine_id"],
        quantity=d["quantity"],
        storage_location=d.get("storage_location"),
        purchase_date=str(d["purchase_date"]) if d.get("purchase_date") else None,
        purchase_price=d.get("purchase_price"),
        purchase_currency=d.get("purchase_currency"),
        notes=d.get("notes"),
        updated_at=str(d["updated_at"]),
        wine_producer=d.get("wine_producer"),
        wine_name=d.get("wine_name"),
        wine_vintage=d.get("wine_vintage"),
        wine_type=d.get("wine_type"),
    )


@router.get("/cellar", response_model=list[CellarItem])
def list_cellar(
    conn=Depends(get_conn),
    _user: CurrentUser = Depends(get_current_user),
):
    cur = conn.cursor()
    cur.execute("""
        SELECT c.*, w.producer AS wine_producer, w.name AS wine_name,
               w.vintage AS wine_vintage, w.wine_type
        FROM wine_cellar c
        JOIN wine w ON w.id = c.wine_id
        WHERE c.quantity > 0
        ORDER BY c.storage_location NULLS LAST, w.producer, w.name
    """)
    cols = [desc[0] for desc in cur.description]
    return [_row_to_item(r, cols) for r in cur.fetchall()]


@router.post("/cellar", response_model=CellarItem)
def add_to_cellar(
    body: CellarCreate,
    conn=Depends(get_conn),
    _user: CurrentUser = Depends(get_current_user),
):
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM wine WHERE id = %s", (body.wine_id,))
    if not cur.fetchone():
        raise HTTPException(404, "Wine not found")

    cur.execute("""
        INSERT INTO wine_cellar (wine_id, quantity, storage_location, purchase_date,
                                 purchase_price, purchase_currency, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (wine_id, storage_location) DO UPDATE
            SET quantity = wine_cellar.quantity + EXCLUDED.quantity,
                updated_at = now()
        RETURNING id
    """, (body.wine_id, body.quantity, body.storage_location,
          body.purchase_date, body.purchase_price, body.purchase_currency, body.notes))
    cellar_id = cur.fetchone()[0]
    conn.commit()

    cur.execute("""
        SELECT c.*, w.producer AS wine_producer, w.name AS wine_name,
               w.vintage AS wine_vintage, w.wine_type
        FROM wine_cellar c JOIN wine w ON w.id = c.wine_id
        WHERE c.id = %s
    """, (cellar_id,))
    cols = [desc[0] for desc in cur.description]
    return _row_to_item(cur.fetchone(), cols)


@router.put("/cellar/{cellar_id}", response_model=CellarItem)
def update_cellar(
    cellar_id: int,
    body: CellarUpdate,
    conn=Depends(get_conn),
    _user: CurrentUser = Depends(get_current_user),
):
    cur = conn.cursor()
    updates = []
    params: dict = {"cellar_id": cellar_id}

    for field in ("quantity", "storage_location", "purchase_date", "purchase_price", "notes"):
        val = getattr(body, field, None)
        if val is not None:
            updates.append(f"{field} = %({field})s")
            params[field] = val

    if not updates:
        raise HTTPException(400, "No fields to update")

    updates.append("updated_at = now()")
    cur.execute(
        f"UPDATE wine_cellar SET {', '.join(updates)} WHERE id = %(cellar_id)s",
        params,
    )
    conn.commit()

    cur.execute("""
        SELECT c.*, w.producer AS wine_producer, w.name AS wine_name,
               w.vintage AS wine_vintage, w.wine_type
        FROM wine_cellar c JOIN wine w ON w.id = c.wine_id
        WHERE c.id = %s
    """, (cellar_id,))
    cols = [desc[0] for desc in cur.description]
    row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Cellar entry not found")
    return _row_to_item(row, cols)


@router.delete("/cellar/{cellar_id}")
def delete_cellar(
    cellar_id: int,
    conn=Depends(get_conn),
    _user: CurrentUser = Depends(get_current_user),
):
    cur = conn.cursor()
    cur.execute("DELETE FROM wine_cellar WHERE id = %s", (cellar_id,))
    conn.commit()
    return {"ok": True}
