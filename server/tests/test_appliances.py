import json
import re
from pathlib import Path

import httpx

from app import appliances, catalog, codes, ingest
from app.db import conn
from app.matching import brand_from_title, match_key
from app.rematch import rematch
from app.scrapers import cactus, darwin, enter, maximum, pandashop, smart, ultra, xstore
from app.scrapers.base import Fetcher

FIXTURES = Path(__file__).parent / "fixtures"
PAGES = {
    appliances.WASHERS: "washers",
    appliances.FRIDGES: "fridges",
    appliances.VACUUMS: "vacuums",
    appliances.MICROWAVES: "microwaves",
}


def _page(category: str) -> str:
    return (FIXTURES / ("maximum_%s.html" % PAGES[category])).read_text(encoding="utf-8")


def _items(category: str):
    return {i.external_id: i for i in maximum.parse_listing(_page(category))}


def test_maximum_has_every_appliance_category():
    for category in appliances.CATEGORIES:
        assert category in maximum.CATEGORIES
    assert len(maximum.CATEGORIES[appliances.VACUUMS]) == 7


def test_russian_maximum_cards_are_parsed():
    washers = _items(appliances.WASHERS)
    lg = washers["6462752"]
    assert lg.title == "Стиральная машина с фронтальной загрузкой LG F2WV3S7S3E"
    assert lg.brand == "LG"
    assert (lg.price, lg.old_price, lg.in_stock) == (7999, 9499, True)
    assert lg.url == "https://maximum.md/ru/6462752/"
    assert lg.details.startswith("Максимальная загрузка, кг: 7")
    for category in appliances.CATEGORIES:
        for item in _items(category).values():
            assert item.price > 0 and item.brand and item.url.startswith(maximum.BASE_URL)


def test_one_category_is_collected_from_several_sections_without_duplicates():
    fridges = _page(appliances.FRIDGES)
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request.url.path)
        if request.url.path.endswith("-kameroj/") or request.url.path.endswith("odnodvernye/"):
            return httpx.Response(200, text=fridges)
        if request.url.path.endswith("french-door/"):
            return httpx.Response(200, text=fridges)
        return httpx.Response(404)

    fetcher = Fetcher(delay=0, check_robots=False,
                      client=httpx.Client(transport=httpx.MockTransport(handler)))
    items = list(maximum.scrape_category(fetcher, appliances.FRIDGES))

    assert len(items) == len(_items(appliances.FRIDGES))
    assert sum(1 for r in requests if not r.rstrip("/").split("/")[-1].isdigit()) == 4


def test_accessories_and_wine_coolers_are_not_appliances():
    assert not appliances.belongs(appliances.FRIDGES, "Винный холодильник Haier HWS77GDAU1")
    assert not appliances.belongs(appliances.VACUUMS, "Док-станция Mova G70 Station Черный")
    assert not appliances.belongs(appliances.WASHERS, "Сушильная машина Bosch WQB245B0BY")
    assert appliances.belongs(appliances.VACUUMS, "Пылесос с аквафильтром Thomas Aqua+")
    assert appliances.belongs(appliances.FRIDGES,
                              "Холодильник Whirlpool WHSD18A013C1 без морозильной камеры")


def test_brand_after_fridge_type_words():
    assert brand_from_title("Холодильник SideBySide Whirlpool WQ9M2L") == "Whirlpool"


