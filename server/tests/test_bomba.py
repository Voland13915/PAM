"""Парсер bomba.md — на сохранённой странице и подставном HTTP, без доступа к сайту."""
from pathlib import Path

import httpx
import pytest

from app.scrapers import bomba
from app.scrapers.base import AccessBlocked, Fetcher, PageNotFound, ParseError

PAGE = (Path(__file__).parent / "fixtures" / "bomba_page1.html").read_text(encoding="utf-8")


def test_parse_listing_reads_ecommerce_items():
    items = {i.external_id: i for i in bomba.parse_listing(PAGE)}

    # товар без цены пропускается
    assert set(items) == {"1102917", "1100001", "1100002"}

    a36 = items["1102917"]
    assert a36.title == "Смартфон Samsung Galaxy A36 5G 8/256GB Black"
    assert a36.brand == "Samsung"
    assert a36.price == 6999
    assert a36.old_price == 7499  # цена + скидка
    assert a36.url == ("https://bomba.md/ru/product/"
                       "smartfon-samsung-galaxy-a36-5g-8256gb-black-1102917/")

    iphone = items["1100001"]
    assert iphone.price == 16999  # цена строкой с пробелом тоже читается
    assert iphone.old_price is None
    assert iphone.url.endswith("-1100001/")

    # фигурная скобка внутри названия не ломает разбор JSON
    assert items["1100002"].title.endswith("{Ocean Blue}")
    assert items["1100002"].url == ""


def test_page_without_items_is_parse_error():
    with pytest.raises(ParseError):
        bomba.parse_listing("<html><body>Технические работы</body></html>")


def _fetcher(pages: dict, requests: list) -> Fetcher:
    """Fetcher, который вместо сайта отдаёт страницы из словаря {номер: html}."""
    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        page = int(request.url.params["page"])
        return httpx.Response(200, text=pages.get(page, pages[max(pages)]))
    return Fetcher(delay=0, check_robots=False,
                   client=httpx.Client(transport=httpx.MockTransport(handler)))


def test_scrape_category_stops_when_pages_repeat():
    second = PAGE.replace("1102917", "1200000")  # на 2-й странице один новый товар
    requests = []
    items = list(bomba.scrape_category(_fetcher({1: PAGE, 2: second}, requests), "Смартфоны"))

    assert len(items) == 4  # 3 с первой + 1 новый со второй
    # 3-я страница (сайт повторил последнюю) не принесла нового — остановились
    assert len(requests) == 3
    first = requests[0].url
    assert first.path == "/ru/category/smartfonyi-686094/"
    assert first.params["limit"] == "32" and first.params["page"] == "1"


def test_fetcher_retries_server_errors():
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(503 if len(calls) < 3 else 200, text="ok")

    fetcher = Fetcher(delay=0, check_robots=False,
                      client=httpx.Client(transport=httpx.MockTransport(handler)))
    assert fetcher.get("https://bomba.md/") == "ok"
    assert len(calls) == 3


def test_fetcher_does_not_retry_404():
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(404)

    fetcher = Fetcher(delay=0, check_robots=False,
                      client=httpx.Client(transport=httpx.MockTransport(handler)))
    with pytest.raises(PageNotFound):
        fetcher.get("https://bomba.md/ru/category/net-takoy/")
    assert len(calls) == 1


def test_cloudflare_challenge_is_access_blocked():
    """Так bomba.md отвечает с ноября 2026: 403 и страница «Just a moment...»."""
    def handler(request):
        return httpx.Response(403, headers={"server": "cloudflare"},
                              text="<title>Just a moment...</title>")

    fetcher = Fetcher(delay=0, check_robots=False,
                      client=httpx.Client(transport=httpx.MockTransport(handler)))
    with pytest.raises(AccessBlocked, match="cloudflare"):
        fetcher.get("https://bomba.md/ru/category/smartfonyi-686094/")


def test_robots_txt_is_respected():
    requests = []

    def handler(request):
        requests.append(request.url.path)
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nDisallow: /search/\n")
        return httpx.Response(200, text="ok")

    fetcher = Fetcher(delay=0, client=httpx.Client(transport=httpx.MockTransport(handler)))
    assert fetcher.get("https://maximum.md/ro/laptopuri/") == "ok"
    with pytest.raises(AccessBlocked, match="robots.txt"):
        fetcher.get("https://maximum.md/search/?q=iphone")
    assert requests == ["/robots.txt", "/ro/laptopuri/"]  # robots.txt запрошен один раз
