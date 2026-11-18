import json

from app import catalog
from app.db import conn
from app.rematch import rematch

MAX_SPECS = "Procesor: {cpu} / Memoria operativă, GB: {ram} / Capacitate SSD, GB: {ssd} / Ecran, inch: {screen}"
ULTRA_SPECS = '{screen}" | IPS | {ram} ГБ | {ssd} ГБ | Intel Core {cpu}'


def _offers(rows, category="Ноутбуки"):
    maximum = catalog.get_or_create_store("maximum", "Maximum", "maximum.md")
    ultra = catalog.get_or_create_store("ultra", "Ultra", "ultra.md")
    stores = {"maximum": maximum, "ultra": ultra}
    for store, external_id, title, details in rows:
        product = catalog.create_product(title, "", category)
        catalog.upsert_offer(product, stores[store], external_id, 10000, title=title,
                             details=details)


def _product(external_id):
    return conn.execute(
        "SELECT p.* FROM offers o JOIN products p ON p.id = o.product_id WHERE o.external_id = ?",
        (external_id,),
    ).fetchone()


def test_laptops_with_same_model_merge_only_with_equal_configuration():
    _offers([
        ("maximum", "grp-1", "Laptop ASUS FZ999XY-RV002 TUF Gaming",
         MAX_SPECS.format(cpu="Core i5-13450HX", ram=16, ssd=512, screen="16")),
        ("ultra", "grp-2", "Игровой ноутбук ASUS TUF Gaming F16 FZ999XY Jaeger Gray",
         ULTRA_SPECS.format(screen=16, ram=16, ssd=512, cpu="i5-13450HX")),
        ("ultra", "grp-3", "Игровой ноутбук ASUS TUF Gaming F16 FZ999XY Jaeger Gray",
         ULTRA_SPECS.format(screen=16, ram=16, ssd=1024, cpu="i5-13450HX")),
        ("ultra", "grp-4", "Игровой ноутбук ASUS TUF Gaming F16 FZ999XY Mecha Gray",
         ULTRA_SPECS.format(screen=16, ram=16, ssd=512, cpu="i7-13650HX")),
    ])
    rematch()

    same = _product("grp-1")
    assert _product("grp-2")["id"] == same["id"]
    assert _product("grp-3")["id"] != same["id"]
    assert _product("grp-4")["id"] not in (same["id"], _product("grp-3")["id"])
    assert same["name"] == "ASUS TUF Gaming F16 FZ999XY · i5-13450HX, 16 ГБ / 512 ГБ"
    specs = json.loads(same["specs"])
    assert specs["Процессор"] in ("Core i5-13450HX", "Intel Core i5-13450HX")
    assert specs["Оперативная память"] == "16 ГБ" and specs["Накопитель"] == "512 ГБ"


def test_unknown_field_does_not_block_match_when_only_one_configuration():
    _offers([
        ("maximum", "grp-5", "Laptop ASUS FW888AB-QD049 Zenbook",
         MAX_SPECS.format(cpu="Core Ultra 5 225H", ram=16, ssd=512, screen="14")),
        ("ultra", "grp-6", "Ноутбук ASUS Zenbook 14 FW888AB Jade Black", ""),
    ])
    rematch()
    assert _product("grp-5")["id"] == _product("grp-6")["id"]


def test_offer_without_specs_is_not_guessed_between_two_configurations():
    _offers([
        ("ultra", "grp-7", "Ноутбук ASUS Vivobook 15 FV777CD Cool Silver",
         ULTRA_SPECS.format(screen=15.6, ram=8, ssd=512, cpu="i3-1315U")),
        ("ultra", "grp-8", "Ноутбук ASUS Vivobook 15 FV777CD Cool Silver",
         ULTRA_SPECS.format(screen=15.6, ram=16, ssd=512, cpu="i5-1335U")),
        ("maximum", "grp-9", "Laptop ASUS FV777CD-BQ982 VivoBook", ""),
    ])
    rematch()
    ids = {_product(e)["id"] for e in ("grp-7", "grp-8", "grp-9")}
    assert len(ids) == 3


def test_phone_screen_mismatch_splits_but_foldables_are_exempt():
    _offers([
        ("maximum", "grp-10", "Smartphone Zeta Z9 8/256GB Black",
         "Ecran, inch: 6,1 / Rezolutie ecran, pixeli: 2400x1080"),
        ("ultra", "grp-11", "Смартфон Zeta Z9 Чёрный 8/256GB", '8 ГБ / 256 ГБ | 6.8" | 120 Гц'),
        ("maximum", "grp-12", "Smartphone Zeta Fold 3 12/512GB Black",
         "Ecran, inch: 6,3 / Rezolutie ecran, pixeli: 2376x1060"),
        ("ultra", "grp-13", "Смартфон Zeta Fold 3 Чёрный 12/512GB", '12 ГБ / 512 ГБ | 8" | 120 Гц'),
    ], category="Смартфоны")
    rematch()
    assert _product("grp-10")["id"] != _product("grp-11")["id"]
    assert _product("grp-12")["id"] == _product("grp-13")["id"]


def test_macbooks_match_by_chip_cores_memory_and_storage():
    _offers([
        ("maximum", "grp-14", 'Laptop Apple MacBook Air 13" M9 10c/8g 16/512 GB Midnight MDXX4',
         MAX_SPECS.format(cpu="Apple M9", ram=16, ssd=512, screen="13,6")),
        ("ultra", "grp-15", "Ноутбук Apple MacBook Air 13 2030 Starlight",
         '13.6" | Liquid Retina | 16 ГБ | 512 ГБ | M9 (10CPU/8GPU)'),
        ("ultra", "grp-16", "Ноутбук Apple MacBook Air 13 2030 Starlight",
         '13.6" | Liquid Retina | 16 ГБ | 512 ГБ | M9 (10CPU/10GPU)'),
    ])
    rematch()
    assert _product("grp-14")["id"] == _product("grp-15")["id"]
    assert _product("grp-16")["id"] != _product("grp-14")["id"]
