from pathlib import Path

import httpx
import pytest

from app import catalog, ingest
from app.db import conn
from app.grouping import same_cpu
from app.matching import brand_from_title, laptop_code, match_key
from app.rematch import rematch
from app.scrapers import AUTOMATIC, SCRAPERS, cactus, darwin, enter, pandashop, smart, xstore
from app.scrapers.base import Fetcher
from app.scrapers.text_specs import laptop_details, phone_title
from app.specs import normalize_cpu, parse_specs

FIXTURES = Path(__file__).parent / "fixtures"
NEW_STORES = ("smart", "cactus", "xstore", "darwin", "enter", "pandashop")


def _page(code: str, kind: str) -> str:
    return (FIXTURES / ("%s_%s.html" % (code, kind))).read_text(encoding="utf-8")


def _items(code: str, kind: str):
    category = "Смартфоны" if kind == "phones" else "Ноутбуки"
    return SCRAPERS[code].parse_listing(_page(code, kind), category)


@pytest.mark.parametrize("code", NEW_STORES)
@pytest.mark.parametrize("kind", ["phones", "laptops"])
def test_every_card_is_parsed(code, kind):
    items = _items(code, kind)
    assert len(items) >= 6
    for item in items:
        assert item.external_id and item.title and item.price > 0
        assert item.url.startswith(SCRAPERS[code].BASE_URL)
        assert item.image_url.startswith("http")
        assert item.old_price is None or item.old_price > item.price
        assert item.brand and item.brand[0].isupper()
    assert len({i.external_id for i in items}) == len(items)


def test_smart_prices_and_laptop_titles():
    phone = _items("smart", "phones")[0]
    assert phone.title == "Apple iPhone 17 Pro 256GB, Deep Blue (SIM fizic + eSIM)"
    assert (phone.price, phone.old_price, phone.in_stock) == (25999, 26899, True)
    assert phone.url == "https://www.smart.md/apple-iphone-17-pro-256gb-deep-blue"

    laptop = _items("smart", "laptops")[1]
    assert laptop.title == "ASUS TUF A16 FA607NUQ"
    assert laptop.brand == "ASUS"
    assert laptop.details == '16" | 16 ГБ | 512 ГБ | AMD Ryzen 7 170 | NVIDIA GeForce RTX 4050'
    assert smart.laptop_model("Laptop Gaming 16'' HP OMEN MAX 16, Shadow Black, Intel Core Ultra 9 "
                              "275HX, 64GB/2048GB, FreeDOS") == "HP OMEN MAX 16"


def test_cactus_laptop_title_keeps_model_only():
    laptops = {i.external_id: i for i in _items("cactus", "laptops")}
    loq = laptops["191008"]
    assert loq.title == "Ноутбук Lenovo LOQ 15AHP10"
    assert loq.details == '15.6" | 16 ГБ | 1 ТБ | Ryzen 7 250 | RTX 5050'
    air = laptops["168627"]
    assert air.title.startswith('Ноутбук Apple MacBook Air 13.6"')
    assert air.details == '13.6" | 24 ГБ | 512 ГБ | M4'


def test_xstore_phone_title_gets_memory_and_colour():
    phone = _items("xstore", "phones")[0]
    assert phone.title == "Apple iPhone 17 Pro Max 12/256GB Deep Blue"
    assert (phone.price, phone.old_price) == (28499, 30199)
    assert phone_title("Apple iPhone 17 Pro Max", "12 GB / 2 TB / Deep Blue") == \
        "Apple iPhone 17 Pro Max 12/2TB Deep Blue"


def test_darwin_moves_ram_into_title():
    phone = _items("darwin", "phones")[0]
    assert phone.title == "Apple iPhone 18 Pro 12/256GB Glacier"
    assert phone.details == '6.3" | 48 Мп | Single SIM'
    assert (phone.price, phone.old_price) == (30999, 32899)
    specs = parse_specs("Смартфоны", phone.details, (12, 256))
    assert (specs.ram, specs.storage, specs.screen) == (12, 256, 6.3)
    assert darwin.phone_parts("Samsung Galaxy Fold 7 1 ТБ Синий Тень", '8.0" | 200 МП | 16 ГБ')[0] == \
        "Samsung Galaxy Fold 7 16/1TB Синий Тень"


