import argparse
import csv
import sys
from pathlib import Path

from .db import conn

COLUMNS = [
    "store", "category", "external_id", "product_id", "match_key", "brand",
    "title", "details", "price", "old_price", "in_stock", "url",
]


def export(path: Path) -> int:
    rows = conn.execute(
        "SELECT s.code AS store, p.category, o.external_id, o.product_id, p.match_key, "
        "p.brand, o.title, o.details, o.price, o.old_price, o.in_stock, o.url "
        "FROM offers o JOIN products p ON p.id = o.product_id "
        "JOIN stores s ON s.id = o.store_id "
        "WHERE o.external_id NOT LIKE 'demo-%' AND o.external_id NOT LIKE 'manual-%' "
        "ORDER BY s.code, p.category, o.title"
    ).fetchall()
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(COLUMNS)
        for row in rows:
            writer.writerow([row[c] for c in COLUMNS])
    return len(rows)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.export_offers")
    parser.add_argument("out", type=Path, nargs="?", default=Path("offers.csv"))
    args = parser.parse_args(argv)
    count = export(args.out)
    print("Выгружено предложений: %d -> %s" % (count, args.out.resolve()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
