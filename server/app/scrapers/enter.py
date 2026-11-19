from typing import Dict, Iterator, List

from bs4 import BeautifulSoup

from .base import Fetcher, ParseError, ScrapedItem, absolute, amount, crawl, text_of
from .darwin import analytics_prices, with_brand
from .text_specs import laptop_details, phone_title

STORE = ("enter", "Enter", "enter.online")
BASE_URL = "https://enter.online"

CATEGORIES: Dict[str, str] = {
    "Смартфоны": "/ru/telefony/smartfony",
    "Ноутбуки": "/ru/noutbuki",
}

_CARD = "div.product-item.product-card"


def _page_url(path: str, page: int) -> str:
    return BASE_URL + path + ("" if page == 1 else "?page=%d" % page)


def parse_listing(html: str, category: str = "Смартфоны") -> List[ScrapedItem]:
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select(_CARD)
    if not cards:
        raise ParseError("на странице нет карточек %s — вёрстка сайта изменилась" % _CARD)

    items: List[ScrapedItem] = []
    for card in cards:
        link = card.select_one("a.stretched-link")
        marker = card.select_one("[data-id]")
        name = text_of(card, ".product-title")
        if link is None or marker is None or not name:
            continue
        name, brand = with_brand(name, card.get("data-gtm"))
        price, old_price = analytics_prices(card.get("data-gtm"))
        if not price:
            continue
        description = text_of(card, ".product-desc")
        if category == "Ноутбуки":
            title, details = name, laptop_details(description)
        else:
            title, details = phone_title(name, description), ""
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
            color="%s %s" % (title, description),
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
