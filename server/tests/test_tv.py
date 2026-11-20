import inspect
import json
from pathlib import Path

import pytest

from app import catalog, ingest, tv
from app.db import conn
from app.matching import brand_from_title, match_key
from app.rematch import rematch
from app.scrapers import SCRAPERS

FIXTURES = Path(__file__).parent / "fixtures"
STORES = ("pandashop", "ultra", "smart", "cactus", "xstore", "darwin", "enter")
TV = "Телевизоры"


def _items(code: str):
    html = (FIXTURES / ("%s_tvs.html" % code)).read_text(encoding="utf-8")
    parse = SCRAPERS[code].parse_listing
    if len(inspect.signature(parse).parameters) > 1:
        return parse(html, TV)
    return parse(html)


def _by_title(code: str, part: str):
    return next(i for i in _items(code) if part.lower() in i.title.lower())


def test_every_store_has_tv_category():
    for code in ("maximum",) + STORES:
        assert TV in SCRAPERS[code].CATEGORIES


@pytest.mark.parametrize("code", STORES)
def test_every_tv_card_is_parsed(code):
    items = _items(code)
    assert len(items) >= 6
    for item in items:
        assert item.external_id and item.title and item.price > 0
        assert item.url.startswith(SCRAPERS[code].BASE_URL)
        assert item.old_price is None or item.old_price > item.price
    assert len({i.external_id for i in items}) == len(items)


def test_brand_is_found_after_tv_words():
    assert brand_from_title('116" LED SMART Телевизор Hisense 116UXQ Черный') == "Hisense"
    assert brand_from_title('43" Nanocell SMART Телевизор LG 43NU800B6LC Черный') == "LG"
    assert brand_from_title("Televizor HI-QLED Hisense 109 cm 43'' 43A7S, Ultra HD 4K") == "Hisense"
    assert brand_from_title("Televizor LED Diamant by Horizon 55HL5530U/C, 139 cm") == "Diamant"
    assert brand_from_title("Телевизор KIVI 24H710QB") == "KIVI"
    assert brand_from_title("Телевизор Kivi 24H710QB Smart TV HD Ready Черный") == "KIVI"


def test_model_code_is_the_key():
    ultra = match_key(TV, "Hisense", '65" LED SMART Телевизор Hisense 65U7S PRO Черный')
    enter = match_key(TV, "Hisense", "Телевизор Hisense 65U7S PRO")
    assert ultra == enter == "Телевизоры|code|hisense 65u7s pro"
    assert match_key(TV, "Hisense", "Телевизор Hisense 65U7SE") != enter

    assert match_key(TV, "LG", "Телевизор LG OLED65G45LW Smart TV 4K Черный") == \
        match_key(TV, "LG", "Televizor LG OLED evo 65G45LW, 164 cm, Smart, 4K Ultra HD")
    assert match_key(TV, "Diamant", "Televizor LED Diamant 43HL5530U/C, 109 cm") == \
        "Телевизоры|code|diamant 43hl5530u"
    assert match_key(TV, "Vesta", "Телевизор Vesta WU4375AAD + MR20GA") == \
        "Телевизоры|code|vesta wu4375aad"


def test_region_and_variant_suffixes_are_ignored():
    assert match_key(TV, "Samsung", "Телевизор Samsung QE55QN70FAUXUA") == \
        match_key(TV, "Samsung", "Телевизор Samsung QE55QN70FAUXXH") == \
        "Телевизоры|code|samsung qe55qn70fa"
    assert match_key(TV, "Samsung", "Телевизор Samsung QE55Q7F5AUXUA") != \
        match_key(TV, "Samsung", "Телевизор Samsung QE55Q7FAAUXUA")
    assert match_key(TV, "LG", "Телевизор LG OLED55C54LA") == \
        match_key(TV, "LG", "Телевизор LG OLED55C5ELB") == "Телевизоры|code|lg 55c5"
    assert match_key(TV, "LG", "Телевизор LG 50UQ80006LA") == \
        match_key(TV, "LG", "Телевизор LG 50UQ80006LB") == "Телевизоры|code|lg 50uq8000"
    assert match_key(TV, "LG", "Телевизор LG 43QNED80A6A") != \
        match_key(TV, "LG", "Телевизор LG 43QNED80B6B")


def test_short_code_joins_the_only_longer_code():
    bases = ["Телевизоры|code|lg 65mrgb87b", "Телевизоры|code|tcl 55c6ks",
             "Телевизоры|code|samsung qe100qn80fa"]
    assert tv.aliases(match_key(TV, "LG", "Телевизор LG 65MRGB87"), bases) == [bases[0]]
    assert tv.aliases(match_key(TV, "Samsung", "Телевизор Samsung QE100QN80FUXUA"), bases) == \
        [bases[2]]
    assert tv.aliases(match_key(TV, "TCL", "Телевизор TCL 55C6K"), bases) == []


