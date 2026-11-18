import json
import re
from typing import Dict, Iterator, List, Optional

from .base import Fetcher, ParseError, ScrapedItem

STORE = ("bomba", "Bomba", "bomba.md")  # (code, name, website)
BASE_URL = "https://bomba.md"
PAGE_SIZE = 32

CATEGORIES: Dict[str, str] = {
    "Смартфоны": "/ru/category/smartfonyi-686094/",
    "Ноутбуки": "/ru/category/vse-noutbuki-634579/",
}

_ITEMS_START = re.compile(r"ecommerceItems\s*=\s*")
_PRODUCT_HREF = re.compile(r"""href=["']((?:https://bomba\.md)?/ru/product/[^"'#?]+)["']""")


def _find_items(node, found: List[dict]) -> None:
    if isinstance(node, dict):
        if "item_id" in node:
            found.append(node)
            return
        for value in node.values():
            _find_items(value, found)
    elif isinstance(node, list):
        for value in node:
            _find_items(value, found)


def _number(value) -> Optional[float]:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace(" ", "").replace(" ", "").replace(",", "."))
    except ValueError:
        return None


def _product_urls(html: str) -> Dict[str, str]:
    urls: Dict[str, str] = {}
    for href in _PRODUCT_HREF.findall(html):
        url = href if href.startswith("http") else BASE_URL + href
        match = re.search(r"(\d+)/?$", href)
        if match:
            urls.setdefault(match.group(1), url)
    return urls


def parse_listing(html: str) -> List[ScrapedItem]:
    start = _ITEMS_START.search(html)
    if start is None:
        raise ParseError("на странице нет ecommerceItems — структура сайта изменилась")
    try:
        data, _ = json.JSONDecoder().raw_decode(html, start.end())
    except ValueError as exc:
        snippet = html[start.end():start.end() + 200]
        raise ParseError("ecommerceItems не разбирается как JSON: %s… (%s)" % (snippet, exc))

    raw: List[dict] = []
    _find_items(data, raw)
    urls = _product_urls(html)

    items: List[ScrapedItem] = []
    for r in raw:
        price = _number(r.get("price"))
        if price is None or price <= 0:
            continue
        external_id = str(r["item_id"])
        discount = _number(r.get("discount")) or 0
        items.append(ScrapedItem(
            external_id=external_id,
            title=str(r.get("item_name", "")).strip(),
            brand=str(r.get("item_brand") or "").strip(),
            price=price,
            old_price=price + discount if discount > 0 else None,
            url=urls.get(external_id, ""),
        ))
    return items


def scrape_category(
    fetcher: Fetcher, category: str, max_pages: int = 60
) -> Iterator[ScrapedItem]:
    path = CATEGORIES[category]
    seen = set()
    for page in range(1, max_pages + 1):
        html = fetcher.get(
            BASE_URL + path, params={"page": page, "limit": PAGE_SIZE, "store": 0}
        )
        fresh = [i for i in parse_listing(html) if i.external_id not in seen]
        if not fresh:
            return
        for item in fresh:
            seen.add(item.external_id)
            yield item
