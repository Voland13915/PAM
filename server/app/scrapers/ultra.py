import re
from typing import Dict, Iterator, List, Optional

from bs4 import BeautifulSoup

from ..matching import brand_from_title
from .base import Fetcher, PageNotFound, ParseError, ScrapedItem, pick_image

STORE = ("ultra", "Ultra", "ultra.md")
BASE_URL = "https://ultra.md"

CATEGORIES: Dict[str, str] = {
    "Смартфоны": "/ru/telefony/smartfony",
    "Ноутбуки": "/ru/kompyuternaya-tekhnika/noutbuki",
    "Телевизоры": "/ru/televizory-i-aksessuary/televizory",
}

_CARD = "div.product-card"
_LINK = "a.product-card__link"
_TITLE = ".product-card__title"
_SPECS = ".product-card__specs-title"
_PRICE_CURRENT = ".product-card__current-price"
_PRICE_OLD = ".product-card__old-price"
_UNPRICED = ".product-card__footer--unpriced"
_ADD_TO_CART = ".product-card__add-to-cart"
_MEMORY = re.compile(r"(\d+)\s*ГБ\s*/\s*(\d+)\s*(ГБ|ТБ)", re.IGNORECASE)


def _number(text: Optional[str]) -> Optional[float]:
    if not text:
        return None
    digits = re.sub(r"[^\d]", "", text)
    return float(digits) if digits else None


def _memory(specs: str) -> str:
    match = _MEMORY.search(specs.split("|")[0])
    if match is None:
        return ""
    ram, storage, unit = match.groups()
    return "%s/%s%s" % (ram, storage, "TB" if unit.upper() == "ТБ" else "GB")


def _page_url(path: str, page: int) -> str:
    return BASE_URL + path + ("" if page == 1 else "?page=%d" % page)


def _text(card, selector: str) -> str:
    element = card.select_one(selector)
    return " ".join(element.get_text(" ").split()) if element is not None else ""


def parse_listing(html: str) -> List[ScrapedItem]:
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select(_CARD)
    if not cards:
        raise ParseError("на странице нет карточек %s — вёрстка сайта изменилась" % _CARD)

    items: List[ScrapedItem] = []
    for card in cards:
        code = card.get("data-code")
        link = card.select_one(_LINK)
        title = _text(card, _TITLE)
        if not code or link is None or not title:
            continue
        if card.select_one(_UNPRICED) is not None:
            continue
        price = _number(card.get("data-price")) or _number(_text(card, _PRICE_CURRENT))
        if not price:
            continue
        old_price = _number(_text(card, _PRICE_OLD))
        specs = _text(card, _SPECS)
        memory = _memory(specs)
        href = link.get("href", "")
        items.append(ScrapedItem(
            external_id=code,
            title=title + (" " + memory if memory else ""),
            brand=brand_from_title(title),
            price=price,
            old_price=old_price if old_price and old_price > price else None,
            url=href if href.startswith("http") else BASE_URL + href,
            in_stock=card.select_one(_ADD_TO_CART) is not None,
            details=specs,
            image_url=pick_image(card, BASE_URL),
        ))
    return items


def scrape_category(
    fetcher: Fetcher, category: str, max_pages: int = 60
) -> Iterator[ScrapedItem]:
    path = CATEGORIES[category]
    seen = set()
    for page in range(1, max_pages + 1):
        try:
            html = fetcher.get(_page_url(path, page))
        except PageNotFound:
            if page == 1:
                raise
            return
        try:
            items = parse_listing(html)
        except ParseError:
            if page == 1:
                raise
            return
        fresh = [i for i in items if i.external_id not in seen]
        if not fresh:
            return
        for item in fresh:
            seen.add(item.external_id)
            yield item
