import re
from typing import Dict, Iterator, List

from bs4 import BeautifulSoup

from ..matching import brand_from_title, is_refurbished
from .base import Fetcher, ParseError, ScrapedItem, absolute, amount, crawl, text_of
from .text_specs import laptop_details, model_part

STORE = ("smart", "Smart", "smart.md")
BASE_URL = "https://www.smart.md"

CATEGORIES: Dict[str, str] = {
    "Смартфоны": "/ru/smartphone",
    "Ноутбуки": "/ru/laptopuri",
    "Телевизоры": "/ru/televizoare",
}

_CARD = "div.category-product-card"
_LAPTOP_PREFIX = re.compile(
    r"^\s*(?:(?:laptop|workstation|ultrabook|smb|consumer)(?:\s+(?:gaming|business))?\s+)+",
    re.IGNORECASE
)


def _page_url(path: str, page: int) -> str:
    return BASE_URL + path + ("" if page == 1 else "?page=%d" % page)


def laptop_model(title: str) -> str:
    model = model_part(_LAPTOP_PREFIX.sub("", title))
    if is_refurbished(title) and not is_refurbished(model):
        model += " Refurbished"
    return model or title


def parse_listing(html: str, category: str = "Смартфоны") -> List[ScrapedItem]:
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select(_CARD)
    if not cards:
        raise ParseError("на странице нет карточек %s — вёрстка сайта изменилась" % _CARD)

    items: List[ScrapedItem] = []
    for card in cards:
        link = card.select_one(".custom_product_title a[data-product-id]")
        raw_title = text_of(card, ".custom_product_title h4")
        if link is None or not raw_title:
            continue
        prices = [amount(text_of(span)) for span in card.select(".custom_product_price span")]
        prices = [p for p in prices if p]
        if not prices:
            continue
        price, highest = min(prices), max(prices)
        if category == "Ноутбуки":
            title, details = laptop_model(raw_title), laptop_details(raw_title)
        elif category == "Телевизоры":
            title, details = raw_title, raw_title
        else:
            title, details = raw_title, ""
        image = card.select_one(".custom_product_image_default img")
        items.append(ScrapedItem(
            external_id=link["data-product-id"],
            title=title,
            brand=brand_from_title(title),
            price=price,
            old_price=highest if highest > price else None,
            url=absolute(link.get("href", ""), BASE_URL),
            in_stock=card.select_one("button.add_to_cart") is not None,
            details=details,
            image_url=absolute(image.get("src", ""), BASE_URL) if image is not None else "",
            color=raw_title,
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
