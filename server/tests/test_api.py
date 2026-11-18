import os
import sqlite3
import subprocess
import sys
from pathlib import Path

from app import catalog
from app.seed import _PRODUCTS


def test_demo_catalog_keeps_old_response_shape(client):
    r = client.get("/products", params={"search": "Galaxy A36"})
    assert r.status_code == 200
    item = r.json()["items"][0]
    assert set(item) >= {"id", "name", "brand", "category", "specs", "offers",
                         "priceHistory", "createdAt"}
    assert item["priceHistory"] == [7499, 7399, 7299, 7199, 6999, 6849]
    assert len(item["priceHistoryDates"]) == 6
    assert min(o["price"] for o in item["offers"] if o["inStock"]) == 6849


def test_all_demo_products_listed(client):
    r = client.get("/products", params={"limit": 100})
    assert r.json()["total"] == len(_PRODUCTS)


def test_stores_report_counts_and_sync_time(client):
    stores = client.get("/stores").json()["items"]
    bomba = next(s for s in stores if s["name"] == "Bomba")
    assert bomba["productsTracked"] > 0
    assert bomba["lastSync"].endswith("Z")


def test_store_without_offers_is_hidden(client):
    catalog.get_or_create_store("empty", "Пустой магазин", "empty.md")
    names = [s["name"] for s in client.get("/stores", params={"limit": 100}).json()["items"]]
    assert "Пустой магазин" not in names


def test_out_of_stock_product_hidden_from_list_but_opens_by_id(client):
    body = {"name": "Только под заказ", "brand": "X", "category": "Смартфоны",
            "offers": [{"storeId": 1, "price": 500, "inStock": True}]}
    created = client.post("/products", json=body).json()
    pid = created["id"]

    def listed() -> int:
        return client.get("/products", params={"search": "Только под заказ"}).json()["total"]

    assert listed() == 1
    catalog.upsert_offer(pid, 1, "manual-%d" % pid, 500, in_stock=False)
    assert listed() == 0
    assert client.get("/products/%d" % pid).status_code == 200

    body["offers"] = [{"storeId": 1, "price": 500, "inStock": False}]
    assert client.put("/products/%d" % pid, json=body).status_code == 400

    body["offers"] = [{"storeId": 2, "price": 600, "inStock": True}]
    updated = client.put("/products/%d" % pid, json=body).json()
    assert [o["storeId"] for o in updated["offers"]] == [2]
    assert listed() == 1

    assert client.delete("/products/%d" % pid).status_code == 204
    assert client.get("/products/%d" % pid).status_code == 404


def test_duplicate_store_in_offers_rejected(client):
    body = {"name": "Дубль", "category": "Смартфоны",
            "offers": [{"storeId": 1, "price": 1}, {"storeId": 1, "price": 2}]}
    assert client.post("/products", json=body).status_code == 400


def test_old_database_is_migrated(tmp_path):
    db_file = tmp_path / "old.db"
    old = sqlite3.connect(db_file)
    old.executescript(
        "CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT, password_hash TEXT,"
        " name TEXT, created_at TEXT);"
        "INSERT INTO users VALUES (1, 'a@b.c', 'x', 'Old user', '2026-01-01');"
        "CREATE TABLE stores (id INTEGER PRIMARY KEY, name TEXT, website TEXT,"
        " products_tracked INTEGER, last_sync TEXT, created_at TEXT);"
        "CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, brand TEXT,"
        " category TEXT, specs TEXT, offers TEXT, price_history TEXT, created_at TEXT);"
    )
    old.close()

    server_dir = Path(__file__).resolve().parent.parent
    subprocess.run(
        [sys.executable, "-c", "import app.main"],
        cwd=server_dir, check=True,
        env={**os.environ, "DB_PATH": str(db_file), "SEED_DEMO": "0"},
    )

    db = sqlite3.connect(db_file)
    assert db.execute("PRAGMA user_version").fetchone()[0] == 5
    assert db.execute("SELECT name FROM users").fetchall() == [("Old user",)]
    columns = {r[1] for r in db.execute("PRAGMA table_info(products)")}
    assert "match_key" in columns and "offers" not in columns
    assert {r[0] for r in db.execute("SELECT code FROM stores")} == {"maximum", "ultra"}


def test_version_2_database_gets_image_column_and_keeps_data(tmp_path):
    db_file = tmp_path / "v2.db"
    old = sqlite3.connect(db_file)
    old.executescript(
        "CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT NOT NULL, brand TEXT NOT NULL "
        "DEFAULT '', category TEXT NOT NULL, specs TEXT NOT NULL DEFAULT '{}', match_key TEXT "
        "UNIQUE, created_at TEXT NOT NULL);"
        "CREATE TABLE offers (id INTEGER PRIMARY KEY, product_id INTEGER NOT NULL, store_id "
        "INTEGER NOT NULL, external_id TEXT NOT NULL, title TEXT NOT NULL DEFAULT '', url TEXT "
        "NOT NULL DEFAULT '', price REAL NOT NULL, old_price REAL, in_stock INTEGER NOT NULL "
        "DEFAULT 1, seen_at TEXT NOT NULL, UNIQUE (store_id, external_id));"
        "INSERT INTO products VALUES (1, 'Phone', 'X', 'Смартфоны', '{}', NULL, '2026-11-18');"
        "INSERT INTO offers VALUES (1, 1, 1, 'e1', 'Phone', '', 100, NULL, 1, '2026-11-18');"
        "PRAGMA user_version = 2;"
    )
    old.close()

    server_dir = Path(__file__).resolve().parent.parent
    subprocess.run(
        [sys.executable, "-c", "import app.main"],
        cwd=server_dir, check=True,
        env={**os.environ, "DB_PATH": str(db_file), "SEED_DEMO": "0"},
    )

    db = sqlite3.connect(db_file)
    assert db.execute("PRAGMA user_version").fetchone()[0] == 5
    assert db.execute("SELECT name FROM products").fetchall() == [("Phone",)]
    assert db.execute("SELECT image_url, details FROM offers").fetchall() == [("", "")]
