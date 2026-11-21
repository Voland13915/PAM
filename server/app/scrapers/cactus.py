import re
from typing import Dict, Iterator, List

from bs4 import BeautifulSoup

from ..matching import brand_from_title, is_refurbished
from .base import Fetcher, ParseError, ScrapedItem, absolute, amount, crawl, text_of
from .text_specs import laptop_details, model_part

STORE = ("cactus", "Cactus", "cactus.md")
BASE_URL = "https://www.cactus.md"

CATEGORIES: Dict[str, str] = {
    "Смартфоны": "/ru/catalogue/electronice/telefone/mobilnye-telefony/",
    "Ноутбуки": "/ru/catalogue/electronice/kompyuternaya-tehnika/noutbuki/",
    "Телевизоры": "/ru/catalogue/electronice/televizory/televizory/",
    "Стиральные машины": "/ru/catalogue/bytovaya-tehnika/krupnaya-bytovaya-tehnika/stiralnye-mashiny/",
    "Холодильники": "/ru/catalogue/bytovaya-tehnika/krupnaya-bytovaya-tehnika/holodilniki-i-morozilniki/",
    "Пылесосы": "/ru/catalogue/bytovaya-tehnika/tehnika-dlya-doma/pylesosy/",
    "Микроволновки": "/ru/catalogue/bytovaya-tehnika/tehnika-dlya-kuhni/mikrovolnovye-pechi/",
}

_CARD = "div.catalog__pill"
_PRICE = ".catalog__pill__controls__price"
_OLD_PRICE = "catalog__pill__controls__price_old"
_NOT_PHONES = ("трекер", "часы", "планшет", "наушники", "чехол", "зарядн")


_GLUED_SCRIPT = re.compile(r"(?<=[а-яё])(?=[a-z])", re.IGNORECASE)
_GLUED_BRAND = re.compile(r"\b(lenovo|asus|acer|dell)(?=\d)", re.IGNORECASE)


def laptop_title(title: str) -> str:
    title = _GLUED_BRAND.sub(r"\1 ", _GLUED_SCRIPT.sub(" ", title))
    model = model_part(title)
    if is_refurbished(title) and not is_refurbished(model):
        model += " Refurbished"
    return model or title


def _page_url(path: str, page: int) -> str:
    if page == 1:
        return BASE_URL + path
    return BASE_URL + path + "?sort_=ByView_Descending&page_=page_%d" % page


def parse_listing(html: str, category: str = "Смартфоны") -> List[ScrapedItem]:
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select(_CARD)
    if not cards:
        raise ParseError("на странице нет карточек %s — вёрстка сайта изменилась" % _CARD)

    items: List[ScrapedItem] = []
    for card in cards:
        code = card.get("data-product")
        link = card.select_one("a[href]")
        title = text_of(card, ".catalog__pill__text__title")
        if not code or link is None or not title:
            continue
        if category != "Ноутбуки" and title.lower().startswith(_NOT_PHONES):
            continue
        price = old_price = None
        for element in card.select(_PRICE):
            value = amount(text_of(element))
            if _OLD_PRICE in (element.get("class") or []):
                old_price = value
            else:
                price = value
        if not price:
            continue
        image = card.select_one("img")
        laptop = category == "Ноутбуки"
        features = " / ".join(text_of(li) for li in card.select(".description__list li"))
        if laptop:
            details = laptop_details(title)
        elif category in ("Смартфоны", "Телевизоры"):
            details = ""
        else:
            details = features
        items.append(ScrapedItem(
            external_id=code,
            title=laptop_title(title) if laptop else title,
            brand=brand_from_title(title),
            price=price,
            old_price=old_price if old_price and old_price > price else None,
            url=absolute(link["href"], BASE_URL),
            in_stock=True,
            details=details,
            image_url=absolute(image.get("src", ""), BASE_URL) if image is not None else "",
            color=title,
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