def test_enter_preorder_is_not_in_stock():
    phones = _items("enter", "phones")
    duo = next(i for i in phones if "Duo" in i.title)
    assert duo.in_stock is False
    assert all(i.in_stock for i in phones if i is not duo)
    first = phones[0]
    assert first.title == "Смартфон Apple iPhone 18 Pro 12/256GB Бургундия"
    flip = next(i for i in phones if "Flip 7 FE" in i.title)
    assert flip.old_price == flip.price + 4800


def _page_urls(module, html: str):
    requested = []

    def handler(request):
        requested.append(str(request.url))
        if len(requested) > 1:
            return httpx.Response(404)
        return httpx.Response(200, text=html)

    fetcher = Fetcher(delay=0, check_robots=False,
                      client=httpx.Client(transport=httpx.MockTransport(handler)))
    items = list(module.scrape_category(fetcher, "Смартфоны", 5))
    return requested, items


@pytest.mark.parametrize("module,second", [
    (smart, "https://www.smart.md/ru/smartphone?page=2"),
    (cactus, "https://www.cactus.md/ru/catalogue/electronice/telefone/mobilnye-telefony/"
             "?sort_=ByView_Descending&page_=page_2"),
    (xstore, "https://xstore.md/ru/telefony/smartfony?page=2"),
    (darwin, "https://darwin.md/ru/telefoane/smartphone?page=2"),
    (enter, "https://enter.online/ru/telefony/smartfony?page=2"),
])
def test_pagination_stops_on_missing_page(module, second):
    code = module.STORE[0]
    requested, items = _page_urls(module, _page(code, "phones"))
    assert requested[0] == module.BASE_URL + module.CATEGORIES["Смартфоны"]
    assert requested[1] == second
    assert len(items) == len(_items(code, "phones"))


def test_pagination_stops_when_page_repeats():
    calls = []

    def handler(request):
        calls.append(str(request.url))
        return httpx.Response(200, text=_page("xstore", "phones"))

    fetcher = Fetcher(delay=0, check_robots=False,
                      client=httpx.Client(transport=httpx.MockTransport(handler)))
    items = list(xstore.scrape_category(fetcher, "Смартфоны", 10))
    assert len(calls) == 2
    assert len(items) == len(_items("xstore", "phones"))


@pytest.mark.parametrize("text,expected", [
    ("Laptop Lenovo V15 G4 AMN cu procesor AMD Ryzen™ 5 7520U pana la 4.3GHz, 15.6'' Full HD, "
     "16GB LPDDR5 RAM, 512GB SSD, AMD Radeon™ 610M Graphics",
     '15.6" | 16 ГБ | 512 ГБ | AMD Ryzen 5 7520U'),
    ("Lenovo LOQ Essential 15ARP11, 15.6'' Full HD, 16GB DDR5, 512GB SSD, NVIDIA GeForce RTX™ 5050 8GB GDDR7",
     '15.6" | 16 ГБ | 512 ГБ | NVIDIA GeForce RTX 5050'),
    ("Ноутбук Apple MacBook Pro 14.2\" 2025 (MDE14) M5,16Gb, 1TB Space Black",
     '14.2" | 16 ГБ | 1 ТБ | M5'),
    ("Ноутбук Dell Latitude 5350 13,3\" i7-1365U / 32GB/ 512GB / 2-in-1",
     '13.3" | 32 ГБ | 512 ГБ | Intel Core i7-1365U'),
    ('15.6" | 16 ГБ | 1 ТБ | AMD Ryzen 7 7445HS | GeForce RTX 3050 4 ГБ',
     '15.6" | 16 ГБ | 1 ТБ | AMD Ryzen 7 7445HS | GeForce RTX 3050'),
    ("Core Ultra 7 255U / 24 ГБ / 1 ТБ / VGA Встроенная / Серебряный",
     "24 ГБ | 1 ТБ | Core Ultra 7 255U"),
    ('16.2" / M4 Max (14C/32G) / 36GB RAM / 1TB SSD', '16.2" | 36 ГБ | 1 ТБ | M4 Max (14C/32G)'),
    ("Laptop Gaming 16'' HP OMEN MAX 16, Intel Core Ultra 9 275HX, 64GB/2048GB, FreeDOS",
     '16" | 64 ГБ | 2 ТБ | Intel Core Ultra 9 275HX'),
])
def test_laptop_details_from_free_text(text, expected):
    assert laptop_details(text) == expected


