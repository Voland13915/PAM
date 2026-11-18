import json
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, Iterator, List, Optional, Tuple

from .db import conn, now_iso

HISTORY_DAYS = 180
HISTORY_POINTS = 6


@contextmanager
def transaction() -> Iterator[None]:
    conn.execute("BEGIN")
    try:
        yield
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    conn.execute("COMMIT")


def get_or_create_store(code: str, name: str, website: str) -> int:
    row = conn.execute("SELECT id FROM stores WHERE code = ?", (code,)).fetchone()
    if row is not None:
        return row["id"]
    cursor = conn.execute(
        "INSERT INTO stores (code, name, website, created_at) VALUES (?, ?, ?, ?)",
        (code, name, website, now_iso()),
    )
    return cursor.lastrowid


def mark_store_synced(store_id: int, when: Optional[str] = None) -> None:
    conn.execute(
        "UPDATE stores SET last_sync = ? WHERE id = ?", (when or now_iso(), store_id)
    )


def store_to_json(row) -> Dict[str, Any]:
    tracked = conn.execute(
        "SELECT COUNT(*) AS n FROM offers WHERE store_id = ?", (row["id"],)
    ).fetchone()["n"]
    return {
        "id": row["id"],
        "name": row["name"],
        "website": row["website"],
        "productsTracked": tracked,
        "lastSync": row["last_sync"],
    }


def create_product(
    name: str,
    brand: str,
    category: str,
    specs: Optional[Dict[str, str]] = None,
    match_key: Optional[str] = None,
) -> int:
    cursor = conn.execute(
        "INSERT INTO products (name, brand, category, specs, match_key, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (name, brand, category, json.dumps(specs or {}, ensure_ascii=False),
         match_key, now_iso()),
    )
    return cursor.lastrowid


def update_product(product_id: int, name: str, brand: str, category: str,
                   specs: Dict[str, str]) -> None:
    conn.execute(
        "UPDATE products SET name = ?, brand = ?, category = ?, specs = ? WHERE id = ?",
        (name, brand, category, json.dumps(specs, ensure_ascii=False), product_id),
    )


def product_to_json(row) -> Dict[str, Any]:
    prices, dates = price_history(row["id"])
    return {
        "id": row["id"],
        "name": row["name"],
        "brand": row["brand"],
        "category": row["category"],
        "specs": json.loads(row["specs"]),
        "offers": offers_json(row["id"]),
        "priceHistory": prices,
        "priceHistoryDates": dates,
        "imageUrl": image_url(row["id"]),
        "createdAt": row["created_at"],
    }


def image_url(product_id: int) -> str:
    row = conn.execute(
        "SELECT image_url FROM offers WHERE product_id = ? AND image_url != '' "
        "ORDER BY in_stock DESC, price LIMIT 1",
        (product_id,),
    ).fetchone()
    return row["image_url"] if row is not None else ""


def _same_price(a: float, b: float) -> bool:
    return round(a, 2) == round(b, 2)


def upsert_offer(
    product_id: int,
    store_id: int,
    external_id: str,
    price: float,
    *,
    old_price: Optional[float] = None,
    in_stock: bool = True,
    title: str = "",
    url: str = "",
    image_url: str = "",
    details: str = "",
    now: Optional[str] = None,
) -> int:
    now = now or now_iso()
    stock = 1 if in_stock else 0
    row = conn.execute(
        "SELECT id, price, in_stock FROM offers WHERE store_id = ? AND external_id = ?",
        (store_id, external_id),
    ).fetchone()

    if row is None:
        offer_id = conn.execute(
            "INSERT INTO offers (product_id, store_id, external_id, title, url, price, "
            "old_price, in_stock, image_url, details, seen_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (product_id, store_id, external_id, title, url, price, old_price, stock,
             image_url, details, now),
        ).lastrowid
        changed = True
    else:
        offer_id = row["id"]
        changed = not _same_price(row["price"], price) or row["in_stock"] != stock
        conn.execute(
            "UPDATE offers SET product_id = ?, title = ?, url = ?, price = ?, "
            "old_price = ?, in_stock = ?, image_url = COALESCE(NULLIF(?, ''), image_url), "
            "details = COALESCE(NULLIF(?, ''), details), seen_at = ? WHERE id = ?",
            (product_id, title, url, price, old_price, stock, image_url, details, now,
             offer_id),
        )

    if changed:
        conn.execute(
            "INSERT INTO price_snapshots (offer_id, price, in_stock, captured_at) "
            "VALUES (?, ?, ?, ?)",
            (offer_id, price, stock, now),
        )
    return offer_id


def mark_out_of_stock(offer_id: int, now: Optional[str] = None) -> None:
    row = conn.execute(
        "SELECT price, in_stock FROM offers WHERE id = ?", (offer_id,)
    ).fetchone()
    if row is None or not row["in_stock"]:
        return
    conn.execute("UPDATE offers SET in_stock = 0 WHERE id = ?", (offer_id,))
    conn.execute(
        "INSERT INTO price_snapshots (offer_id, price, in_stock, captured_at) "
        "VALUES (?, ?, 0, ?)",
        (offer_id, row["price"], now or now_iso()),
    )


def offers_json(product_id: int) -> List[Dict[str, Any]]:
    rows = conn.execute(
        "SELECT store_id, price, old_price, in_stock, url FROM offers "
        "WHERE product_id = ? ORDER BY in_stock DESC, price",
        (product_id,),
    ).fetchall()
    best: Dict[int, Any] = {}
    for r in rows:
        best.setdefault(r["store_id"], r)
    return [
        {
            "storeId": r["store_id"],
            "price": r["price"],
            "oldPrice": r["old_price"],
            "inStock": bool(r["in_stock"]),
            "url": r["url"],
        }
        for r in sorted(best.values(), key=lambda r: (not r["in_stock"], r["price"]))
    ]


def _utc_today() -> date:
    return datetime.now(timezone.utc).date()


def price_history(
    product_id: int, today: Optional[date] = None
) -> Tuple[List[float], List[str]]:
    rows = conn.execute(
        "SELECT s.offer_id, s.price, s.in_stock, s.captured_at "
        "FROM price_snapshots s JOIN offers o ON o.id = s.offer_id "
        "WHERE o.product_id = ? ORDER BY s.captured_at, s.id",
        (product_id,),
    ).fetchall()
    if not rows:
        return [], []

    today = today or _utc_today()
    first = date.fromisoformat(rows[0]["captured_at"][:10])
    start = max(first, today - timedelta(days=HISTORY_DAYS - 1))

    state: Dict[int, Tuple[float, int]] = {}
    i = 0
    daily: List[Tuple[date, float]] = []
    day = start
    while day <= today:
        while i < len(rows) and date.fromisoformat(rows[i]["captured_at"][:10]) <= day:
            state[rows[i]["offer_id"]] = (rows[i]["price"], rows[i]["in_stock"])
            i += 1
        in_stock = [price for price, stock in state.values() if stock]
        if in_stock:
            daily.append((day, min(in_stock)))
        day += timedelta(days=1)

    points: List[Tuple[date, float]] = []
    for day, price in daily:
        if not points or not _same_price(points[-1][1], price):
            points.append((day, price))
    if daily and points[-1][0] != daily[-1][0]:
        points.append(daily[-1])

    points = points[-HISTORY_POINTS:]
    return [p for _, p in points], [d.isoformat() for d, _ in points]
