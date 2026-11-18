import json
import logging
import sys
import threading
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .db import conn, now_iso
from .scrapers.base import AccessBlocked, Fetcher, PageNotFound

MAX_IMAGES = 12
REFRESH_AFTER = timedelta(days=7)
RETRY_AFTER = timedelta(hours=6)

_MAXIMUM_ORIGINAL = "https://i.simpalsmedia.com/marketplace/products/original/"
_MAXIMUM_RESIZED = "https://i.simpalsmedia.com/thumbor/800x0/i.simpalsmedia.com/marketplace/products/original/"

_log = logging.getLogger("uvicorn.error")
_lock = threading.Lock()
_fetcher: Optional[Fetcher] = None


def _get_fetcher() -> Fetcher:
    global _fetcher
    if _fetcher is None:
        _fetcher = Fetcher(delay=0.5, retries=2, timeout=10.0)
    return _fetcher


def _image_values(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _image_values(item)
    elif isinstance(value, dict):
        for key in ("contentUrl", "url"):
            if isinstance(value.get(key), str):
                yield value[key]
                return


def _products(node: Any) -> Iterable[Dict[str, Any]]:
    if isinstance(node, list):
        for item in node:
            yield from _products(item)
    elif isinstance(node, dict):
        kind = node.get("@type")
        if kind == "Product" or (isinstance(kind, list) and "Product" in kind):
            yield node
        for key in ("@graph", "mainEntity"):
            if key in node:
                yield from _products(node[key])


def _resize(url: str) -> str:
    if url.startswith(_MAXIMUM_ORIGINAL):
        return _MAXIMUM_RESIZED + url[len(_MAXIMUM_ORIGINAL):]
    return url


def extract_images(html: str, page_url: str) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    found: List[str] = []
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(script.string or "")
        except ValueError:
            continue
        for product in _products(data):
            found.extend(_image_values(product.get("image")))
        if found:
            break
    if not found:
        found = [m.get("content", "") for m in soup.select('meta[property="og:image"]')]

    images: List[str] = []
    for url in found:
        url = _resize(urljoin(page_url, url.strip()))
        if url.startswith("http") and url not in images:
            images.append(url)
    return images


def _fresh(fetched_at: str, images: str) -> bool:
    if not fetched_at:
        return False
    moment = datetime.fromisoformat(fetched_at.replace("Z", "+00:00"))
    age = datetime.now(timezone.utc) - moment
    return age < (REFRESH_AFTER if images not in ("", "[]") else RETRY_AFTER)


def _download(url: str) -> Optional[List[str]]:
    try:
        with _lock:
            html = _get_fetcher().get(url)
    except (AccessBlocked, PageNotFound) as exc:
        _log.warning("gallery: %s: %s", url, exc)
        return []
    except Exception as exc:
        _log.warning("gallery: %s: %r", url, exc)
        return None
    images = extract_images(html, url)
    if not images:
        _log.warning("gallery: %s: на странице не найдено фото", url)
    return images


def product_images(product_id: int) -> List[str]:
    rows = conn.execute(
        "SELECT id, store_id, url, image_url, images, images_fetched_at FROM offers "
        "WHERE product_id = ? AND url != '' ORDER BY in_stock DESC, price",
        (product_id,),
    ).fetchall()

    per_store: Dict[int, Any] = {}
    for row in rows:
        per_store.setdefault(row["store_id"], row)

    result: List[str] = []
    for row in per_store.values():
        if _fresh(row["images_fetched_at"], row["images"]):
            images = json.loads(row["images"] or "[]")
        else:
            images = _download(row["url"])
            if images is None:
                images = json.loads(row["images"] or "[]")
            else:
                conn.execute(
                    "UPDATE offers SET images = ?, images_fetched_at = ? WHERE id = ?",
                    (json.dumps(images), now_iso(), row["id"]),
                )
        for url in images or ([row["image_url"]] if row["image_url"] else []):
            if url not in result:
                result.append(url)

    if not result:
        fallback = conn.execute(
            "SELECT image_url FROM offers WHERE product_id = ? AND image_url != '' LIMIT 1",
            (product_id,),
        ).fetchone()
        if fallback is not None:
            result.append(fallback["image_url"])
    return result[:MAX_IMAGES]


def reset(product_id: Optional[int] = None) -> int:
    if product_id is None:
        cursor = conn.execute("UPDATE offers SET images = '', images_fetched_at = ''")
    else:
        cursor = conn.execute(
            "UPDATE offers SET images = '', images_fetched_at = '' WHERE product_id = ?",
            (product_id,),
        )
    return cursor.rowcount


def _check(product_id: int) -> None:
    logging.basicConfig(level=logging.WARNING, format="%(message)s")
    product = conn.execute("SELECT name FROM products WHERE id = ?", (product_id,)).fetchone()
    if product is None:
        print("Товар %d не найден" % product_id)
        return
    print(product["name"])
    reset(product_id)
    for row in conn.execute(
        "SELECT s.name AS store, o.url, o.in_stock, o.price FROM offers o "
        "JOIN stores s ON s.id = o.store_id WHERE o.product_id = ? ORDER BY s.name, o.price",
        (product_id,),
    ):
        print("  %s  %.0f  %s  %s" % (
            row["store"], row["price"], "в наличии" if row["in_stock"] else "нет", row["url"] or "(без ссылки)"))
    images = product_images(product_id)
    print("Фото: %d" % len(images))
    for url in images:
        print("  " + url)


def main(argv: List[str]) -> None:
    if argv and argv[0] == "--reset":
        print("Сброшено предложений: %d" % reset())
    elif argv and argv[0].isdigit():
        _check(int(argv[0]))
    elif argv:
        rows = conn.execute(
            "SELECT p.id, p.name, COUNT(DISTINCT o.store_id) AS stores FROM products p "
            "JOIN offers o ON o.product_id = p.id WHERE p.name LIKE ? "
            "GROUP BY p.id ORDER BY stores DESC, p.name LIMIT 5",
            ("%" + " ".join(argv) + "%",),
        ).fetchall()
        if not rows:
            print("Ничего не найдено")
            return
        for row in rows:
            print("%6d  %s" % (row["id"], row["name"]))
        print()
        _check(rows[0]["id"])
    else:
        print("python -m app.gallery <id товара | часть названия> | --reset")


if __name__ == "__main__":
    main(sys.argv[1:])
