from pathlib import Path

import httpx

from app import catalog, ingest, scrape
from app.db import conn
from app.scrapers.base import Fetcher, ScrapedItem

PAGE = (Path(__file__).parent / "fixtures" / "bomba_page1.html").read_text(encoding="utf-8")


def _laptop(external_id: str, price: float, title: str = None) -> ScrapedItem:
    return ScrapedItem(external_id, title or "Ноутбук Test %s" % external_id, "Test", price)


def _offer(store_id: int, external_id: str):
    return conn.execute(
        "SELECT * FROM offers WHERE store_id = ? AND external_id = ?", (store_id, external_id)
    ).fetchone()


def test_second_run_updates_prices_and_marks_missing():
    store = catalog.get_or_create_store("bomba", "Bomba", "bomba.md")

    first = "2026-11-10T10:00:00.000Z"
    with catalog.transaction():
        stats = ingest.save_items(store, "Ноутбуки",
                                  [_laptop("L1", 10000), _laptop("L2", 12000)], first)
        assert ingest.mark_missing(store, "Ноутбуки", first) == 0
    assert stats == {"items": 2, "new_products": 2, "new_offers": 2, "price_changes": 0}

    product = conn.execute(
        "SELECT * FROM products WHERE id = ?", (_offer(store, "L1")["product_id"],)
    ).fetchone()
    assert product["name"] == "Test L1"
    assert product["category"] == "Ноутбуки"

    second = "2026-11-11T10:00:00.000Z"
    with catalog.transaction():
        stats = ingest.save_items(store, "Ноутбуки", [_laptop("L1", 9500)], second)
        missing = ingest.mark_missing(store, "Ноутбуки", second)
    assert stats["new_products"] == 0 and stats["price_changes"] == 1
    assert missing == 1

    l2 = _offer(store, "L2")
    assert l2["in_stock"] == 0
    assert l2["seen_at"] == first
    snapshots = conn.execute(
        "SELECT price, in_stock FROM price_snapshots WHERE offer_id = ? ORDER BY id",
        (l2["id"],),
    ).fetchall()
    assert [tuple(s) for s in snapshots] == [(12000, 1), (12000, 0)]

    third = "2026-11-12T10:00:00.000Z"
    with catalog.transaction():
        ingest.save_items(store, "Ноутбуки", [_laptop("L1", 9500), _laptop("L2", 12000)], third)
    assert _offer(store, "L2")["in_stock"] == 1
    assert _offer(store, "L2")["product_id"] == l2["product_id"]


def test_same_title_in_two_stores_becomes_one_product():
    bomba = catalog.get_or_create_store("bomba", "Bomba", "bomba.md")
    maximum = catalog.get_or_create_store("maximum", "Maximum", "maximum.md")
    now = "2026-11-12T10:00:00.000Z"
    with catalog.transaction():
        ingest.save_items(bomba, "Ноутбуки",
                          [_laptop("B-9", 100, "Игровой ноутбук Lenovo LOQ 15IAX9 Luna Grey")], now)
        ingest.save_items(maximum, "Ноутбуки",
                          [_laptop("M-9", 90, "Laptop Lenovo LOQ 15IAX9 Luna Grey (83GS005CRK)")], now)
    assert _offer(bomba, "B-9")["product_id"] == _offer(maximum, "M-9")["product_id"]


def _mock_fetcher(*args, **kwargs) -> Fetcher:
    def handler(request):
        if request.url.params.get("page") == "1":
            return httpx.Response(200, text=PAGE)
        return httpx.Response(200, text="<script>const ecommerceItems = {};</script>")
    return Fetcher(delay=0, check_robots=False,
                   client=httpx.Client(transport=httpx.MockTransport(handler)))


def test_cli_dry_run_writes_nothing(monkeypatch, capsys):
    monkeypatch.setattr(scrape, "Fetcher", _mock_fetcher)
    before = conn.execute("SELECT COUNT(*) AS n FROM offers").fetchone()["n"]

    assert scrape.main(["bomba", "--category", "Смартфоны", "--dry-run"]) == 0

    out = capsys.readouterr().out
    assert "найдено товаров: 3" in out
    assert "Samsung Galaxy A36" in out
    assert conn.execute("SELECT COUNT(*) AS n FROM offers").fetchone()["n"] == before


def test_cli_run_replaces_demo_catalog(monkeypatch, capsys):
    assert conn.execute(
        "SELECT COUNT(*) AS n FROM offers WHERE external_id LIKE 'demo-%'"
    ).fetchone()["n"] > 0
    monkeypatch.setattr(scrape, "Fetcher", _mock_fetcher)

    assert scrape.main(["bomba", "--category", "Смартфоны"]) == 0

    out = capsys.readouterr().out
    assert "Удалён демо-каталог" in out
    assert conn.execute(
        "SELECT COUNT(*) AS n FROM offers WHERE external_id LIKE 'demo-%'"
    ).fetchone()["n"] == 0
    codes = {r["code"] for r in conn.execute("SELECT code FROM stores")}
    assert {"darwin", "enter", "smart"}.isdisjoint(codes)
    assert {"bomba", "maximum"} <= codes

    a36 = _offer(catalog.get_or_create_store("bomba", "Bomba", "bomba.md"), "1102917")
    assert a36["price"] == 6999 and a36["old_price"] == 7499
    bomba = conn.execute("SELECT last_sync FROM stores WHERE code = 'bomba'").fetchone()
    assert bomba["last_sync"] != ""


def test_cli_all_runs_every_automatic_store(monkeypatch, capsys):
    fixtures = Path(__file__).parent / "fixtures"
    pages = {
        "maximum.md": (fixtures / "maximum_page1.html").read_text(encoding="utf-8"),
        "ultra.md": (fixtures / "ultra_page1.html").read_text(encoding="utf-8"),
    }

    def fetcher(*args, **kwargs):
        def handler(request):
            if request.url.params.get("page") or request.url.path.endswith("/2/"):
                return httpx.Response(404)
            return httpx.Response(200, text=pages[request.url.host])
        return Fetcher(delay=0, check_robots=False,
                       client=httpx.Client(transport=httpx.MockTransport(handler)))

    monkeypatch.setattr(scrape, "Fetcher", fetcher)
    assert scrape.main(["all", "--category", "Смартфоны", "--dry-run"]) == 0

    out = capsys.readouterr().out
    assert "Maximum / Смартфоны" in out and "Ultra / Смартфоны" in out
    assert "Bomba" not in out