def test_laptop_details_are_understood_by_specs_parser():
    specs = parse_specs("Ноутбуки", laptop_details('16" / i7-14650HX / 16GB RAM / 1TB SSD / RTX5070'))
    assert (specs.ram, specs.storage, specs.screen, specs.cpu) == (16, 1024, 16.0, "i7 14650hx")
    apple = parse_specs("Ноутбуки", laptop_details("A18 Pro 6C/5G / 8 ГБ / 256 ГБ / VGA Встроенная"))
    assert (apple.ram, apple.storage, apple.cpu) == (8, 256, "a18 pro c6g5")


def test_cpu_names_from_new_stores_are_normalized():
    assert normalize_cpu("Apple M5 10C/8G") == normalize_cpu("M5 (10CPU/8GPU)") == "m5 c10g8"
    assert normalize_cpu("Apple M5 M5") == "m5"
    assert normalize_cpu("Qualcomm Snapdragon X1X1-26-100") == \
        normalize_cpu("Snapdragon X X1-26-100") == "snapdragon x1 26 100"
    assert same_cpu("a18 pro", "a18 pro c6g5")
    assert not same_cpu("m4 c10g8", "m4 c10g10")
    assert not same_cpu("m5", "m5 pro")


def test_brand_and_laptop_codes_for_new_title_styles():
    assert brand_from_title("iPhone 16e 128GB, Black") == "Apple"
    assert brand_from_title("Мобильный телефон iPhone 18 Pro Max 512Gb Burgundy") == "Apple"
    assert brand_from_title("Laptop Gaming ASUS TUF A16 FA607NUQ") == "ASUS"
    assert brand_from_title("Ноутбук Игровой Asus TUF Gaming A15 FA506NCG") == "ASUS"
    assert laptop_code("Dell Latitude 14 3450", "Dell") == "dell latitude 3450"
    assert laptop_code("Laptop DELL Latitude 3450 (N012L345014EMEA)", "Dell") == "dell latitude 3450"
    assert laptop_code('Ноутбук Apple MacBook Air 13.6" MC6C4 2025', "Apple") == \
        laptop_code('Laptop Apple MacBook Air 13" M4 16/512GB', "Apple") == "apple macbook air 13"


def _product(code: str, external_id: str) -> int:
    return conn.execute(
        "SELECT o.product_id FROM offers o JOIN stores s ON s.id = o.store_id "
        "WHERE s.code = ? AND o.external_id = ?", (code, external_id)
    ).fetchone()["product_id"]


def test_same_models_from_new_stores_become_one_product():
    now = "2026-11-18T12:00:00.000Z"
    with catalog.transaction():
        for code in NEW_STORES:
            store = catalog.get_or_create_store(*SCRAPERS[code].STORE)
            for kind, category in (("phones", "Смартфоны"), ("laptops", "Ноутбуки")):
                ingest.save_items(store, category, _items(code, kind), now)
    rematch()

    pro_max = {_product("cactus", "179214"), _product("smart", "29336855"),
               _product("xstore", "115429")}
    assert len(pro_max) == 1
    assert _product("cactus", "179205") != _product("cactus", "179214")

    assert _product("darwin", "170970") == _product("enter", "456614")
    assert _product("darwin", "172534") == _product("enter", "463021")
    assert _product("darwin", "172534") != _product("darwin", "172535")


def test_demo_cleanup_keeps_real_stores():
    for code in AUTOMATIC:
        catalog.get_or_create_store(*SCRAPERS[code].STORE)
    ingest.remove_demo_catalog()
    codes = {r["code"] for r in conn.execute("SELECT code FROM stores")}
    assert set(AUTOMATIC) <= codes


