import re
from typing import Dict, Iterator, List, Optional

from bs4 import BeautifulSoup

from .base import Fetcher, PageNotFound, ParseError, ScrapedItem

STORE = ("maximum", "Maximum", "maximum.md")
BASE_URL = "https://maximum.md"

CATEGORIES: Dict[str, str] = {
    "Смартфоны": "/ro/telefoane-si-gadgeturi/telefoane-si-comunicatii/smartphoneuri/",
    "Ноутбуки": "/ro/tehnica-computerizata/laptopuri-si-computere/laptopuri/",
}

_CARD = "div.product__item"
_TITLE = ".product__item__title a"
_PRICE_CURRENT = ".product__item__price-current"
_PRICE_OLD = ".product__item__price-old"
_COUNTER = ".page__header__title__counter"
_OUT_OF_STOCK = re.compile(r"nu este [îi]n stoc", re.IGNORECASE)
_AMOUNT = re.compile(r"(\d[\d\s ]*)\s*lei(?!\s*/)")
_PRODUCT_ID = re.compile(r"/ro/(\d+)/?$")
_TYPE_WORDS = {"smartphone", "laptop", "telefon", "notebook"}


def _price(text: str) -> Optional[float]:
    digits = re.sub(r"[^\d]", "", text.split("lei")[0])
    return float(digits) if digits else None


def _brand(title: str) -> str:
    words = title.split()
    if words and words[0].lower() in _TYPE_WORDS:
        words = words[1:]
    return words[0] if words else ""


def _page_url(path: str, page: int) -> str:
    return BASE_URL + path + ("" if page == 1 else "%d/" % page)


def parse_total(html: str) -> Optional[int]:
    counter = BeautifulSoup(html, "html.parser").select_one(_COUNTER)
    if counter is None:
        return None
    digits = re.sub(r"[^\d]", "", counter.get_text())
    return int(digits) if digits else None


def parse_listing(html: str) -> List[ScrapedItem]:
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select(_CARD)
    if not cards:
        raise ParseError("на странице нет карточек %s — вёрстка сайта изменилась" % _CARD)

    items: List[ScrapedItem] = []
    for card in cards:
        link = card.select_one(_TITLE)
        current = card.select_one(_PRICE_CURRENT)
        if link is None or current is None:
            continue
        href = link.get("href", "")
        match = _PRODUCT_ID.search(href)
        if match is None:
            continue
        price = _price(current.get_text(" "))
        if not price:
            continue
        old_el = card.select_one(_PRICE_OLD)
        if old_el is not None:
            old_price = _price(old_el.get_text(" "))
        else:
            block = current.parent.get_text(" ") if current.parent is not None else ""
            amounts = [_price(a + " lei") for a in _AMOUNT.findall(block)]
            old_price = max([a for a in amounts if a], default=None)
        title = " ".join(link.get_text(" ").split())
        items.append(ScrapedItem(
            external_id=match.group(1),
            title=title,
            brand=_brand(title),
            price=price,
            old_price=old_price if old_price and old_price > price else None,
            url=href if href.startswith("http") else BASE_URL + href,
            in_stock=not _OUT_OF_STOCK.search(card.get_text(" ")),
        ))
    return items


def scrape_category(
    fetcher: Fetcher, category: str, max_pages: int = 60
) -> Iterator[ScrapedItem]:
    path = CATEGORIES[category]
    seen = set()
    total = None
    for page in range(1, max_pages + 1):
        try:
            html = fetcher.get(_page_url(path, page))
        except PageNotFound:
            if page == 1:
                raise
            break
        if page == 1:
            total = parse_total(html)
        try:
            items = parse_listing(html)
        except ParseError:
            if page == 1:
                raise
            break
        fresh = [i for i in items if i.external_id not in seen]
        if not fresh:
            break
        for item in fresh:
            seen.add(item.external_id)
            yield item
    if total and len(seen) < total and page < max_pages:
        print("  внимание: на сайте указано товаров: %d, собрано: %d" % (total, len(seen)))
