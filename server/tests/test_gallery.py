from pathlib import Path

import httpx
import pytest

from app import catalog, gallery
from app.scrapers.base import Fetcher

FIXTURES = Path(__file__).parent / "fixtures"
MAXIMUM = (FIXTURES / "maximum_product.html").read_text(encoding="utf-8")
ULTRA = (FIXTURES / "ultra_product.html").read_text(encoding="utf-8")


def test_images_from_maximum_product_page_are_resized_originals():
    images = gallery.extract_images(MAXIMUM, "https://maximum.md/ro/6949091/")
    assert len(images) == 9
    assert all(i.startswith("https://i.simpalsmedia.com/thumbor/800x0/i.simpalsmedia.com/"
                            "marketplace/products/original/") for i in images)


def test_images_from_ultra_product_page():
    images = gallery.extract_images(ULTRA, "https://ultra.md/ru/product/a17-4128gb-light-blue")
    assert len(images) == 10
    assert images[0] == ("https://cdn-ultra.esempla.com/storage/webp/"
                         "6a58e405-133b-44f3-ada1-760b5503261c.webp")


def test_page_without_structured_data_falls_back_to_og_image():
    html = '<html><head><meta property="og:image" content="/img/a.jpg"></head></html>'
    assert gallery.extract_images(html, "https://shop.md/p/1") == ["https://shop.md/img/a.jpg"]


@pytest.fixture
def requests(monkeypatch):
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        if request.url.host == "maximum.md":
            return httpx.Response(200, text=MAXIMUM)
        if request.url.host == "ultra.md":
            return httpx.Response(200, text=ULTRA)
        return httpx.Response(404)

    fetcher = Fetcher(delay=0, check_robots=False,
                      client=httpx.Client(transport=httpx.MockTransport(handler)))
    monkeypatch.setattr(gallery, "_fetcher", fetcher)
    return seen


def _product_with_offers(tag):
    maximum = catalog.get_or_create_store("maximum", "Maximum", "maximum.md")
    ultra = catalog.get_or_create_store("ultra", "Ultra", "ultra.md")
    product = catalog.create_product("Gallery phone", "Samsung", "Смартфоны")
    catalog.upsert_offer(product, maximum, "gal-%s-1" % tag, 5099, url="https://maximum.md/ro/6949091/",
                         image_url="https://i.simpalsmedia.com/thumbor/239x0/a.jpg")
    catalog.upsert_offer(product, maximum, "gal-%s-2" % tag, 5199, url="https://maximum.md/ro/6949092/")
    catalog.upsert_offer(product, ultra, "gal-%s-3" % tag, 5099,
                         url="https://ultra.md/ru/product/a17-4128gb-light-blue")
    return product


def test_gallery_is_downloaded_once_per_store_and_cached(requests):
    product = _product_with_offers("cache")

    images = gallery.product_images(product)
    assert len(images) == gallery.MAX_IMAGES
    assert len(requests) == 2
    assert images[0].startswith("https://i.simpalsmedia.com/thumbor/800x0/")
    assert any(i.startswith("https://cdn-ultra.esempla.com/") for i in images)

    assert gallery.product_images(product) == images
    assert len(requests) == 2


def test_listing_image_is_used_when_store_page_has_no_gallery(monkeypatch, requests):
    product = _product_with_offers("empty")
    monkeypatch.setattr(gallery, "_download", lambda url: [])
    assert gallery.product_images(product) == ["https://i.simpalsmedia.com/thumbor/239x0/a.jpg"]


def test_images_endpoint(client, requests):
    product = _product_with_offers("api")
    response = client.get("/products/%d/images" % product)
    assert response.status_code == 200
    assert len(response.json()["images"]) == gallery.MAX_IMAGES
    assert client.get("/products/999999/images").status_code == 404


def test_reset_clears_cached_images():
    from app import gallery
    from app.db import conn

    conn.execute("UPDATE offers SET images = '[\"x\"]', images_fetched_at = '2026-01-01T00:00:00Z'")
    assert gallery.reset() > 0
    assert conn.execute("SELECT COUNT(*) FROM offers WHERE images_fetched_at != ''").fetchone()[0] == 0
