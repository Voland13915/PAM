import argparse
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

from . import catalog
from .db import conn
from .matching import display_name, match_parts, trimmed_keys


def rematch() -> Dict[str, int]:
    offers = conn.execute(
        "SELECT o.id, o.product_id, o.title, p.category, p.brand "
        "FROM offers o JOIN products p ON p.id = o.product_id "
        "WHERE o.external_id NOT LIKE 'manual-%' AND o.external_id NOT LIKE 'demo-%' "
        "AND o.title != '' ORDER BY o.id"
    ).fetchall()

    parts = [(o,) + match_parts(o["category"], o["brand"], o["title"]) for o in offers]
    bases = {base for _, base, _, _ in parts}
    alias: Dict[str, str] = {}
    for base in bases:
        alias[base] = next((t for t in trimmed_keys(base) if t in bases), base)

    def resolve(key: str) -> str:
        while alias.get(key, key) != key:
            key = alias[key]
        return key

    by_base: Dict[str, List] = defaultdict(list)
    for offer, base, full, ram in parts:
        root = resolve(base)
        if root != base:
            pieces = full.split("|")
            pieces[1] = root.split("|")[1]
            full = "|".join(pieces)
        by_base[root].append((offer, full, ram))

    groups: Dict[str, List] = defaultdict(list)
    for base, members in by_base.items():
        rams = {ram for _, _, ram in members if ram is not None}
        for offer, full, ram in members:
            groups[base if len(rams) <= 1 else full].append(offer)

    old_keys = {
        r["match_key"]: r["id"]
        for r in conn.execute("SELECT id, match_key FROM products WHERE match_key IS NOT NULL")
    }
    affected = {o["product_id"] for o in offers}

    stats = {"offers": len(offers), "products": len(groups), "moved": 0, "removed": 0}
    with catalog.transaction():
        conn.executemany(
            "UPDATE products SET match_key = NULL WHERE id = ?", [(p,) for p in affected]
        )
        used = set()
        redirect: Dict[int, int] = {}
        for key, group in sorted(groups.items(), key=lambda kv: min(o["id"] for o in kv[1])):
            candidates = [old_keys.get(key)] + sorted({o["product_id"] for o in group})
            target = next((p for p in candidates if p in affected and p not in used), None)
            first = group[0]
            if target is None:
                target = catalog.create_product(
                    display_name(first["title"]), first["brand"], first["category"]
                )
            used.add(target)
            conn.execute(
                "UPDATE products SET match_key = ?, name = ? WHERE id = ?",
                (key, display_name(first["title"]), target),
            )
            for offer in group:
                if offer["product_id"] != target:
                    conn.execute(
                        "UPDATE offers SET product_id = ? WHERE id = ?", (target, offer["id"])
                    )
                    redirect.setdefault(offer["product_id"], target)
                    stats["moved"] += 1

        for old, new in redirect.items():
            conn.execute("UPDATE wishlist SET product_id = ? WHERE product_id = ?", (new, old))
        empty = [r["id"] for r in conn.execute(
            "SELECT id FROM products p WHERE NOT EXISTS "
            "(SELECT 1 FROM offers o WHERE o.product_id = p.id)"
        )]
        conn.executemany("DELETE FROM products WHERE id = ?", [(p,) for p in empty])
        stats["removed"] = len(empty)
    return stats


def report(path: Path) -> Dict[str, int]:
    rows = conn.execute(
        "SELECT p.id, p.category, p.match_key, s.name AS store, o.title, o.price "
        "FROM offers o JOIN products p ON p.id = o.product_id JOIN stores s ON s.id = o.store_id "
        "ORDER BY p.category, p.match_key, s.name"
    ).fetchall()
    by_product: Dict[int, List] = defaultdict(list)
    for r in rows:
        by_product[r["id"]].append(r)

    matched = [g for g in by_product.values() if len({r["store"] for r in g}) > 1]
    single = [g for g in by_product.values() if len({r["store"] for r in g}) == 1]

    lines = ["СОПОСТАВЛЕНЫ (%d товаров есть в нескольких магазинах)" % len(matched), ""]
    for group in matched:
        lines.append(group[0]["match_key"])
        for r in group:
            lines.append("    %-8s %8.0f  %s" % (r["store"], r["price"], r["title"]))
    lines += ["", "ТОЛЬКО В ОДНОМ МАГАЗИНЕ (%d)" % len(single), ""]
    for group in sorted(single, key=lambda g: (g[0]["category"], g[0]["store"], g[0]["match_key"])):
        r = group[0]
        lines.append("%-8s %-9s %-55s %s" % (r["store"], r["category"], r["match_key"][:55], r["title"]))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"matched": len(matched), "single": len(single)}


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    parser = argparse.ArgumentParser(prog="python -m app.rematch")
    parser.add_argument("--report", type=Path, metavar="FILE")
    args = parser.parse_args(argv)

    stats = rematch()
    print("Предложений: %(offers)d, товаров после сопоставления: %(products)d, "
          "перенесено предложений: %(moved)d, удалено пустых товаров: %(removed)d" % stats)
    if args.report:
        result = report(args.report)
        print("Есть в нескольких магазинах: %(matched)d, только в одном: %(single)d" % result)
        print("Отчёт: %s" % args.report.resolve())
    return 0


if __name__ == "__main__":
    sys.exit(main())
