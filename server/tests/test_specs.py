from app.matching import product_name
from app.specs import normalize_cpu, parse_specs

MAXIMUM_LAPTOP = ("Procesor: Core i5-13450HX / Memoria operativă, GB: 16 / "
                  "Capacitate SSD, GB: 1000 / Ecran, inch: 15,6")
ULTRA_LAPTOP = ('15.6" | IPS | 144 Гц | 16 ГБ | 1 ТБ | Intel Core i5-13450HX | '
                'NVIDIA GeForce RTX 4050 | 6 Гб GDDR6')


def test_maximum_laptop_pairs():
    specs = parse_specs("Ноутбуки", MAXIMUM_LAPTOP)
    assert (specs.ram, specs.storage, specs.screen) == (16, 1024, 15.6)
    assert specs.cpu == "i5 13450hx"
    assert specs.display["Накопитель"] == "1 ТБ"


def test_ultra_laptop_segments_have_same_meaning():
    specs = parse_specs("Ноутбуки", ULTRA_LAPTOP)
    maximum = parse_specs("Ноутбуки", MAXIMUM_LAPTOP)
    assert (specs.ram, specs.storage, specs.screen, specs.cpu) == \
        (maximum.ram, maximum.storage, maximum.screen, maximum.cpu)
    assert specs.display["Видеокарта"] == "NVIDIA GeForce RTX 4050"
    assert specs.display["Видеопамять"] == "6 Гб GDDR6"
    assert specs.display["Частота экрана"] == "144 Гц"
    assert specs.display["Матрица"] == "IPS"


def test_ultra_laptop_with_single_size_is_storage():
    specs = parse_specs("Ноутбуки", '16" | OLED | 512 ГБ | AMD Ryzen 7 5800H')
    assert specs.ram is None and specs.storage == 512
    assert specs.cpu == "ryzen 7 5800h"


def test_phones_from_both_stores():
    ultra = parse_specs("Смартфоны", '12 ГБ / 1024 ГБ | 6.3" | 120 Гц | 4056 мА·ч')
    assert (ultra.ram, ultra.storage, ultra.screen) == (12, 1024, 6.3)
    assert ultra.display["Аккумулятор"] == "4056 мА·ч"

    maximum = parse_specs(
        "Смартфоны",
        "Ecran, inch: 6,7 / Rezolutie ecran, pixeli: 2340x1080 Full HD+ / "
        "Tehnologie sensor: Super AMOLED / Rezoluția foto (principala), Mp: 50",
        memory=(8, 256),
    )
    assert (maximum.ram, maximum.storage, maximum.screen) == (8, 256, 6.7)
    assert maximum.display["Камера"] == "50 Мп"
    assert maximum.display["Матрица"] == "Super AMOLED"


def test_cpu_names_are_normalized_the_same_way():
    assert normalize_cpu("Core Ultra 7 255U") == normalize_cpu("Intel Core Ultra 7 255U")
    assert normalize_cpu("Core i5-13450HX") == normalize_cpu("Intel Core i5 13450HX")
    assert normalize_cpu("Ryzen AI 7 445") == normalize_cpu("AMD Ryzen AI 7 445")
    assert normalize_cpu("M1 with 8-core CPU and 7-core GPU") == "m1 c8g7"
    assert normalize_cpu("A18 Pro(6CPU/5GPU)") == "a18 pro c6g5"
    assert normalize_cpu("Core i5-13450HX") != normalize_cpu("Core i5-12450HX")


def test_apple_cores_are_taken_from_maximum_title():
    specs = parse_specs("Ноутбуки", "Procesor: Apple M5 / Memoria operativă, GB: 16 / "
                        "Capacitate SSD, GB: 512 / Ecran, inch: 13,6",
                        title='Laptop Apple MacBook Air 13" M5 10c/8g 16/512 GB Midnight')
    assert specs.cpu == normalize_cpu("M5 (10CPU/8GPU)") == "m5 c10g8"


def test_laptop_product_name_contains_configuration():
    specs = parse_specs("Ноутбуки", ULTRA_LAPTOP)
    name = product_name("Ноутбуки", [
        "Laptop ASUS FX608JM-RV002 TUF Gaming",
        "Игровой ноутбук ASUS TUF Gaming F16 FX608JM Jaeger Gray",
    ], specs)
    assert name == "ASUS TUF Gaming F16 FX608JM · i5-13450HX, 16 ГБ / 1 ТБ"

    mac = product_name("Ноутбуки", ['Laptop Apple MacBook Air 13" M5 10c/8g 16/512 GB Midnight MDHE4'],
                       parse_specs("Ноутбуки", '13.6" | Liquid Retina | 16 ГБ | 512 ГБ | M5 (10CPU/8GPU)'))
    assert mac == "Apple MacBook Air 13 M5 · 16 ГБ / 512 ГБ"
