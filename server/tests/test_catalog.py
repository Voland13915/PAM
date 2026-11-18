"""Снимки цен и построение истории (app/catalog.py)."""
from datetime import date

from app import catalog
from app.db import conn


def _new_product(name: str) -> int:
    return catalog.create_product(name, "Brand", "Смартфоны")


def _snapshots(offer_id: int) -> int:
    return conn.execute(
        "SELECT COUNT(*) AS n FROM price_snapshots WHERE offer_id = ?", (offer_id,)
    ).fetchone()["n"]


def test_snapshot_written_only_when_price_or_stock_changes():
    store = catalog.get_or_create_store("bomba", "Bomba", "bomba.md")
    product = _new_product("Snapshot test")

    offer = catalog.upsert_offer(product, store, "ext-1", 1000, now="2026-11-01T10:00:00.000Z")
    assert _snapshots(offer) == 1

    # тот же проход ещё раз — новой строки нет
    same = catalog.upsert_offer(product, store, "ext-1", 1000, now="2026-11-01T11:00:00.000Z")
    assert same == offer and _snapshots(offer) == 1

    catalog.upsert_offer(product, store, "ext-1", 950, now="2026-11-02T10:00:00.000Z")
    catalog.upsert_offer(product, store, "ext-1", 950, in_stock=False,
                         now="2026-11-03T10:00:00.000Z")
    assert _snapshots(offer) == 3

    seen = conn.execute("SELECT seen_at FROM offers WHERE id = ?", (offer,)).fetchone()
    assert seen["seen_at"] == "2026-11-03T10:00:00.000Z"


def test_history_is_daily_minimum_of_in_stock_offers():
    a = catalog.get_or_create_store("bomba", "Bomba", "bomba.md")
    b = catalog.get_or_create_store("maximum", "Maximum", "maximum.md")
    product = _new_product("History test")

    catalog.upsert_offer(product, a, "h-a", 1000, now="2026-11-01T10:00:00.000Z")
    catalog.upsert_offer(product, b, "h-b", 1100, now="2026-11-01T10:00:00.000Z")
    catalog.upsert_offer(product, b, "h-b", 900, now="2026-11-04T10:00:00.000Z")
    # дешёвое предложение закончилось — минимум снова 1000
    catalog.upsert_offer(product, b, "h-b", 900, in_stock=False, now="2026-11-06T10:00:00.000Z")

    prices, dates = catalog.price_history(product, today=date(2026, 11, 10))
    assert prices == [1000, 900, 1000, 1000]
    assert dates == ["2026-11-01", "2026-11-04", "2026-11-06", "2026-11-10"]


def test_history_keeps_last_points_only():
    store = catalog.get_or_create_store("bomba", "Bomba", "bomba.md")
    product = _new_product("Long history")
    for day in range(1, 11):
        catalog.upsert_offer(product, store, "long", 2000 - day,
                             now="2026-11-%02dT10:00:00.000Z" % day)

    prices, dates = catalog.price_history(product, today=date(2026, 11, 10))
    assert len(prices) == catalog.HISTORY_POINTS
    assert prices[-1] == 1990 and dates[-1] == "2026-11-10"


def test_product_without_snapshots_has_empty_history():
    product = _new_product("No offers")
    assert catalog.price_history(product) == ([], [])
