import json
import re
from typing import Dict, Iterator, List, Optional, Tuple

from bs4 import BeautifulSoup

from ..matching import brand_from_title, canonical_brand
from .base import Fetcher, ParseError, ScrapedItem, absolute, amount, crawl, text_of
from .text_specs import laptop_details

STORE = ("darwin", "Darwin", "darwin.md")
BASE_URL = "https://darwin.md"

CATEGORIES: Dict[str, str] = {
    "Смартфоны": "/ru/telefoane/smartphone",
    "Ноутбуки": "/ru/noutbuki",
    "Телевизоры": "/ru/tv-i-akssesuary/televizory",
    "Стиральные машины": "/ru/bytovaya-tehnika/stiralnye-masiny",
    "Холодильники": "/ru/bytovaya-tehnika/xolodilniki",
    "Пылесосы": "/ru/bytovaya-tehnika/pylesosy",
    "Микроволновки": "/ru/bytovaya-tehnika/mikrovolnovye-peci",
}

_CARD = "div.product-card.product-item"
_SIZE = re.compile(r"(\d+)\s*(ГБ|ТБ|GB|TB)", re.IGNORECASE)


def _page_url(path: str, page: int) -> str:
    return BASE_URL + path + ("" if page == 1 else "?page=%d" % page)


def analytics_item(raw: Optional[str]) -> dict:
    try:
        item = json.loads(raw or "")["ecommerce"]["items"][0]
    except (ValueError, KeyError, IndexError, TypeError):
        return {}
    return item if isinstance(item, dict) else {}


def analytics_prices(raw: Optional[str]) -> Tuple[Optional[float], Optional[float]]:
    item = analytics_item(raw)
    price = amount(item.get("price"))
    discount = amount(item.get("discount")) or 0
    return price, (price + discount if price and discount else None)


def with_brand(name: str, raw: Optional[str]) -> Tuple[str, str]:
    brand = brand_from_title(name)
    declared = str(analytics_item(raw).get("item_brand") or "").strip()
    if declared and declared.lower() not in name.lower():
        brand = canonical_brand(declared)
        return "%s %s" % (brand, name), brand
    return name, brand or (canonical_brand(declared) if declared else "")


def phone_parts(title: str, specs: str) -> Tuple[str, str]:
    segments = [s.strip() for s in specs.split("|") if s.strip()]
    ram = next((s for s in segments if re.fullmatch(r"\d{1,2}\s*(ГБ|GB)", s, re.IGNORECASE)), None)
    details = " | ".join(s for s in segments if s is not ram)
    if ram is None:
        return title, details
    match = _SIZE.search(title)
    if match is None:
        return title, details
    unit = "TB" if match.group(2).upper() in ("ТБ", "TB") else "GB"
    memory = "%s/%s%s" % (re.sub(r"\D", "", ram), match.group(1), unit)
    return title[:match.start()] + memory + title[match.end():], details


def parse_listing(html: str, category: str = "Смартфоны") -> List[ScrapedItem]:
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select(_CARD)
    if not cards:
        raise ParseError("на странице нет карточек %s — вёрстка сайта изменилась" % _CARD)

    items: List[ScrapedItem] = []
    for card in cards:
        link = card.select_one("a.product-link")
        marker = card.select_one("[data-id]")
        name = text_of(card, ".title-product")
        if link is None or marker is None or not name:
            continue
        name, brand = with_brand(name, link.get("data-ga4"))
        price, old_price = analytics_prices(link.get("data-ga4"))
        price = price or amount(text_of(card, ".price-new"))
        if not price:
            continue
        old_price = old_price or amount(text_of(card, ".price-old"))
        specs = text_of(card, ".title-description .color-80")
        if category == "Ноутбуки":
            title, details = name, laptop_details(specs)
        elif category == "Смартфоны":
            title, details = phone_parts(name, specs)
        else:
            title, details = name, specs
        image = card.select_one(".product-img img")
        image_url = (image.get("data-src") or image.get("src") or "") if image is not None else ""
        items.append(ScrapedItem(
            external_id=marker["data-id"],
            title=title,
            brand=brand,
            price=price,
            old_price=old_price if old_price and old_price > price else None,
            url=absolute(link.get("href", ""), BASE_URL),
            in_stock=card.select_one("button.add-to-cart") is not None,
            details=details,
            image_url=absolute(image_url, BASE_URL),
        ))
    return items


def scrape_category(
    fetcher: Fetcher, category: str, max_pages: int = 200
) -> Iterator[ScrapedItem]:
    path = CATEGORIES[category]
    return crawl(
        fetcher,
        lambda page: _page_url(path, page),
        lambda html: parse_listing(html, category),
        max_pages,
    )
