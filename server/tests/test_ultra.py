from pathlib import Path

import httpx

from app.scrapers import ultra
from app.scrapers.base import Fetcher

PAGE = (Path(__file__).parent / "fixtures" / "ultra_page1.html").read_text(encoding="utf-8")


def test_parse_listing_reads_real_cards():
    items = {i.external_id: i for i in ultra.parse_listing(PAGE)}
    assert set(items) == {"272306", "272318", "272310", "276779", "233025"}

    pro_max = items["272306"]
    assert pro_max.title == "Смартфон Apple iPhone 18 Pro Max Серебристый 12/512GB"
    assert pro_max.brand == "Apple"
    assert pro_max.price == 40399
    assert pro_max.old_price is None
    assert pro_max.url == ("https://ultra.md/ru/telefony/smartfony/"
                           "apple-iphone-18-pro-max-12-gb-512-gb-5g-serebristyi")
    assert pro_max.details.startswith("12 ГБ / 512 ГБ")
    assert pro_max.image_url.startswith("https://cdn.ultra.md/images/")
    assert pro_max.image_url.endswith(".webp")

    assert items["272310"].title.endswith("12/1024GB")

    dyson = items["276779"]
    assert dyson.price == 8799 and dyson.old_price == 9499
    assert dyson.title == "Утюжок для волос Dyson Airstrait HT03 Фиолетовый"


def test_only_cards_with_cart_button_are_in_stock():
    items = {i.external_id: i for i in ultra.parse_listing(PAGE)}
    assert items["272306"].in_stock
    assert items["276779"].in_stock
    showroom = items["233025"]
    assert not showroom.in_stock
    assert showroom.price == 20999


def test_pages_use_query_parameter_and_stop_on_repeat():
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(str(request.url))
        return httpx.Response(200, text=PAGE)

    fetcher = Fetcher(delay=0, check_robots=False,
                      client=httpx.Client(transport=httpx.MockTransport(handler)))
    items = list(ultra.scrape_category(fetcher, "Смартфоны"))

    assert len(items) == 5
    assert requests == [
        "https://ultra.md/ru/telefony/smartfony",
        "https://ultra.md/ru/telefony/smartfony?page=2",
    ]
