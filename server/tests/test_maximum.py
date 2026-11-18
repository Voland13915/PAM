from pathlib import Path

import httpx
import pytest

from app.scrapers import maximum
from app.scrapers.base import Fetcher, ParseError

PAGE = (Path(__file__).parent / "fixtures" / "maximum_page1.html").read_text(encoding="utf-8")


def test_parse_listing_reads_real_cards():
    items = {i.external_id: i for i in maximum.parse_listing(PAGE)}
    assert set(items) == {"6744031", "6749202", "6864355", "6870847"}

    iphone = items["6744031"]
    assert iphone.title == "Smartphone Apple iPhone 15 128GB Black MTP03"
    assert iphone.brand == "Apple"
    assert iphone.price == 14999 and iphone.old_price is None
    assert iphone.url == "https://maximum.md/ro/6744031/"
    assert iphone.in_stock
    assert iphone.image_url.startswith("https://i.simpalsmedia.com/thumbor/239x0/")
    assert iphone.details.startswith("Ecran, inch: 6,1")
    assert "Cod produsului" not in iphone.details

    oppo = items["6749202"]
    assert oppo.price == 3759 and oppo.old_price == 3899
    assert items["6864355"].old_price == 6799


def test_hidden_out_of_stock_label_is_ignored_and_visible_one_counts():
    items = {i.external_id: i for i in maximum.parse_listing(PAGE)}
    assert [i for i in items if not items[i].in_stock] == ["6870847"]


def test_page_without_cards_is_parse_error():
    with pytest.raises(ParseError):
        maximum.parse_listing("<html><body>Pagina nu a fost găsită</body></html>")


def _fetcher(handler) -> Fetcher:
    return Fetcher(delay=0, check_robots=False,
                   client=httpx.Client(transport=httpx.MockTransport(handler)))


def test_pages_are_path_segments_and_404_ends_category():
    requests = []
    second = PAGE.replace("6744031", "6000001")

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request.url.path)
        if request.url.path.endswith("/smartphoneuri/"):
            return httpx.Response(200, text=PAGE)
        if request.url.path.endswith("/smartphoneuri/2/"):
            return httpx.Response(200, text=second)
        return httpx.Response(404)

    items = list(maximum.scrape_category(_fetcher(handler), "Смартфоны"))

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

    items = list(maximum.scrape_category(_fetcher(handler), "Смартфоны"))

    assert len(items) == 4
    assert capsys.readouterr().out == ""


def test_parse_total_and_warning_when_fewer_collected(capsys):
    assert maximum.parse_total(PAGE) == 4
    page = PAGE.replace("produse: 4", "produse: 710")

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/smartphoneuri/"):
            return httpx.Response(200, text=page)
        return httpx.Response(404)

    list(maximum.scrape_category(_fetcher(handler), "Смартфоны"))

    assert "указано товаров: 710, собрано: 4" in capsys.readouterr().out
