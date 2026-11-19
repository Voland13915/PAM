import re
from typing import Dict, Iterator, List, Optional

from bs4 import BeautifulSoup

from ..matching import brand_from_title
from .base import Fetcher, ParseError, ScrapedItem, absolute, amount, crawl, text_of
from .text_specs import cpu, gpu, size_text

STORE = ("pandashop", "PandaShop", "pandashop.md")
BASE_URL = "https://www.pandashop.md"

CATEGORIES: Dict[str, str] = {
    "Смартфоны": "/ru/catalog/electronics/telephones/mobile/",
    "Ноутбуки": "/ru/catalog/electronics/orgtech/notebooks/",
}

_CARD = "div.card.js-itemsList-item"
_RYZEN = re.compile(r"\bR(?:yzen)?\s*([3579])[\s-]+(?=\w)", re.IGNORECASE)
_RYZEN_AI = re.compile(r"\bR\s+(?=AI\b)", re.IGNORECASE)
_REPEATED = re.compile(r"\b(\w+)\s+\1\b", re.IGNORECASE)


def _page_url(path: str, page: int) -> str:
    return BASE_URL + path + ("" if page == 1 else "?page_=page_%d" % page)


def _properties(card) -> Dict[str, str]:
    result = {}
    for row in card.select(".card-propertiesTbl-row"):
        cells = row.select(".card-propertiesTbl-cell")
        if len(cells) == 2:
            result[text_of(cells[0]).rstrip(":").lower()] = text_of(cells[1])
    return result


def _size(value: Optional[str]) -> Optional[int]:
    match = re.search(r"(\d+(?:[.,]\d+)?)\s*(гб|тб|gb|tb)", value or "", re.IGNORECASE)
    if match is None:
        return None
    number = float(match.group(1).replace(",", "."))
    if match.group(2).lower() in ("тб", "tb"):
        return int(round(number * 1024))
    return int(round(number / 1000.0)) * 1024 if number >= 900 else int(round(number))


def _screen(value: Optional[str]) -> Optional[str]:
    match = re.search(r"\d+(?:[.,]\d+)?", value or "")
    return match.group(0).replace(",", ".") + '"' if match else None


def expand_cpu(text: str) -> str:
    return _RYZEN.sub(r"Ryzen \1 ", _RYZEN_AI.sub("Ryzen ", text))


def laptop_cpu(title: str, value: str) -> str:
    bracket = re.search(r"\(([^)]*)\)", title)
    for source in (bracket.group(1) if bracket else "", value):
        found = cpu(expand_cpu(source))
        if found:
            return found
    return expand_cpu(value).strip()


def laptop_details(title: str, properties: Dict[str, str]) -> str:
    parts = []
    screen = _screen(properties.get("диагональ экрана"))
    if screen:
        parts.append(screen)
    ram = _size(properties.get("оперативная память"))
    storage = _size(properties.get("ssd диск"))
    if ram and storage:
        parts += [size_text(ram), size_text(storage)]
    elif storage:
        parts.append(size_text(storage))
    processor = laptop_cpu(title, properties.get("процессор", ""))
    if processor:
        parts.append(processor)
    graphics = gpu(title)
    if graphics:
        parts.append(graphics)
    return " | ".join(parts)


def phone_details(properties: Dict[str, str]) -> str:
    parts = []
    ram = _size(properties.get("оперативная память"))
    storage = _size(properties.get("встроенная память"))
    if ram and storage:
        parts.append("%s / %s" % (size_text(ram), size_text(storage)))
    screen = _screen(properties.get("диагональ дисплея"))
    if screen:
        parts.append(screen)
    return " | ".join(parts)


def laptop_title(title: str) -> str:
    return " ".join(_REPEATED.sub(r"\1", re.sub(r"\([^)]*\)", " ", title)).split())


def parse_listing(html: str, category: str = "Смартфоны") -> List[ScrapedItem]:
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select(_CARD)
    if not cards:
        raise ParseError("на странице нет карточек %s — вёрстка сайта изменилась" % _CARD)

    items: List[ScrapedItem] = []
    for card in cards:
        code = card.get("data-product")
        link = card.select_one("a.card-title")
        raw_title = text_of(card, ".card-title")
        if not code or link is None or not raw_title:
            continue
        price_meta = card.select_one("meta[itemprop=price]")
        price = amount(price_meta.get("content") if price_meta else None) or \
            amount(text_of(card, ".card-price_curr"))
        if not price:
            continue
        old_price = amount(text_of(card, ".card-price_old_inner"))
        availability = card.select_one("[itemprop=availability]")
        in_stock = "InStock" in (availability.get("href", "") if availability else "") \
            if availability is not None else card.select_one("button.card-cart") is not None
        properties = _properties(card)
        if category == "Ноутбуки":
            title, details = laptop_title(raw_title), laptop_details(raw_title, properties)
        else:
            title, details = raw_title, phone_details(properties)
        image = card.select_one("meta[itemprop=image]")
        items.append(ScrapedItem(
            external_id=code,
            title=title,
            brand=brand_from_title(title),
            price=price,
            old_price=old_price if old_price and old_price > price else None,
            url=absolute(link.get("href", ""), BASE_URL),
            in_stock=in_stock,
            details=details,
            image_url=absolute(image.get("content", ""), BASE_URL) if image is not None else "",
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
        fresh_session=True,
    )