def test_appliance_keys_use_model_codes():
    assert match_key(appliances.FRIDGES, "Liebherr", "Холодильник SideBySide Liebherr Msdd 9012") == \
        match_key(appliances.FRIDGES, "Liebherr", "Холодильник Liebherr MSDD9012") == \
        "Холодильники|code|liebherr msdd9012"
    assert match_key(appliances.FRIDGES, "LG", "Холодильник LG GW-B509SQKM DoorCooling+") == \
        match_key(appliances.FRIDGES, "LG", "Холодильник LG GWB509SQKM") == \
        "Холодильники|code|lg gwb509sqkm"
    assert match_key(appliances.VACUUMS, "Samsung", "Пылесос Samsung VC18M31C0HG/UK") == \
        "Пылесосы|code|samsung vc18m31c0hg"
    assert match_key(appliances.WASHERS, "Indesit",
                     "Стиральная машина Indesit BTWD51052(EU)") == \
        "Стиральные машины|code|indesit btwd51052"
    assert match_key(appliances.MICROWAVES, "Panasonic", "Микроволновая печь Panasonic NN-ST35MKZPE") \
        == "Микроволновки|code|panasonic nnst35mkzpe"


def test_codes_split_by_spaces_are_joined():
    assert match_key(appliances.MICROWAVES, "Gorenje", "Микроволновая печь Gorenje BM 235 CLB Черный") \
        == match_key(appliances.MICROWAVES, "Gorenje", "Микроволновая печь Gorenje BM235CLB") == \
        "Микроволновки|code|gorenje bm235clb"
    assert match_key(appliances.WASHERS, "Hotpoint-Ariston",
                     "Стиральная машина Hotpoint-Ariston NM11 847 WS A EU Белый") == \
        "Стиральные машины|code|hotpoint-ariston nm11847ws"
    assert match_key(appliances.MICROWAVES, "Gorenje", "Микроволновая печь Gorenje BM 251 SG2WG") \
        == "Микроволновки|code|gorenje bm251sg2wg"
    assert match_key(appliances.VACUUMS, "Mova", "Робот-Пылесос Mova E50 Pro Ultra Белый") == \
        "Пылесосы|model|mova e50proultra|-"


def test_appliances_without_code_keep_model_words_but_not_colours():
    black = match_key(appliances.VACUUMS, "Roborock", "Пылесос робот Roborock Q10 VF Black")
    white = match_key(appliances.VACUUMS, "Roborock", "Пылесос робот Roborock Q10 VF White")
    assert black == white == "Пылесосы|code|roborock q10vf"
    assert match_key(appliances.VACUUMS, "Dreame", "Робот-Пылесос Dreame Matrix 10 Ultra Черный") \
        == match_key(appliances.VACUUMS, "Dreame", "Робот-Пылесос Dreame Matrix 10 Ultra Белый") \
        == "Пылесосы|model|dreame matrix10ultra|-"
    assert match_key(appliances.VACUUMS, "Dreame", "Пылесос робот Dreame X50 Ultra") != \
        match_key(appliances.VACUUMS, "Dreame", "Пылесос робот Dreame X50 Ultra Complete")
    assert match_key(appliances.VACUUMS, "Xiaomi", "Пылесос робот Xiaomi 5 Pro EU") == \
        "Пылесосы|model|xiaomi 5pro|-"


def test_spelling_variants_of_robot_names_match():
    pairs = [
        ("Робот-пылесос Roborock QRevo Curv2 FlowX, White",
         "Робот-пылесос Roborock Q Revo Curv 2 Flow X, White"),
        ("Робот пылесос Roborock S7 MaxV Plus", "Робот-Пылесос Roborock S7 Max V Plus Черный"),
        ("Робот пылесос Roborock Q5 Pro Plus", "Робот-Пылесос Roborock Q5 Pro+ Черный"),
        ("Вертикальный пылесос MIELE Triflex HX2 Cat & Dog Obsidian Black",
         "Aspirator vertical Miele Triflex HX2 CatDog, 3 in 1, 25,2 V"),
        ("Вертикальный пылесос Karcher LVS 1/1 Bp (1.394-110.0)",
         "Пылесос беспроводной Karcher 1.394-110.0 LVS 1/1 Bp"),
        ("Робот-пылесос BOSCH BCRDW3BX", "Robot de aspirare Bosch Spotless Max BCRDW3BX, 5.700 mAh"),
    ]
    for a, b in pairs:
        assert match_key(appliances.VACUUMS, brand_from_title(a), a) == \
            match_key(appliances.VACUUMS, brand_from_title(b), b), (a, b)
    assert match_key(appliances.VACUUMS, "Roborock", "Робот пылесос Roborock S7 MaxV") != \
        match_key(appliances.VACUUMS, "Roborock", "Робот пылесос Roborock S7 MaxV Plus")


