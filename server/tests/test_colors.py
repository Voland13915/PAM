import pytest

from app import catalog, gallery
from app.colors import color_info, color_of
from app.db import conn


@pytest.mark.parametrize("title,code", [
    ("Smartphone Apple iPhone 17 Pro 256GB Deep Blue MG8J4", "navy"),
    ("Смартфон Apple iPhone 17 Pro Max Серебристый 12/512GB", "silver"),
    ("Samsung Galaxy Fold 7 16/1TB Синий Тень", "blue"),
    ("Samsung Galaxy S25 Ultra 256 ГБ Серебристо голубой Титан", "lightblue"),
    ("Смартфон Samsung Galaxy S24 Ultra Titanium Black 12/1024GB", "black"),
    ("Samsung Galaxy A57 5G 12/512GB Icy Blue", "lightblue"),
    ("Samsung Galaxy A57 5G 12/512GB Navy", "navy"),
    ("Телефон Moto G57 Power 8/256 Pink Lemonade", "pink"),
    ("Смартфон Xiaomi Black Shark 5 Зеркально-чёрный 8/128GB", "black"),
    ("Смартфон nubia Red Magic 10 Pro 12/256GB Silver", "silver"),
    ("Xiaomi Redmi Note 13 Pro 12/512GB Зеленый Forest", "green"),
    ("Ноутбук Apple MacBook Air 13.6 2026 Midnight", "midnight"),
    ("Ноутбук Apple MacBook Air 13.6 2026 Starlight", "starlight"),
    ("Ноутбук для бизнеса HP EliteBook 8 G1i Glacier Silver", "silver"),
    ("Смартфон Apple iPhone 18 Pro Glacier 12/256GB", "glacier"),
    ("Смартфон Apple iPhone 16 Бирюзовый 8/128GB", "teal"),
    ("Мобильный телефон Maxcom MM718 4G", ""),
])
def test_color_is_found_in_any_language(title, code):
    assert color_of(title) == code


def test_every_color_has_a_name_and_swatch():
    name, swatch = color_info("navy")
    assert name == "Тёмно-синий" and swatch.startswith("#")


def _phone(tag):
    a = catalog.get_or_create_store("maximum", "Maximum", "maximum.md")
    b = catalog.get_or_create_store("ultra", "Ultra", "ultra.md")
    product = catalog.create_product("Color phone %s" % tag, "Apple", "Смартфоны")
    catalog.upsert_offer(product, a, "col-%s-1" % tag, 900, title="iPhone Black",
                         image_url="https://img/black-a.jpg", url="https://a/1")
    catalog.upsert_offer(product, b, "col-%s-2" % tag, 950, title="iPhone Чёрный",
                         image_url="https://img/black-b.jpg", url="https://b/1")
    catalog.upsert_offer(product, a, "col-%s-3" % tag, 1000, title="iPhone Silver",
                         image_url="https://img/silver-a.jpg", url="https://a/2")
    catalog.upsert_offer(product, b, "col-%s-4" % tag, 800, in_stock=False, title="iPhone Orange",
                         image_url="https://img/orange-b.jpg", url="https://b/2")
    catalog.upsert_offer(product, b, "col-%s-5" % tag, 700, title="iPhone",
                         url="https://b/3")
    return product


def test_product_json_lists_colors_with_their_own_offers():
    product = _phone("json")
    row = conn.execute("SELECT * FROM products WHERE id = ?", (product,)).fetchone()
    data = catalog.product_to_json(row)

    assert [c["code"] for c in data["colors"]] == ["black", "silver", "orange"]
    black = data["colors"][0]
    assert black["name"] == "Чёрный"
    assert black["imageUrl"] == "https://img/black-a.jpg"
    assert [o["price"] for o in black["offers"]] == [900, 950]
    assert [o["price"] for o in data["colors"][1]["offers"]] == [1000]
    assert data["colors"][2]["offers"][0]["inStock"] is False
    assert [o["price"] for o in data["offers"]] == [700, 900]


def test_store_color_hint_wins_over_title():
    store = catalog.get_or_create_store("enter", "Enter", "enter.online")
    product = catalog.create_product("Hint laptop", "Acer", "Ноутбуки")
    offer = catalog.upsert_offer(product, store, "hint-1", 100, title="Ноутбук Acer Extensa 15",
                                 color="Ноутбук Acer Extensa 15 Ryzen 7 / 16 ГБ / Серый")
    assert conn.execute("SELECT color FROM offers WHERE id = ?", (offer,)).fetchone()[0] == "gray"


def test_gallery_can_be_limited_to_one_color(monkeypatch, client):
    product = _phone("gallery")
    monkeypatch.setattr(gallery, "_download", lambda url: [url + "#photo"])

    assert gallery.product_images(product, "silver") == ["https://a/2#photo"]
    black = gallery.product_images(product, "black")
    assert black == ["https://a/1#photo", "https://b/1#photo"]

    response = client.get("/products/%d/images" % product, params={"color": "silver"})
    assert response.json()["images"] == ["https://a/2#photo"]
    response = client.get("/products/%d" % product)
    assert {c["code"] for c in response.json()["colors"]} == {"black", "silver", "orange"}