def test_pandashop_cards_use_properties_table():
    phones = {i.external_id: i for i in _items("pandashop", "phones")}
    a57 = phones["3486428"]
    assert a57.details == '8 ГБ / 256 ГБ | 6.7"'
    assert match_key("Смартфоны", a57.brand, a57.title) == "Смартфоны|galaxy a57|8/256gb"
    s25 = phones["3231282"]
    assert (s25.price, s25.old_price, s25.in_stock) == (20884, 22787, True)

    laptops = {i.external_id: i for i in _items("pandashop", "laptops")}
    tuf = laptops["3514574"]
    assert tuf.title == "Ноутбук Asus TUF Gaming A15 FA506NCQ Black"
    assert tuf.details == '15.6" | 16 ГБ | 512 ГБ | Ryzen 7 170 | RTX3050'
    nitro = laptops["3516878"]
    assert nitro.details.endswith("| 210H")
    assert parse_specs("Ноутбуки", nitro.details).cpu == "210h"
    assert pandashop.expand_cpu("R AI MAX+ 392") == "Ryzen AI MAX+ 392"
    assert pandashop.laptop_title("Ноутбук Hp HP 255R G10 (C68W9ET)") == "Ноутбук Hp 255R G10"


def test_bare_cpu_model_matches_full_name():
    assert same_cpu("210h", "5 210h")
    assert same_cpu("260", "ryzen 7 260")
    assert not same_cpu("210h", "i7 13620h")
    assert not same_cpu("pro", "a18 pro")


def test_redirect_loop_on_next_page_keeps_first_page():
    def handler(request):
        if "page_" in str(request.url):
            return httpx.Response(302, headers={"location": str(request.url)})
        return httpx.Response(200, text=_page("pandashop", "phones"))

    fetcher = Fetcher(delay=0, check_robots=False,
                      client=httpx.Client(transport=httpx.MockTransport(handler),
                                          follow_redirects=True))
    items = list(pandashop.scrape_category(fetcher, "Смартфоны", 5))
    assert len(items) == len(_items("pandashop", "phones"))


def test_pandashop_pages_are_requested_without_session_cookies():
    def handler(request):
        if "cookie" in request.headers:
            return httpx.Response(500)
        if "page_=page_2" in str(request.url):
            return httpx.Response(200, text=_page("pandashop", "laptops"))
        if "page_=page_3" in str(request.url):
            return httpx.Response(404)
        return httpx.Response(200, text=_page("pandashop", "phones"),
                              headers={"set-cookie": "ASP.NET_SessionId=abc; path=/"})

    fetcher = Fetcher(delay=0, check_robots=False,
                      client=httpx.Client(transport=httpx.MockTransport(handler)))
    items = list(pandashop.scrape_category(fetcher, "Смартфоны", 5))
    assert len(items) == len(_items("pandashop", "phones")) + len(_items("pandashop", "laptops"))


def test_redirect_loop_after_short_last_page_is_quiet(capsys):
    phones = _page("pandashop", "phones")
    short = phones.split('<div class="card js-itemsList-item"')
    last = short[0] + '<div class="card js-itemsList-item"' + short[1].replace(
        'data-product="', 'data-product="9', 1)

    def handler(request):
        url = str(request.url)
        if "page_=page_3" in url:
            return httpx.Response(302, headers={"location": url})
        if "page_=page_2" in url:
            return httpx.Response(200, text=last)
        return httpx.Response(200, text=phones)

    fetcher = Fetcher(delay=0, check_robots=False,
                      client=httpx.Client(transport=httpx.MockTransport(handler),
                                          follow_redirects=True))
    items = list(pandashop.scrape_category(fetcher, "Смартфоны", 5))
    assert len(items) == len(_items("pandashop", "phones")) + 1
    assert "внимание" not in capsys.readouterr().out