def test_bundled_detergent_is_not_the_model():
    assert match_key(appliances.VACUUMS, "Karcher",
                     "Моющий пылесос KARCHER SE 2 Spot Pure+ RM519 6.295-771.0") == \
        match_key(appliances.VACUUMS, "Karcher",
                  "Пылесос моющий Karcher SE 2 Spot Pure+ Detergent p/u covoare 1L RM 519")
    assert match_key(appliances.VACUUMS, "Karcher", "Моющий пылесос KARCHER SE5 + RM519") != \
        match_key(appliances.VACUUMS, "Karcher", "Моющий пылесос KARCHER SE 2 Spot Pure+ RM519")


def test_region_letters_join_the_only_longer_code():
    bases = ["Стиральные машины|code|beko b3wfu49215wwes", "Телевизоры|code|tcl 55c6ks"]
    assert codes.aliases("Стиральные машины|code|beko b3wfu49215ww", bases) == [bases[0]]
    assert codes.aliases("Телевизоры|code|tcl 55c6k", bases) == []


def test_appliance_specs():
    washer = appliances.parse_specs(
        appliances.WASHERS, "Стиральная машина с фронтальной загрузкой LG F2WV3S7S3E",
        "Максимальная загрузка, кг: 8,5 / Макс. скорость отжима, об/мин: 1200 / "
        "Класс энергопотребления: A (A-G)")
    assert washer.display == {"Загрузка белья": "Фронтальная", "Загрузка": "8,5 кг",
                              "Отжим": "1200 об/мин", "Класс энергопотребления": "A"}

    fridge = appliances.parse_specs(
        appliances.FRIDGES, "Холодильник с нижней морозильной камерой Beko RCNE720E30DXPN",
        "Общий полезный объём, л: 586 / Объём холодильной камеры, л: 426 / "
        "Система охлаждения и разморозки мор. камеры: NeoFrost")
    assert fridge.display == {"Тип": "С нижней морозильной камерой", "Общий объём": "586 л",
                              "Разморозка": "No Frost"}

    robot = appliances.parse_specs(
        appliances.VACUUMS, "Пылесос робот Hobot Legee D8",
        "Мощность всасывания, Па: 5000 / Время работы от аккумулятора, минут: 180")
    assert robot.display == {"Тип": "Робот", "Мощность всасывания": "5000 Па",
                             "Время работы": "180 мин"}

    oven = appliances.parse_specs(
        appliances.MICROWAVES, "Микроволновая печь Gorenje MO20S4W",
        "Тип: с грилем / Объём камеры, л: 20 / Мощность микроволн, Вт: 800 / Мощность гриля, Вт: 1000")
    assert oven.display == {"Тип": "С грилем", "Объём": "20 л", "Мощность": "800 Вт"}


def _product(external_id: str):
    return conn.execute(
        "SELECT p.id, p.name, p.specs FROM offers o JOIN products p ON p.id = o.product_id "
        "JOIN stores s ON s.id = o.store_id WHERE s.code = 'maximum' AND o.external_id = ?",
        (external_id,),
    ).fetchone()


def test_colour_variants_become_one_product_with_specs():
    store = catalog.get_or_create_store(*maximum.STORE)
    with catalog.transaction():
        for category in appliances.CATEGORIES:
            ingest.save_items(store, category, list(_items(category).values()),
                              "2026-11-20T12:00:00.000Z")
    rematch()

    black, white = _product("6938075"), _product("6938074")
    assert black["id"] == white["id"]
    assert black["name"] == "Roborock Q10 VF"
    assert json.loads(black["specs"])["Тип"] == "Робот"

    lg = _product("6462752")
    assert lg["name"] == "LG F2WV3S7S3E"
    assert json.loads(lg["specs"])["Отжим"] == "1200 об/мин"


