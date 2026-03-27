from fastapi import APIRouter, Depends, HTTPException

from src.api.deps import CurrentUser, get_conn, get_current_user
from src.api.models import WishlistCreate, WishlistItem, WishlistUpdate

router = APIRouter()


def _row_to_item(row, cols):
    d = dict(zip(cols, row))
    return WishlistItem(
        id=d["id"],
        wine_id=d["wine_id"],
        wishlisted_at=str(d["wishlisted_at"]),
        notes=d.get("notes"),
        acquired=d["acquired"],
        wine_producer=d.get("wine_producer"),
        wine_name=d.get("wine_name"),
        wine_vintage=d.get("wine_vintage"),
        wine_type=d.get("wine_type"),
    )


@router.get("/wishlist", response_model=list[WishlistItem])
def list_wishlist(
    conn=Depends(get_conn),
    _user: CurrentUser = Depends(get_current_user),
):
    cur = conn.cursor()
    cur.execute("""
        SELECT ww.*, w.producer AS wine_producer, w.name AS wine_name,
               w.vintage AS wine_vintage, w.wine_type
        FROM wine_wishlist ww
        JOIN wine w ON w.id = ww.wine_id
        ORDER BY ww.acquired, ww.wishlisted_at DESC
    """)
    cols = [desc[0] for desc in cur.description]
    return [_row_to_item(r, cols) for r in cur.fetchall()]


@router.post("/wishlist", response_model=WishlistItem)
def add_to_wishlist(
    body: WishlistCreate,
    conn=Depends(get_conn),
    _user: CurrentUser = Depends(get_current_user),
):
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM wine WHERE id = %s", (body.wine_id,))
    if not cur.fetchone():
        raise HTTPException(404, "Wine not found")

    cur.execute("""
        INSERT INTO wine_wishlist (wine_id, notes)
        VALUES (%s, %s)
        ON CONFLICT (wine_id) DO NOTHING
        RETURNING id
    """, (body.wine_id, body.notes))
    row = cur.fetchone()
    if not row:
        raise HTTPException(409, "Wine already on wishlist")
    conn.commit()

    cur.execute("""
        SELECT ww.*, w.producer AS wine_producer, w.name AS wine_name,
               w.vintage AS wine_vintage, w.wine_type
        FROM wine_wishlist ww JOIN wine w ON w.id = ww.wine_id
        WHERE ww.id = %s
    """, (row[0],))
    cols = [desc[0] for desc in cur.description]
    return _row_to_item(cur.fetchone(), cols)


@router.put("/wishlist/{wishlist_id}", response_model=WishlistItem)
def update_wishlist(
    wishlist_id: int,
    body: WishlistUpdate,
    conn=Depends(get_conn),
    _user: CurrentUser = Depends(get_current_user),
):
    cur = conn.cursor()
    updates = []
    params: dict = {"wid": wishlist_id}

    if body.notes is not None:
        updates.append("notes = %(notes)s")
        params["notes"] = body.notes
    if body.acquired is not None:
        updates.append("acquired = %(acquired)s")
        params["acquired"] = body.acquired

    if not updates:
        raise HTTPException(400, "No fields to update")

    cur.execute(
        f"UPDATE wine_wishlist SET {', '.join(updates)} WHERE id = %(wid)s",
        params,
    )
    conn.commit()

    cur.execute("""
        SELECT ww.*, w.producer AS wine_producer, w.name AS wine_name,
               w.vintage AS wine_vintage, w.wine_type
        FROM wine_wishlist ww JOIN wine w ON w.id = ww.wine_id
        WHERE ww.id = %s
    """, (wishlist_id,))
    cols = [desc[0] for desc in cur.description]
    row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Wishlist entry not found")
    return _row_to_item(row, cols)


@router.delete("/wishlist/{wishlist_id}")
def delete_wishlist(
    wishlist_id: int,
    conn=Depends(get_conn),
    _user: CurrentUser = Depends(get_current_user),
):
    cur = conn.cursor()
    cur.execute("DELETE FROM wine_wishlist WHERE id = %s", (wishlist_id,))
    conn.commit()
    return {"ok": True}