def test_tv_without_code_is_matched_by_model_and_diagonal():
    assert match_key(TV, "Xiaomi", 'Телевизор Xiaomi TV A Pro 43" 2026') == \
        match_key(TV, "Xiaomi", "Телевизор Xiaomi A Pro 2026 Smart TV 4K Черный", '43" | QLED | 4K') == \
        match_key(TV, "Xiaomi", '43" QLED SMART Телевизор Xiaomi A Pro 2026 Серый') == \
        "Телевизоры|model|xiaomi a pro 2026|43"
    assert match_key(TV, "Xiaomi", 'Телевизор Xiaomi TV A Pro 55" 2026') != \
        match_key(TV, "Xiaomi", 'Телевизор Xiaomi TV A Pro 43" 2026')


def test_diagonal_from_code_beats_card_attributes():
    assert tv.diagonal("Телевизор Hisense 50E7S Pro Smart TV 4K Черный", '55" | QLED | 4K',
                       "Hisense") == 50
    assert tv.diagonal("Телевизор Xiaomi TV S 2025 Smart TV 4K Черный", '65" | MiniLED | 4K',
                       "Xiaomi") == 65
    assert tv.diagonal("Televizor TCL QLED 55P8L, 139 cm, Smart Google TV", "", "TCL") == 55
    assert tv.diagonal("Телевизор Xiaomi TV S 65 2025", "", "Xiaomi") == 65
    assert tv.diagonal("Televizor Xiaomi Mini LED S Mini, 189 cm, Smart Google TV", "",
                       "Xiaomi") == 75


def test_year_less_title_joins_the_only_matching_model():
    bases = ["Телевизоры|model|xiaomi s 2025|55", "Телевизоры|model|xiaomi s 2025|65"]
    assert tv.aliases("Телевизоры|model|xiaomi s|55", bases) == [bases[0]]
    assert tv.aliases("Телевизоры|model|xiaomi s|75", bases) == []
    assert tv.aliases(bases[0], bases) == []


def test_tv_specs_from_every_kind_of_card():
    ultra = tv.parse_specs('116" LED SMART Телевизор Hisense 116UXQ Черный',
                           "3840x2160 px | 165 Гц | 80 Вт | VIDAA", "Hisense")
    assert ultra.display == {"Экран": '116"', "Разрешение": "4K Ultra HD", "Матрица": "LED",
                             "Частота экрана": "165 Гц", "Smart-платформа": "VIDAA"}

    smart = tv.parse_specs("Televizor TCL QD-MiniLed 50C6K, 126 cm, Smart Google TV, 4K Ultra HD, "
                           "100Hz, Clasa E (Model 2025)", "", "TCL")
    assert smart.display["Матрица"] == "Mini LED"
    assert smart.display["Smart-платформа"] == "Google TV"
    assert smart.display["Экран"] == '50"'

    panda = tv.parse_specs("Телевизор Vesta LD43M5045",
                           'диагональ экрана: 43 " / разрешение: (FHD) 1920x1080 / '
                           "частота обновления экрана: 60 Гц / тип операционной системы: Android TV",
                           "Vesta")
    assert panda.display == {"Экран": '43"', "Разрешение": "Full HD", "Частота экрана": "60 Гц",
                             "Smart-платформа": "Android TV"}

    assert tv.parse_specs("Телевизор LG OLED55C54LA").display["Матрица"] == "OLED"
    assert tv.parse_specs("Телевизор Samsung MRE65R85HAUXUA", "75\" / Micro RGB / 4K") \
        .display["Матрица"] == "Micro RGB"


def _product(code: str, external_id: str) -> int:
    return conn.execute(
        "SELECT o.product_id FROM offers o JOIN stores s ON s.id = o.store_id "
        "WHERE s.code = ? AND o.external_id = ?", (code, external_id)
    ).fetchone()["product_id"]


def test_same_tvs_from_different_stores_become_one_product():
    now = "2026-11-20T12:00:00.000Z"
    with catalog.transaction():
        for code in STORES:
            store = catalog.get_or_create_store(*SCRAPERS[code].STORE)
            ingest.save_items(store, TV, _items(code), now)
    rematch()

    hisense = {_product(code, _by_title(code, "65U7S PRO").external_id) for code in ("ultra", "enter")}
    assert len(hisense) == 1

    xiaomi_s = {_product(code, _by_title(code, part).external_id) for code, part in (
        ("pandashop", "TV S Mini LED 55"), ("xstore", 'S Mini 55"'), ("ultra", "Xiaomi S 2025"),
    )}
    assert len(xiaomi_s) == 1

    row = conn.execute("SELECT name, specs FROM products WHERE id = ?", (hisense.pop(),)).fetchone()
    assert row["name"] == "Hisense 65U7S Pro"
    assert json.loads(row["specs"])["Экран"] == '65"'

    row = conn.execute("SELECT name FROM products WHERE id = ?", (xiaomi_s.pop(),)).fetchone()
    assert row["name"] == 'Xiaomi TV S 2025 55"'