_WORDS = {
    appliances.WASHERS: "стиральн", appliances.FRIDGES: "холодильн",
    appliances.VACUUMS: "пылесос|док-станц", appliances.MICROWAVES: "микроволнов",
}


def _store_items(module, category):
    html = (FIXTURES / ("%s_appliances.html" % module.STORE[0])).read_text(encoding="utf-8")
    items = enter.parse_listing(html, category) if module is enter else module.parse_listing(html)
    return [i for i in items if re.search(_WORDS[category], i.title, re.IGNORECASE)]


def test_ultra_and_enter_have_every_appliance_category():
    for module in (ultra, enter):
        for category in appliances.CATEGORIES:
            assert module.CATEGORIES[category].startswith("/ru/")


def test_enter_appliance_cards_keep_description_as_details():
    washer = next(i for i in _store_items(enter, appliances.WASHERS) if "WIW24342EU" in i.title)
    assert washer.details.startswith("8 кг / 1200 об/мин")
    specs = appliances.parse_specs(appliances.WASHERS, washer.title, washer.details)
    assert specs.display == {"Загрузка": "8 кг", "Отжим": "1200 об/мин"}


def test_ultra_specs_from_card_segments():
    oven = next(i for i in _store_items(ultra, appliances.MICROWAVES) if "SG2WG" in i.title)
    specs = appliances.parse_specs(appliances.MICROWAVES, oven.title, oven.details)
    assert specs.display == {"Установка": "Встраиваемая", "Объём": "25 л", "Мощность": "900 Вт"}


def _offer_product(code: str, external_id: str) -> int:
    return conn.execute(
        "SELECT o.product_id FROM offers o JOIN stores s ON s.id = o.store_id "
        "WHERE s.code = ? AND o.external_id = ?", (code, external_id)
    ).fetchone()["product_id"]


def test_same_appliances_from_ultra_and_enter_become_one_product():
    now = "2026-11-20T13:00:00.000Z"
    with catalog.transaction():
        for module in (ultra, enter):
            store = catalog.get_or_create_store(*module.STORE)
            for category in appliances.CATEGORIES:
                ingest.save_items(store, category, _store_items(module, category), now)
    rematch()

    assert _offer_product("ultra", "147138") == _offer_product("enter", "88312")
    assert _offer_product("ultra", "243814") == _offer_product("ultra", "243813") == \
        _offer_product("enter", "459307")
    stored = {(r["code"], r["external_id"]) for r in conn.execute(
        "SELECT s.code, o.external_id FROM offers o JOIN stores s ON s.id = o.store_id")}
    assert ("enter", "248589") not in stored
    assert ("ultra", "247725") not in stored


def test_darwin_and_xstore_appliance_sections():
    for category in appliances.CATEGORIES:
        assert darwin.CATEGORIES[category].startswith("/ru/bytovaya-tehnika/")
    assert xstore.CATEGORIES[appliances.VACUUMS] == "/ru/roboty-pylesosy"


def test_darwin_fridge_volume_is_sum_of_chambers():
    html = (FIXTURES / "darwin_appliances.html").read_text(encoding="utf-8")
    fridge = next(i for i in darwin.parse_listing(html, appliances.FRIDGES)
                  if "RB38C676DSA" in i.title)
    specs = appliances.parse_specs(appliances.FRIDGES, fridge.title, fridge.details)
    assert specs.display["Общий объём"] == "390 л"
    assert specs.display["Разморозка"] == "No Frost"
    oven = next(i for i in darwin.parse_listing(html, appliances.MICROWAVES)
                if "NQ50T9539BD" in i.title)
    assert appliances.parse_specs(appliances.MICROWAVES, oven.title, oven.details).display == \
        {"Тип": "С конвекцией", "Объём": "50 л", "Мощность": "850 Вт"}