@pytest.mark.parametrize("title,expected", [
    ("Laptop ASUS Gaming 16'' ROG Strix G16 G615LW, Eclipse Gray, Intel Core Ultra 9 290HX, 32GB/1024GB",
     "ASUS ROG Strix G16 G615LW"),
    ("Laptop ASUS ROG Strix G16 FHD+ 16 inch AMD Ryzen 9 8940HX 16GB 512GB SSD RTX 5060",
     "ASUS ROG Strix G16"),
    ("Laptop Lenovo ThinkBook 14 G9 IRL Procesor Intel Core™ 5 210H 12M Cache", "Lenovo ThinkBook 14 G9 IRL"),
    ("Ultrabook Lenovo ThinkPad L16 Gen 2 Procesor Intel Core™ Ultra 5 225U", "Lenovo ThinkPad L16 Gen 2"),
    ("Workstation Dell Pro Max 16 Premium, Intel Core Ultra 7 265H, 32GB/1TB", "Dell Pro Max 16 Premium"),
    ("Laptop 16.0\" Dell Pro 16 PC16250, Intel Core Ultra 5 235U, 16GB/512GB", "Dell Pro 16 PC16250"),
])
def test_smart_laptop_model_is_cut_before_configuration(title, expected):
    assert smart.laptop_model(title) == expected


@pytest.mark.parametrize("title,expected", [
    ('Ноутбук 16.0" Dell Pro 16 PC16255 Ryzen 5 220 16/512Gb', "Ноутбук Dell Pro 16 PC16255"),
    ("Ноутбук ASUS 16.0 TUF Gaming A16 FA608PP", "Ноутбук ASUS TUF Gaming A16 FA608PP"),
    ("Ноутбук ASUS B9406CAA Core Ultra 7 356H 32/1Tb Win 11 Black", "Ноутбук ASUS B9406CAA"),
    ("Ноутбук Lenovo16IAX10H Core Ultra9 275HX 64/1TB RTX5090", "Ноутбук Lenovo 16IAX10H"),
])
def test_cactus_laptop_title_is_cleaned(title, expected):
    assert cactus.laptop_title(title) == expected


def test_cactus_skips_trackers_in_phone_list():
    html = _page("cactus", "phones").replace(
        "Мобильный телефон Apple iPhone 17 Pro 256Gb Silver", "Трекер Smart Cellularline Tracy")
    assert len(cactus.parse_listing(html, "Смартфоны")) == len(_items("cactus", "phones")) - 1


def test_enter_adds_brand_from_analytics():
    from app.scrapers.darwin import with_brand
    raw = '{"ecommerce":{"items":[{"item_brand":"Nomi"}]}}'
    assert with_brand("i5010", raw) == ("Nomi i5010", "Nomi")
    assert with_brand("Смартфон Apple iPhone 18 Pro", '{"ecommerce":{"items":[{"item_brand":"Apple"}]}}') == \
        ("Смартфон Apple iPhone 18 Pro", "Apple")


@pytest.mark.parametrize("a,b", [
    ("Смартфон Xiaomi X6 Белый 12/256GB", "Poco X6 12/256GB Blue"),
    ("Телефон Moto G57 Power 8/256 Pink", "Motorola Moto G57 Power 8/256GB"),
    ("Мобильный телефон Huawei Honor Magic 7 Lite 8/256GB", "Honor Magic 7 Lite 8/256GB"),
    ("OPPO A6х 4G 4/128GB Plum Purple", "OPPO A6X 4/128GB"),
    ("nubia Z80 Ultra 5G 16/512GB", "ZTE nubia Z80 Ultra 16/512GB"),
])
def test_phone_title_variants_share_a_key(a, b):
    assert match_key("Смартфоны", brand_from_title(a), a) == match_key("Смартфоны", brand_from_title(b), b)


def test_unlabelled_ram_next_to_ssd_and_gpu_memory():
    assert laptop_details("ASUS ROG Strix G16 16GB 512GB SSD RTX 5060") == "16 ГБ | 512 ГБ | RTX 5060"
    assert laptop_details("Ryzen 7 / 1TB SSD / RTX 5050 8GB") == "1 ТБ | RTX 5050"
    assert normalize_cpu("Core Ultra9 275HX") == normalize_cpu("Intel Core Ultra 9 275HX")
