import pytest

from app import catalog

CATEGORY = "Фильтры-тест"


@pytest.fixture(scope="module")
def data(client):
    maximum = catalog.get_or_create_store("maximum", "Maximum", "maximum.md")
    ultra = catalog.get_or_create_store("ultra", "Ultra", "ultra.md")
    rows = [
        ("Alpha Phone 128GB", "Alpha", [(maximum, 1000, None), (ultra, 1100, None)]),
        ("Alpha Phone Pro 256GB", "Alpha", [(ultra, 3000, 3500)]),
        ("Beta Phone 64GB", "Beta", [(maximum, 500, 700)]),
        ("beta phone max", "BETA", [(maximum, 2000, None), (ultra, 1900, None)]),
    ]
    ids = {}
    for name, brand, offers in rows:
        product = catalog.create_product(name, brand, CATEGORY)
        for store, price, old in offers:
            catalog.upsert_offer(product, store, "flt-%d-%d" % (product, store), price,
                                 old_price=old, title="Смартфон " + name + " Чёрный")
        ids[name] = product
    return {"ids": ids, "maximum": maximum, "ultra": ultra}


def _names(client, **params):
    params = {"category": CATEGORY, "limit": 100, **params}
    return [p["name"] for p in client.get("/products", params=params).json()["items"]]


def test_category_filter_and_default_sort_puts_compared_first(client, data):
    names = _names(client)
    assert set(names) == {"Alpha Phone 128GB", "Alpha Phone Pro 256GB",
                          "Beta Phone 64GB", "beta phone max"}
    assert set(names[:2]) == {"Alpha Phone 128GB", "beta phone max"}


def test_sort_by_best_in_stock_price(client, data):
    assert _names(client, sort="price_asc") == [
        "Beta Phone 64GB", "Alpha Phone 128GB", "beta phone max", "Alpha Phone Pro 256GB"]
    assert _names(client, sort="price_desc")[0] == "Alpha Phone Pro 256GB"
    assert _names(client, sort="discount")[:2] == ["Beta Phone 64GB", "Alpha Phone Pro 256GB"]


def test_brand_filter_ignores_case(client, data):
    assert sorted(_names(client, brand="beta")) == ["Beta Phone 64GB", "beta phone max"]
    assert len(_names(client, brand="alpha,beta")) == 4


def test_price_store_discount_and_multi_filters(client, data):
    assert sorted(_names(client, min_price=900, max_price=2000)) == [
        "Alpha Phone 128GB", "beta phone max"]
    assert sorted(_names(client, store=data["ultra"])) == [
        "Alpha Phone 128GB", "Alpha Phone Pro 256GB", "beta phone max"]
    assert sorted(_names(client, discount=1)) == ["Alpha Phone Pro 256GB", "Beta Phone 64GB"]
    assert sorted(_names(client, multi=1)) == ["Alpha Phone 128GB", "beta phone max"]


def test_search_matches_all_words_in_any_order_and_store_titles(client, data):
    assert _names(client, search="phone alpha") == ["Alpha Phone 128GB", "Alpha Phone Pro 256GB"]
    assert len(_names(client, search="чёрный")) == 4
    assert _names(client, search="alpha 64gb") == []


def test_facets_count_each_dimension_without_its_own_filter(client, data):
    facets = client.get("/products/facets",
                        params={"category": CATEGORY, "brand": "alpha"}).json()
    assert facets["total"] == 2
    brands = {b["name"].lower(): b["count"] for b in facets["brands"]}
    assert brands == {"alpha": 2, "beta": 2}
    stores = {s["id"]: s["count"] for s in facets["stores"]}
    assert stores == {data["maximum"]: 1, data["ultra"]: 2}
    assert facets["minPrice"] == 1000 and facets["maxPrice"] == 3000
    assert {"name": CATEGORY, "count": 2} in facets["categories"]


def test_unavailable_products_are_hidden_unless_asked(client, data):
    ultra = data["ultra"]
    product = catalog.create_product("Gamma Phone Gone", "Gamma", CATEGORY)
    catalog.upsert_offer(product, ultra, "flt-gone", 4000, in_stock=False)

    assert "Gamma Phone Gone" not in _names(client)
    names = _names(client, unavailable=1)
    assert names[-1] == "Gamma Phone Gone"
    assert "Gamma Phone Gone" in _names(client, unavailable=1, store=ultra)
    assert _names(client, unavailable=1, sort="price_asc")[-1] == "Gamma Phone Gone"

    facets = client.get("/products/facets",
                        params={"category": CATEGORY, "unavailable": 1}).json()
    assert facets["total"] == 5
    assert {s["id"]: s["count"] for s in facets["stores"]}[ultra] == 4