def test_xstore_robot_names_match_other_stores():
    html = (FIXTURES / "xstore_appliances.html").read_text(encoding="utf-8")
    robots = {i.external_id: i for i in xstore.parse_listing(html, appliances.VACUUMS)}
    s40c = robots["135328"]
    assert match_key(appliances.VACUUMS, s40c.brand, s40c.title, s40c.details) == \
        match_key(appliances.VACUUMS, "Xiaomi", "Пылесос робот Xiaomi S40C EU")
    curv = robots["76576"]
    assert match_key(appliances.VACUUMS, curv.brand, curv.title) == \
        "Пылесосы|model|roborock qrevocurv|-"
    assert appliances.parse_specs(appliances.VACUUMS, s40c.title, s40c.details) \
        .display["Мощность всасывания"] == "5000 Па"


def _fixture_items(module, category):
    html = (FIXTURES / ("%s_appliances.html" % module.STORE[0])).read_text(encoding="utf-8")
    return {i.external_id: i for i in module.parse_listing(html, category)}


def test_cactus_pandashop_smart_appliance_sections():
    for module in (cactus, pandashop, smart):
        for category in appliances.CATEGORIES:
            assert module.CATEGORIES[category].startswith("/ru/")


def test_romanian_smart_titles_get_real_brands_and_specs():
    items = _fixture_items(smart, appliances.FRIDGES)
    combi = items["26754457"]
    assert combi.brand == "Bosch"
    assert match_key(appliances.FRIDGES, combi.brand, combi.title) == "Холодильники|code|bosch kgn39vweq"
    specs = appliances.parse_specs(appliances.FRIDGES, combi.title, combi.details)
    assert specs.display == {"Общий объём": "368 л", "Разморозка": "No Frost"}
    assert items["29367107"].brand == "Samsung"
    robot = items["29408485"]
    assert match_key(appliances.VACUUMS, robot.brand, robot.title) == "Пылесосы|model|xiaomi h40|-"
    assert not appliances.belongs(appliances.FRIDGES, items["25388626"].title)
    assert not appliances.belongs(appliances.FRIDGES, items["24859551"].title)
    assert not appliances.belongs(appliances.MICROWAVES, items["24437836"].title)
    oven = items["25387749"]
    assert appliances.parse_specs(appliances.MICROWAVES, oven.title, oven.details).display == \
        {"Объём": "20 л", "Мощность": "700 Вт"}


def test_cactus_features_become_details():
    items = _fixture_items(cactus, appliances.WASHERS)
    bosch = items["202218"]
    assert bosch.brand == "Bosch"
    specs = appliances.parse_specs(appliances.WASHERS, bosch.title, bosch.details)
    assert specs.display["Загрузка"] == "8 кг" and specs.display["Отжим"] == "1400 об/мин"
    fridges = _fixture_items(cactus, appliances.FRIDGES)
    assert not appliances.belongs(appliances.FRIDGES, fridges["199188"].title)
    assert match_key(appliances.FRIDGES, "Liebherr", fridges["202263"].title) == \
        "Холодильники|code|liebherr xrfsf5225"


def test_pandashop_properties_become_details():
    items = _fixture_items(pandashop, appliances.MICROWAVES)
    oven = items["2564854"]
    assert appliances.parse_specs(appliances.MICROWAVES, oven.title, oven.details).display == \
        {"Тип": "Соло", "Объём": "23 л", "Мощность": "800 Вт"}
    assert items["2531668"].brand == "Black+Decker"
    assert match_key(appliances.MICROWAVES, oven.brand, oven.title) == \
        match_key(appliances.MICROWAVES, "Samsung", "Микроволновая печь Samsung MS23K3513AS/OL")
