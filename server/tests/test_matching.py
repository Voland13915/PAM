import pytest

from app import catalog
from app.db import conn
from app.matching import display_name, match_key, trimmed_keys
from app.rematch import rematch

SAME = [
    ("Смартфоны", "Apple", "Smartphone Apple iPhone 15 128GB Black MTP03",
     "Apple", "Смартфон Apple iPhone 15 Черный 6/128GB"),
    ("Смартфоны", "Apple", "Smartphone Apple iPhone Duo 256GB Star White MK2D4",
     "Apple", "Смартфон Apple iPhone Duo Star White 12/256GB"),
    ("Смартфоны", "Apple", "Smartphone Apple iPhone 17 Pro 1TB Deep Blue MG8R4",
     "Apple", "Смартфон Apple iPhone 17 Pro Glacier 12/1024GB"),
    ("Смартфоны", "Samsung", "Smartphone Samsung A175 Galaxy A17 LTE 8/256GB Blue",
     "Samsung", "Смартфон Samsung Galaxy A17 Синий 8/256GB"),
    ("Смартфоны", "Xiaomi", "Smartphone Xiaomi Redmi Note 17 Pro 5G 6/256GB Black",
     "Xiaomi", "Смартфон Xiaomi Redmi Note 17 Pro Черный 6/256GB"),
    ("Смартфоны", "Poco", "Smartphone Poco F8 Ultra 16/512GB Black",
     "Xiaomi", "Смартфон Xiaomi Poco F8 Ultra Черный 16/512GB"),
    ("Смартфоны", "Samsung", "Smartphone Samsung F761 Flip7 FE 5G 8/128GB Black",
     "Samsung", "Смартфон Samsung Galaxy Flip 7 FE Чёрный 8/128GB"),
    ("Смартфоны", "Samsung", "Smartphone Samsung S936 Galaxy S25 Plus 12/256GB Blue Black",
     "Samsung", "Смартфон Samsung Galaxy S25+ Ice Blue 12/256GB"),
    ("Смартфоны", "Poco", "Smartphone Poco M8Pro 5G 8/256GB Black",
     "Xiaomi", "Смартфон Xiaomi Poco M8 Pro Черный 8/256GB"),
    ("Ноутбуки", "ASUS", "Laptop ASUS FA608UMI-TU211 TUF Gaming",
     "ASUS", "Игровой ноутбук ASUS TUF Gaming A16 FA608UMI Jaeger Gray"),
    ("Ноутбуки", "Lenovo", "Laptop Lenovo LOQ 15IAX9 Luna Grey (83GS005CRK)",
     "Lenovo", "Игровой ноутбук Lenovo LOQ 15IAX9 Luna Grey"),
    ("Ноутбуки", "Dell", "Laptop Dell DC16250_RPLU-R_010",
     "DELL", "Ноутбук DELL 16 DC16250 Black"),
]

DIFFERENT = [
    ("Смартфоны", "Apple", "Smartphone Apple iPhone 15 128GB Black MTP03",
     "Apple", "Smartphone Apple iPhone 15 256GB Black MTP43"),
    ("Смартфоны", "Apple", "Smartphone Apple iPhone 18 Pro 256GB Silver",
     "Apple", "Smartphone Apple iPhone 18 Pro Max 256GB Silver"),
    ("Смартфоны", "Apple", "Smartphone Apple iPhone 14 128GB Blue {Ref.}",
     "Apple", "Smartphone Apple iPhone 14 128GB Blue MPVN3"),
    ("Смартфоны", "Apple", "Smartphone Apple iPhone 13 Pro 128 GB Silver {Grade B} Refurb.",
     "Apple", "Смартфон Apple iPhone 13 Pro Серебристый 6/128GB"),
    ("Смартфоны", "Xiaomi", "Smartphone Xiaomi Redmi Note 17 4/128GB Purple",
     "Xiaomi", "Smartphone Xiaomi Redmi Note 17 6/128GB Purple"),
    ("Ноутбуки", "Lenovo", "Laptop Lenovo IdeaPad Slim 3 16IRH10 (83K2000WRK)",
     "Lenovo", "Ноутбук Lenovo IdeaPad Slim 5 16IRH10 Luna Grey"),
]


