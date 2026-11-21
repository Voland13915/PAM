import re
from typing import Dict, Iterator, List, Optional, Tuple, Union

from bs4 import BeautifulSoup

from ..matching import brand_from_title
from .base import Fetcher, PageNotFound, ParseError, ScrapedItem, paths, pick_image

STORE = ("maximum", "Maximum", "maximum.md")
BASE_URL = "https://maximum.md"

_WASHERS = "/ru/krupnaya-bytovaya-tehnika/stiralnye-i-sushilnye-mashiny/"
_FRIDGES = "/ru/krupnaya-bytovaya-tehnika/holodilniki/"
_VACUUMS = "/ru/krupnaya-bytovaya-tehnika/pylesosy/"

CATEGORIES: Dict[str, Union[str, Tuple[str, ...]]] = {
    "Смартфоны": "/ro/telefoane-si-gadgeturi/telefoane-si-comunicatii/smartphoneuri/",
    "Ноутбуки": "/ro/tehnica-computerizata/laptopuri-si-computere/laptopuri/",
    "Телевизоры": "/ro/televizoare/televizoare/televizoare/",
    "Стиральные машины": tuple(_WASHERS + p for p in (
        "stiralnye-mashiny-s-frontalnoj-zagruzkoj/", "stiralnye-mashiny-s-sushkoj/",
        "stiralnye-mashiny-s-vertikalnoj-zagruzkoj/",
    )),
    "Холодильники": tuple(_FRIDGES + p for p in (
        "holodilniki-sidebyside-i-french-door/", "holodilniki-s-nijnej-morozilnoj-kameroj/",
        "holodilniki-s-verhnej-morozilnoj-kameroj/", "holodilniki-odnodvernye/",
    )),
    "Пылесосы": tuple(_VACUUMS + p for p in (
        "pylesosy-roboty/", "pylesosy-portativnye/", "pylesosy-bez-meshka/", "pylesosy-s-meshkom/",
        "pylesosy-s-akvafiltrom/", "pylesosy-moyushhie/", "pylesosy-vertikalnye/",
    )),
    "Микроволновки": "/ru/krupnaya-bytovaya-tehnika/mikrovolnovye-pechi/mikrovolnovye-pechi/",
}

_CARD = "div.product__item"
_TITLE = ".product__item__title a"
_PRICE_CURRENT = ".product__item__price-current"
_PRICE_OLD = ".product__item__price-old"
_COUNTER = ".page__header__title__counter"
_DESCRIPTION = ".product-item-description"
_CODE = ".product-item-description-code"
_OUT_OF_STOCK = re.compile(r"nu este [îi]n stoc|нет в наличии", re.IGNORECASE)
_CURRENCY = re.compile(r"lei|ле[еи]в|лей", re.IGNORECASE)
_AMOUNT = re.compile(r"(\d[\d\s\u00a0]*)\s*(?:lei|ле[еи]в|лей)(?!\s*/)", re.IGNORECASE)
_PRODUCT_ID = re.compile(r"/(?:ro|ru)/(\d+)/?$")


def _price(text: str) -> Optional[float]:
    digits = re.sub(r"[^\d]", "", _CURRENCY.split(text)[0])
    return float(digits) if digits else None


def _visible(node, card) -> bool:
    for parent in node.parents:
        classes = parent.get("class") or []
        style = (parent.get("style") or "").replace(" ", "")
        if "hidden" in classes or "display:none" in style:
            return False
        if parent is card:
            return True
    return True


def _details(card) -> str:
    description = card.select_one(_DESCRIPTION)
    if description is None:
        return ""
    for code in description.select(_CODE):
        code.extract()
    return " ".join(description.get_text(" ").split())


def _in_stock(card) -> bool:
    return not any(_visible(text, card) for text in card.find_all(string=_OUT_OF_STOCK))


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
            amounts = [_price(a) for a in _AMOUNT.findall(block)]
            old_price = max([a for a in amounts if a], default=None)
        title = " ".join(link.get_text(" ").split())
        items.append(ScrapedItem(
            external_id=match.group(1),
            title=title,
            brand=brand_from_title(title),
            price=price,
            old_price=old_price if old_price and old_price > price else None,
            url=href if href.startswith("http") else BASE_URL + href,
            in_stock=_in_stock(card),
            details=_details(card),
            image_url=pick_image(card, BASE_URL),
        ))
    return items


def scrape_category(
    fetcher: Fetcher, category: str, max_pages: int = 60
) -> Iterator[ScrapedItem]:
    seen: set = set()
    for path in paths(CATEGORIES[category]):
        yield from _scrape_path(fetcher, path, max_pages, seen)


def _scrape_path(fetcher: Fetcher, path: str, max_pages: int, seen: set) -> Iterator[ScrapedItem]:
    path_seen: set = set()
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
        page_ids = {i.external_id for i in items}
        if page_ids <= path_seen:
            break
        path_seen |= page_ids
        for item in items:
            if item.external_id not in seen:
                seen.add(item.external_id)
                yield item
    if total and len(path_seen) < total and page < max_pages:
        print("  внимание: на сайте указано товаров: %d, собрано: %d" % (total, len(path_seen)))
