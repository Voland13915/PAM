from pathlib import Path

import httpx
import pytest

from app.scrapers import maximum
from app.scrapers.base import Fetcher, ParseError

PAGE = (Path(__file__).parent / "fixtures" / "maximum_page1.html").read_text(encoding="utf-8")


def test_parse_listing_reads_cards():
    items = {i.external_id: i for i in maximum.parse_listing(PAGE)}
    assert set(items) == {"6854535", "6998945", "7004001", "6877754"}

    poco = items["6854535"]
    assert poco.title == "Smartphone Xiaomi POCO X6 5G 12/256GB Blue"
    assert poco.brand == "Xiaomi"
    assert poco.price == 7499 and poco.old_price == 10899
    assert poco.url == "https://maximum.md/ro/6854535/"
    assert poco.in_stock

    oppo = items["6998945"]
    assert oppo.title == "Smartphone OPPO Find X9 Ultra 5G 12/512GB Umber"
    assert oppo.price == 34999
    assert oppo.old_price is None

    assert not items["7004001"].in_stock

    asus = items["6877754"]
    assert asus.brand == "ASUS"
    assert asus.old_price == 8999


def test_page_without_cards_is_parse_error():
    with pytest.raises(ParseError):
        maximum.parse_listing("<html><body>Pagina nu a fost găsită</body></html>")


def test_pages_are_path_segments_and_404_ends_category():
    requests = []
    second = PAGE.replace("6854535", "6000001")

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request.url.path)
        if request.url.path.endswith("/smartphoneuri/"):
            return httpx.Response(200, text=PAGE)
        if request.url.path.endswith("/smartphoneuri/2/"):
            return httpx.Response(200, text=second)
        return httpx.Response(404)

    fetcher = Fetcher(delay=0, check_robots=False,
                      client=httpx.Client(transport=httpx.MockTransport(handler)))
    items = list(maximum.scrape_category(fetcher, "Смартфоны"))

    assert len(items) == 5
    assert requests == [
        "/ro/telefoane-si-gadgeturi/telefoane-si-comunicatii/smartphoneuri/",
        "/ro/telefoane-si-gadgeturi/telefoane-si-comunicatii/smartphoneuri/2/",
        "/ro/telefoane-si-gadgeturi/telefoane-si-comunicatii/smartphoneuri/3/",
    ]


def test_page_without_cards_after_first_ends_category(capsys):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/smartphoneuri/"):
            return httpx.Response(200, text=PAGE)
        return httpx.Response(200, text="<html><body>Nu au fost găsite produse</body></html>")

    fetcher = Fetcher(delay=0, check_robots=False,
                      client=httpx.Client(transport=httpx.MockTransport(handler)))
    items = list(maximum.scrape_category(fetcher, "Смартфоны"))

    assert len(items) == 4
    assert capsys.readouterr().out == ""


def test_parse_total_and_warning_when_fewer_collected(capsys):
    assert maximum.parse_total(PAGE) == 4
    page = PAGE.replace("produse: 4", "produse: 710")

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/smartphoneuri/"):
            return httpx.Response(200, text=page)
        return httpx.Response(404)

    fetcher = Fetcher(delay=0, check_robots=False,
                      client=httpx.Client(transport=httpx.MockTransport(handler)))
    list(maximum.scrape_category(fetcher, "Смартфоны"))

    assert "указано товаров: 710, собрано: 4" in capsys.readouterr().out
