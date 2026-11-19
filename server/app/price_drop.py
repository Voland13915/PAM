import math
import sys
from typing import Any, Dict, List

from .db import conn, now_iso


def watched() -> List[Any]:
    return conn.execute(
        "SELECT w.id, w.product_id, w.target_price, p.name FROM wishlist w "
        "JOIN products p ON p.id = w.product_id WHERE w.notify = 1 ORDER BY w.id"
    ).fetchall()


def cheapest(product_id: int) -> Any:
    return conn.execute(
        "SELECT o.id, o.price, s.name AS store FROM offers o "
        "JOIN stores s ON s.id = o.store_id "
        "WHERE o.product_id = ? AND o.in_stock = 1 ORDER BY o.price LIMIT 1",
        (product_id,),
    ).fetchone()


def set_price(offer_id: int, price: float, old_price: float) -> None:
    conn.execute(
        "UPDATE offers SET price = ?, old_price = ? WHERE id = ?",
        (price, old_price, offer_id),
    )
    conn.execute(
        "INSERT INTO price_snapshots (offer_id, price, in_stock, captured_at) "
        "VALUES (?, ?, 1, ?)",
        (offer_id, price, now_iso()),
    )


def drop_to_targets(percent: float = 1.0) -> List[Dict[str, Any]]:
    changed = []
    for item in watched():
        offer = cheapest(item["product_id"])
        if offer is None:
            continue
        price = math.floor(item["target_price"] * (1 - percent / 100))
        if offer["price"] <= price:
            continue
        set_price(offer["id"], price, offer["price"])
        changed.append({
            "product": item["name"],
            "store": offer["store"],
            "old": offer["price"],
            "new": price,
        })
    return changed


def main(argv: List[str]) -> None:
    percent = float(argv[0]) if argv else 1.0
    changed = drop_to_targets(percent)
    if not changed:
        print("Нечего снижать: нет отслеживаемых товаров дороже целевой цены")
        return
    for c in changed:
        print("%s — %s: %.0f → %.0f MDL" % (c["product"], c["store"], c["old"], c["new"]))
    print("\nНастоящие цены вернутся после следующего сбора (python -m app.scrape all)")


if __name__ == "__main__":
    main(sys.argv[1:])
