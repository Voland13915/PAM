import sqlite3
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

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
  id               INTEGER PRIMARY KEY AUTOINCREMENT,
  name             TEXT    NOT NULL,
  website          TEXT    NOT NULL,
  products_tracked INTEGER NOT NULL DEFAULT 0,
  last_sync        TEXT    NOT NULL DEFAULT '',
  created_at       TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  name          TEXT    NOT NULL,
  brand         TEXT    NOT NULL DEFAULT '',
  category      TEXT    NOT NULL,
  specs         TEXT    NOT NULL DEFAULT '{}',  -- JSON-объект «характеристика: значение»
  offers        TEXT    NOT NULL DEFAULT '[]',  -- JSON-массив цен по магазинам
  price_history TEXT    NOT NULL DEFAULT '[]',  -- JSON-массив минимальных цен
  created_at    TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS wishlist (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id      INTEGER NOT NULL REFERENCES users (id),
  product_id   INTEGER NOT NULL REFERENCES products (id),
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

conn = sqlite3.connect(
    BASE_DIR / "app.db", check_same_thread=False, isolation_level=None
)
conn.row_factory = sqlite3.Row  # rows behave like dicts: row["title"]
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