@pytest.mark.parametrize("category,brand_a,title_a,brand_b,title_b", SAME)
def test_same_product_in_two_stores(category, brand_a, title_a, brand_b, title_b):
    assert match_key(category, brand_a, title_a) == match_key(category, brand_b, title_b)


@pytest.mark.parametrize("category,brand_a,title_a,brand_b,title_b", DIFFERENT)
def test_different_products_stay_apart(category, brand_a, title_a, brand_b, title_b):
    assert match_key(category, brand_a, title_a) != match_key(category, brand_b, title_b)


def test_examples_of_keys():
    assert match_key("Смартфоны", "Apple", "Смартфон Apple iPhone 18 Pro Max Серебристый 12/512GB") \
        == "Смартфоны|iphone 18 pro max|512gb"
    assert match_key("Смартфоны", "Apple", "Smartphone Apple iPhone 14 256GB Midnight {Ref.}") \
        == "Смартфоны|iphone 14|256gb|ref"
    assert match_key("Ноутбуки", "Acer", "Laptop Acer Aspire 3 A315-24PT-R288 (NX.JK5AA.001)") \
        == "Ноутбуки|code|acer a315-24pt"
    assert match_key("Ноутбуки", "ASUS", "Laptop ASUS FA608UMI-TU211 TUF Gaming") \
        == "Ноутбуки|code|asus fa608umi"
    assert match_key("Ноутбуки", "Apple",
                     'Laptop Apple MacBook Air 13" M5 10c/10g 16/1TB Midnight MDHF4') \
        == "Ноутбуки|code|apple macbook air 13"


def test_rematch_merges_products_and_moves_wishlist(client):
    maximum = catalog.get_or_create_store("maximum", "Maximum", "maximum.md")
    ultra = catalog.get_or_create_store("ultra", "Ultra", "ultra.md")
    user = conn.execute("SELECT id FROM users LIMIT 1").fetchone()["id"]

    a = catalog.create_product("Apple iPhone 16e 128GB Black", "Apple", "Смартфоны",
                               match_key="old-key-a")
    b = catalog.create_product("Apple iPhone 16e Черный", "Apple", "Смартфоны",
                               match_key="old-key-b")
    catalog.upsert_offer(a, maximum, "rm-1", 11999, title="Smartphone Apple iPhone 16e 128GB Black MD1Q4")
    catalog.upsert_offer(b, ultra, "rm-2", 11799, title="Смартфон Apple iPhone 16e Черный 8/128GB")
    conn.execute(
        "INSERT INTO wishlist (user_id, product_id, store_id, target_price, created_at) "
        "VALUES (?, ?, ?, 11000, '2026-11-18T10:00:00.000Z')",
        (user, b, ultra),
    )

    stats = rematch()

    owners = {r["product_id"] for r in conn.execute(
        "SELECT product_id FROM offers WHERE external_id IN ('rm-1', 'rm-2')")}
    assert owners == {a}
    assert conn.execute("SELECT 1 FROM products WHERE id = ?", (b,)).fetchone() is None
    assert conn.execute(
        "SELECT product_id FROM wishlist WHERE store_id = ? AND target_price = 11000", (ultra,)
    ).fetchone()["product_id"] == a
    assert conn.execute("SELECT match_key FROM products WHERE id = ?", (a,)).fetchone()[0] \
        == "Смартфоны|iphone 16e|128gb"
    assert stats["moved"] >= 1

    again = rematch()
    assert again["moved"] == 0 and again["removed"] == 0


def test_trimming_removes_colour_words_but_not_model_words():
    assert trimmed_keys("Смартфоны|galaxy a36 lavander|128gb") == ["Смартфоны|galaxy a36|128gb"]
    assert trimmed_keys("Смартфоны|motorola edge 60 fusion pantone slipstream|256gb")[:2] == [
        "Смартфоны|motorola edge 60 fusion pantone|256gb",
        "Смартфоны|motorola edge 60 fusion|256gb",
    ]
    assert trimmed_keys("Смартфоны|galaxy a03 core|32gb") == []
    assert trimmed_keys("Смартфоны|iphone 18 pro max|512gb") == []


