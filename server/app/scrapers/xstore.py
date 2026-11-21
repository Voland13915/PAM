from typing import Dict, Iterator, List

from bs4 import BeautifulSoup

from ..matching import brand_from_title
from .base import Fetcher, ParseError, ScrapedItem, absolute, amount, crawl, text_of
from .text_specs import laptop_details, phone_title

STORE = ("xstore", "XStore", "xstore.md")
BASE_URL = "https://xstore.md"

CATEGORIES: Dict[str, str] = {
    "Смартфоны": "/ru/telefony/smartfony",
    "Ноутбуки": "/ru/noutbuki",
    "Телевизоры": "/ru/televizory",
    "Пылесосы": "/ru/roboty-pylesosy",
}

_CARD = "figure.card-product"


def _page_url(path: str, page: int) -> str:
    return BASE_URL + path + ("" if page == 1 else "?page=%d" % page)


def parse_listing(html: str, category: str = "Смартфоны") -> List[ScrapedItem]:
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select(_CARD)
    if not cards:
        raise ParseError("на странице нет карточек %s — вёрстка сайта изменилась" % _CARD)

    items: List[ScrapedItem] = []
    for card in cards:
        link = card.select_one("a.xnc-title")
        marker = card.select_one("[data-id]")
        name = text_of(card, ".xnc-title")
        if link is None or marker is None or not name:
            continue
        price = amount(text_of(card, ".xnc-price"))
        if not price:
            continue
        old_price = amount(text_of(card, ".xnc-price-striked"))
        attributes = text_of(card, ".xnc-attr")
        if category == "Ноутбуки":
            title, details = name, laptop_details(attributes)
        elif category == "Смартфоны":
            title, details = phone_title(name, attributes), ""
        else:
            title, details = name, attributes
        image = card.select_one("img.xnc-img")
        items.append(ScrapedItem(
            external_id=marker["data-id"],
            title=title,
            brand=brand_from_title(name),
            price=price,
            old_price=old_price if old_price and old_price > price else None,
            url=absolute(link.get("href", ""), BASE_URL),
            in_stock=card.select_one(".add_xcart") is not None,
            details=details,
            image_url=absolute(image.get("src", ""), BASE_URL) if image is not None else "",
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
