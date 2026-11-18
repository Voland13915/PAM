import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DB_PATH = Path(os.environ.get("DB_PATH", str(BASE_DIR / "app.db")))

SCHEMA_VERSION = 5

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  email         TEXT    NOT NULL UNIQUE,
  password_hash TEXT    NOT NULL,
  name          TEXT    NOT NULL,
  created_at    TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS notes (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id    INTEGER NOT NULL REFERENCES users (id),
  title      TEXT    NOT NULL,
  content    TEXT    NOT NULL DEFAULT '',
  created_at TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS stores (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  code       TEXT    NOT NULL UNIQUE,
  name       TEXT    NOT NULL,
  website    TEXT    NOT NULL,
  last_sync  TEXT    NOT NULL DEFAULT '',
  created_at TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  name       TEXT    NOT NULL,
  brand      TEXT    NOT NULL DEFAULT '',
  category   TEXT    NOT NULL,
  specs      TEXT    NOT NULL DEFAULT '{}',
  match_key  TEXT    UNIQUE,
  created_at TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS offers (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  product_id  INTEGER NOT NULL REFERENCES products (id) ON DELETE CASCADE,
  store_id    INTEGER NOT NULL REFERENCES stores (id),
  external_id TEXT    NOT NULL,
  title       TEXT    NOT NULL DEFAULT '',
  url         TEXT    NOT NULL DEFAULT '',
  price       REAL    NOT NULL,
  old_price   REAL,
  in_stock    INTEGER NOT NULL DEFAULT 1,
  image_url   TEXT    NOT NULL DEFAULT '',
  details     TEXT    NOT NULL DEFAULT '',
  images      TEXT    NOT NULL DEFAULT '',
  images_fetched_at TEXT NOT NULL DEFAULT '',
  seen_at     TEXT    NOT NULL,
  UNIQUE (store_id, external_id)
);
CREATE INDEX IF NOT EXISTS offers_product ON offers (product_id);

CREATE TABLE IF NOT EXISTS price_snapshots (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  offer_id    INTEGER NOT NULL REFERENCES offers (id) ON DELETE CASCADE,
  price       REAL    NOT NULL,
  in_stock    INTEGER NOT NULL,
  captured_at TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS snapshots_offer ON price_snapshots (offer_id, captured_at);

CREATE TABLE IF NOT EXISTS wishlist (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id      INTEGER NOT NULL REFERENCES users (id),
  product_id   INTEGER NOT NULL REFERENCES products (id) ON DELETE CASCADE,
  store_id     INTEGER NOT NULL REFERENCES stores (id),
  target_price REAL    NOT NULL,
  notify       INTEGER NOT NULL DEFAULT 1,
  created_at   TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS files (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id    INTEGER NOT NULL REFERENCES users (id),
  name       TEXT    NOT NULL,
  mime_type  TEXT    NOT NULL,
  size       INTEGER NOT NULL,
  path       TEXT    NOT NULL,
  created_at TEXT    NOT NULL
);
"""


def _migrate(db: sqlite3.Connection) -> None:
    version = db.execute("PRAGMA user_version").fetchone()[0]
    if version >= SCHEMA_VERSION:
        return

    def has_table(name: str) -> bool:
        return db.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)
        ).fetchone() is not None

    if version < 2 and has_table("products"):
        print("Схема каталога обновлена до версии %d: товары, магазины и "
              "избранное созданы заново." % SCHEMA_VERSION)
        db.executescript(
            "DROP TABLE IF EXISTS wishlist;"
            "DROP TABLE IF EXISTS price_snapshots;"
            "DROP TABLE IF EXISTS offers;"
            "DROP TABLE IF EXISTS products;"
            "DROP TABLE IF EXISTS stores;"
        )
    elif has_table("offers"):
        columns = {r[1] for r in db.execute("PRAGMA table_info(offers)")}
        if "image_url" not in columns:
            db.execute("ALTER TABLE offers ADD COLUMN image_url TEXT NOT NULL DEFAULT ''")
        if "details" not in columns:
            db.execute("ALTER TABLE offers ADD COLUMN details TEXT NOT NULL DEFAULT ''")
        if "images" not in columns:
            db.execute("ALTER TABLE offers ADD COLUMN images TEXT NOT NULL DEFAULT ''")
            db.execute(
                "ALTER TABLE offers ADD COLUMN images_fetched_at TEXT NOT NULL DEFAULT ''"
            )
    db.execute("PRAGMA user_version = %d" % SCHEMA_VERSION)


conn = sqlite3.connect(DB_PATH, check_same_thread=False, isolation_level=None)
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA foreign_keys = ON")
_migrate(conn)
conn.executescript(_SCHEMA)

conn.create_function(
    "ULOWER", 1, lambda s: s.lower() if isinstance(s, str) else s,
    deterministic=True,
)


def now_iso():
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )
