from typing import Dict, Iterable

from . import catalog
from .db import conn
from .matching import display_name, match_parts
from .scrapers import AUTOMATIC
from .scrapers.base import ScrapedItem

def remove_demo_catalog() -> int:
    ids = [r["product_id"] for r in conn.execute(
        "SELECT DISTINCT product_id FROM offers WHERE external_id LIKE 'demo-%'"
    ).fetchall()]
    if not ids:
        return 0
    with catalog.transaction():
        conn.executemany("DELETE FROM products WHERE id = ?", [(i,) for i in ids])
        conn.execute(
            "DELETE FROM stores WHERE code NOT IN (%s) AND NOT EXISTS "
            "(SELECT 1 FROM offers o WHERE o.store_id = stores.id)"
            % ",".join("?" * len(AUTOMATIC)),
            AUTOMATIC,
        )
    return len(ids)


def save_items(
    store_id: int, category: str, items: Iterable[ScrapedItem], now: str
) -> Dict[str, int]:
    stats = {"items": 0, "new_products": 0, "new_offers": 0, "price_changes": 0}
    for item in items:
        stats["items"] += 1
        existing = conn.execute(
            "SELECT product_id, price, in_stock FROM offers "
            "WHERE store_id = ? AND external_id = ?",
            (store_id, item.external_id),
        ).fetchone()

        if existing is not None:
            product_id = existing["product_id"]
            if round(existing["price"], 2) != round(item.price, 2):
                stats["price_changes"] += 1
        else:
            base, _, _ = match_parts(category, item.brand, item.title, item.details)
            row = conn.execute(
                "SELECT id FROM products WHERE match_key = ?", (base,)
            ).fetchone()
            if row is not None:
                product_id = row["id"]
            else:
                product_id = catalog.create_product(
                    display_name(item.title), item.brand, category
                )
                stats["new_products"] += 1
            stats["new_offers"] += 1

        catalog.upsert_offer(
            product_id, store_id, item.external_id, item.price,
            old_price=item.old_price, in_stock=item.in_stock,
            title=item.title, url=item.url, image_url=item.image_url,
            details=item.details, color=item.color, now=now,
        )
    return stats


def mark_missing(store_id: int, category: str, run_started: str) -> int:
    rows = conn.execute(
        "SELECT o.id FROM offers o JOIN products p ON p.id = o.product_id "
        "WHERE o.store_id = ? AND p.category = ? AND o.in_stock = 1 AND o.seen_at < ?",
        (store_id, category, run_started),
    ).fetchall()
    for r in rows:
        catalog.mark_out_of_stock(r["id"], run_started)
    return len(rows)