def test_display_name_drops_colour_and_codes():
    assert display_name("Smartphone Xiaomi 15T Pro 12/1024GB Black") == "Xiaomi 15T Pro 12/1024GB"
    assert display_name("Смартфон Xiaomi 17T Pro Deep Blue 12/1024GB") == "Xiaomi 17T Pro 12/1024GB"
    assert display_name("Smartphone Apple iPhone 14 128GB Blue {Ref.}") \
        == "Apple iPhone 14 128GB (восстановленный)"
    assert display_name("Smartphone Apple iPhone 13 Pro 128 GB Gold {Grade A} Refurb.") \
        == "Apple iPhone 13 Pro 128GB (восстановленный)"


def _offer_ids(*external_ids):
    return {r["external_id"]: r["product_id"] for r in conn.execute(
        "SELECT external_id, product_id FROM offers WHERE external_id IN (%s)"
        % ",".join("?" * len(external_ids)), external_ids)}


def test_ram_is_ignored_when_one_store_omits_it_and_kept_when_variants_differ():
    maximum = catalog.get_or_create_store("maximum", "Maximum", "maximum.md")
    ultra = catalog.get_or_create_store("ultra", "Ultra", "ultra.md")
    offers = [
        (maximum, "ram-1", "Samsung", "Smartphone Samsung A366 Galaxy A36 5G 128GB White"),
        (ultra, "ram-2", "Samsung", "Смартфон Samsung Galaxy A36 Awesome Black 6/128GB"),
        (ultra, "ram-3", "Samsung", "Смартфон Samsung Galaxy A36 Lavander 6/128GB"),
        (maximum, "ram-4", "Xiaomi", "Smartphone Xiaomi Redmi Note 99 4/128GB Black"),
        (ultra, "ram-5", "Xiaomi", "Смартфон Xiaomi Redmi Note 99 Черный 6/128GB"),
    ]
    for store, external_id, brand, title in offers:
        product = catalog.create_product(title, brand, "Смартфоны")
        catalog.upsert_offer(product, store, external_id, 5000, title=title)

    rematch()

    ids = _offer_ids("ram-1", "ram-2", "ram-3", "ram-4", "ram-5")
    assert ids["ram-1"] == ids["ram-2"] == ids["ram-3"]
    assert ids["ram-4"] != ids["ram-5"]
    name = conn.execute("SELECT name FROM products WHERE id = ?", (ids["ram-1"],)).fetchone()[0]
    assert name == "Samsung Galaxy A36 5G 6/128GB"


def test_offers_are_one_per_store_with_lowest_price():
    maximum = catalog.get_or_create_store("maximum", "Maximum", "maximum.md")
    ultra = catalog.get_or_create_store("ultra", "Ultra", "ultra.md")
    product = catalog.create_product("Test phone", "Test", "Смартфоны")
    catalog.upsert_offer(product, maximum, "agg-1", 1000)
    catalog.upsert_offer(product, maximum, "agg-2", 900)
    catalog.upsert_offer(product, maximum, "agg-3", 800, in_stock=False)
    catalog.upsert_offer(product, ultra, "agg-4", 950)

    offers = catalog.offers_json(product)
    assert [(o["storeId"], o["price"]) for o in offers] == [(maximum, 900), (ultra, 950)]


def test_product_image_comes_from_cheapest_offer_with_image():
    maximum = catalog.get_or_create_store("maximum", "Maximum", "maximum.md")
    ultra = catalog.get_or_create_store("ultra", "Ultra", "ultra.md")
    product = catalog.create_product("Image phone", "Test", "Смартфоны")
    catalog.upsert_offer(product, maximum, "img-1", 900)
    catalog.upsert_offer(product, ultra, "img-2", 950, image_url="https://cdn.ultra.md/a.webp")
    assert catalog.image_url(product) == "https://cdn.ultra.md/a.webp"

    catalog.upsert_offer(product, ultra, "img-2", 940)
    assert catalog.image_url(product) == "https://cdn.ultra.md/a.webp"
