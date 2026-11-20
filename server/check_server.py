#!/usr/bin/env python3
"""Собственный набор проверок backend-а TechPrice (L5).

ВАЖНО: это НЕ официальный набор соответствия (conformance) из kit-а курса.
Скрипт написан по тому же принципу: бьёт по запущенному серверу через HTTP
ровно так, как это делает приложение, и проверяет контракт — сначала базовый
контракт шаблона (health, auth, notes, files), затем маршруты темы
(stores, products, wishlist).

Только стандартная библиотека Python 3.8+, ничего устанавливать не нужно.

Запуск (сервер должен работать):
    .\\.venv\\Scripts\\python check_server.py --base-url http://localhost:8080

Скрипт можно запускать сколько угодно раз: пользователи создаются с
уникальными e-mail, созданные товары, слежения и заметки удаляются.
Единственный след — тестовые пользователи (API не умеет удалять
пользователей); при желании удалите app.db и перезапустите сервер.
Код возврата: 0 — все проверки прошли, 1 — есть провалы.
"""

import argparse
import http.client
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TIMEOUT = 20
passed = 0
failed = 0
BASE = "http://localhost:8080"


class Resp:
    def __init__(self, status, headers, raw):
        self.status = status
        self.headers = headers
        self.raw = raw

    @property
    def json(self):
        return json.loads(self.raw.decode("utf-8")) if self.raw else None


def call(method, path, body=None, token=None, raw=None, ctype="application/json",
         headers=None):
    data = raw if raw is not None else (
        json.dumps(body).encode("utf-8") if body is not None else None)
    req = urllib.request.Request(BASE + path, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", ctype)
    if token:
        req.add_header("Authorization", "Bearer " + token)
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return Resp(resp.status, resp.headers, resp.read())
    except urllib.error.HTTPError as err:
        return Resp(err.code, err.headers, err.read())


def call_large_upload(path, content_type, body, token):
    """Отправляет тело, которое сервер отвергнет, не дочитав до конца.

    Сервер вправе ответить 400 и закрыть соединение раньше, чем клиент
    закончит передачу: тогда send() падает с BrokenPipe/ConnectionReset,
    а ответ уже лежит во входном буфере. Поэтому ошибку передачи
    проглатываем и пытаемся прочитать ответ.
    """
    parsed = urllib.parse.urlparse(BASE)
    conn = http.client.HTTPConnection(parsed.hostname, parsed.port or 80, timeout=TIMEOUT)
    try:
        conn.putrequest("POST", path)
        conn.putheader("Content-Type", content_type)
        conn.putheader("Content-Length", str(len(body)))
        conn.putheader("Authorization", "Bearer " + token)
        conn.endheaders()
        try:
            conn.send(body)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass  # сервер ответил и закрыл соединение досрочно
        try:
            resp = conn.getresponse()
            return Resp(resp.status, resp.headers, resp.read())
        except (OSError, http.client.HTTPException):
            return None
    finally:
        conn.close()


def check(condition, name):
    global passed, failed
    if condition:
        passed += 1
        print("  \u2713 " + name)
    else:
        failed += 1
        print("  \u2717 " + name)


def error_code(resp):
    try:
        return resp.json["error"]["code"]
    except Exception:
        return None


def multipart(fields, boundary="----techprice"):
    """Минимальное multipart/form-data тело: [(name, filename, ctype, bytes)]."""
    out = b""
    for name, filename, ctype, content in fields:
        out += ("--%s\r\n" % boundary).encode()
        disposition = 'form-data; name="%s"' % name
        if filename:
            disposition += '; filename="%s"' % filename
        out += ("Content-Disposition: %s\r\n" % disposition).encode()
        if ctype:
            out += ("Content-Type: %s\r\n" % ctype).encode()
        out += b"\r\n" + content + b"\r\n"
    out += ("--%s--\r\n" % boundary).encode()
    return out, "multipart/form-data; boundary=%s" % boundary


def section(title):
    print("\n\u2014 " + title)


def main():
    global BASE
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--base-url", default="http://localhost:8080")
    BASE = parser.parse_args().base_url.rstrip("/")

    stamp = str(int(time.time() * 1000))
    email_a = "check_a_%s@test.md" % stamp
    email_b = "check_b_%s@test.md" % stamp
    password = "parola123"

    print("TechPrice: собственный набор проверок backend-а (не официальный conformance)")
    print("Сервер: " + BASE)

    # ------------------------------------------------------------------
    token_a = token_b = store_id = store_id2 = pid = tag = new_product = item = None

    def sec_1():
        nonlocal token_a, token_b, store_id, store_id2, pid, tag, new_product, item
        if token_a is None and 1 > 1:
            raise RuntimeError("нет token-а: не прошла регистрация в первом разделе")
        r = call("GET", "/health")
        check(r.status == 200 and r.json == {"status": "ok"}, "GET /health \u2192 200 {status: ok}")
        r = call("GET", "/notes")
        check(r.status == 401 and error_code(r) == "UNAUTHORIZED", "запрос без token-а \u2192 401 UNAUTHORIZED")
        r = call("GET", "/notes", token="not.a.token")
        check(r.status == 401, "поддельный token \u2192 401")

        r = call("POST", "/auth/register", {"email": email_a, "password": password, "name": "Ana"})
        check(r.status == 201 and "token" in r.json and r.json["user"]["email"] == email_a,
              "register \u2192 201 {token, user}")
        token_a = r.json["token"]
        r = call("POST", "/auth/register", {"email": email_a, "password": password, "name": "Ana"})
        check(r.status == 409 and error_code(r) == "EMAIL_TAKEN", "повторный email \u2192 409 EMAIL_TAKEN")
        r = call("POST", "/auth/register", {"email": "x_%s@test.md" % stamp, "password": password})
        check(r.status == 400 and error_code(r) == "VALIDATION_ERROR", "register без name \u2192 400 VALIDATION_ERROR")
        r = call("POST", "/auth/register", {"email": "not-an-email", "password": password, "name": "A"})
        check(r.status == 400, "register с неверным email \u2192 400")
        r = call("POST", "/auth/login", {"email": email_a, "password": "wrong-password"})
        check(r.status == 401 and error_code(r) == "UNAUTHORIZED", "login с неверным паролем \u2192 401")
        r = call("POST", "/auth/login", {"email": email_a, "password": password})
        check(r.status == 200 and "token" in r.json, "login \u2192 200 {token}")
        r = call("GET", "/me", token=token_a)
        check(r.status == 200 and r.json["email"] == email_a and r.json["name"] == "Ana", "GET /me \u2192 данные пользователя")

        r = call("POST", "/auth/register", {"email": email_b, "password": password, "name": "Ion"})
        token_b = r.json["token"]

    def sec_2():
        nonlocal token_a, token_b, store_id, store_id2, pid, tag, new_product, item
        if token_a is None and 2 > 1:
            raise RuntimeError("нет token-а: не прошла регистрация в первом разделе")
        r = call("GET", "/notes", token=token_a)
        check(r.status == 200 and r.json == {"items": [], "page": 1, "limit": 20, "total": 0},
              "пустой пагинированный конверт {items, page, limit, total}")
        r = call("POST", "/notes", {"content": "без заголовка"}, token_a)
        check(r.status == 400 and error_code(r) == "VALIDATION_ERROR", "создание без title \u2192 400")
        r = call("POST", "/notes", {"title": "Покупки", "content": "молоко, хлеб"}, token_a)
        check(r.status == 201 and r.json["id"] > 0, "создание \u2192 201, id выдал сервер")
        note_id = r.json["id"]
        r = call("GET", "/notes?search=" + urllib.parse.quote("Покуп"), token=token_a)
        check(r.status == 200 and r.json["total"] == 1, "поиск ?search= находит заметку")
        r = call("GET", "/notes/%d" % note_id, token=token_a)
        check(r.status == 200 and r.json["title"] == "Покупки", "GET /notes/{id} \u2192 200")
        r = call("GET", "/notes/%d" % note_id, token=token_b)
        check(r.status == 404 and error_code(r) == "NOT_FOUND", "чужая заметка \u2192 404, а не 403")
        r = call("PUT", "/notes/%d" % note_id, {"title": "Покупки 2", "content": ""}, token_a)
        check(r.status == 200 and r.json["title"] == "Покупки 2", "PUT \u2192 200")
        r = call("DELETE", "/notes/%d" % note_id, token=token_a)
        check(r.status == 204 and not r.raw, "DELETE \u2192 204 без тела")
        r = call("GET", "/notes/%d" % note_id, token=token_a)
        check(r.status == 404, "после удаления \u2192 404")

    def sec_3():
        nonlocal token_a, token_b, store_id, store_id2, pid, tag, new_product, item
        if token_a is None and 3 > 1:
            raise RuntimeError("нет token-а: не прошла регистрация в первом разделе")
        body, ctype = multipart([("file", "a.txt", "text/plain", b"hello")])
        r = call("POST", "/files", raw=body, ctype=ctype, token=token_a)
        check(r.status == 201 and r.json["url"].startswith("/files/") and r.json["size"] == 5,
              "upload \u2192 201 {id, url, name, size, mimeType}")
        file_url = r.json["url"]
        r = call("GET", file_url)
        check(r.status == 200 and r.raw == b"hello", "GET /files/{id} возвращает те же байты")
        check(r.headers.get("Content-Type") == "text/plain", "Content-Type отдаётся как был загружен")
        body, ctype = multipart([("other", "a.txt", "text/plain", b"x")])
        r = call("POST", "/files", raw=body, ctype=ctype, token=token_a)
        check(r.status == 400, "нет поля file \u2192 400")
        r = call("POST", "/files", raw=b"garbage", ctype="multipart/form-data; boundary=zzz", token=token_a)
        check(r.status == 400, "битое multipart-тело \u2192 400, без зависания")
        big, ctype = multipart([("file", "big.bin", "application/octet-stream", b"0" * (5 * 1024 * 1024 + 1024))])
        r = call_large_upload("/files", ctype, big, token_a)
        check(r is not None and r.status == 400, "файл больше 5 МБ \u2192 400")
        r = call("POST", "/files", raw=b"x", ctype="text/plain", token=token_a)
        check(r.status == 400, "не multipart \u2192 400")
        r = call("GET", "/files/999999999")
        check(r.status == 404, "несуществующий файл \u2192 404")

    def sec_4():
        nonlocal token_a, token_b, store_id, store_id2, pid, tag, new_product, item
        if token_a is None and 4 > 1:
            raise RuntimeError("нет token-а: не прошла регистрация в первом разделе")
        r = call("GET", "/stores")
        check(r.status == 401, "без token-а \u2192 401")
        r = call("GET", "/stores?limit=100", token=token_a)
        check(r.status == 200 and r.json["total"] >= 1 and len(r.json["items"]) == r.json["total"],
              "список: пагинированный конверт")
        store = r.json["items"][0]
        check(all(k in store for k in ("id", "name", "website", "productsTracked", "lastSync")),
              "поля магазина: id, name, website, productsTracked, lastSync")
        store_id = store["id"]
        check(len(r.json["items"]) >= 2, "в каталоге не меньше двух магазинов")
        store_id2 = r.json["items"][1]["id"]
        r = call("GET", "/stores/%d" % store_id, token=token_a)
        check(r.status == 200 and r.json["id"] == store_id, "GET /stores/{id} \u2192 200")
        r = call("GET", "/stores/999999", token=token_a)
        check(r.status == 404 and error_code(r) == "NOT_FOUND", "несуществующий магазин \u2192 404")
        r = call("GET", "/stores/abc", token=token_a)
        check(r.status == 404, "нечисловой id \u2192 404")

    def sec_5():
        nonlocal token_a, token_b, store_id, store_id2, pid, tag, new_product, item
        if token_a is None and 5 > 1:
            raise RuntimeError("нет token-а: не прошла регистрация в первом разделе")
        r = call("GET", "/products")
        check(r.status == 401, "без token-а \u2192 401")
        r = call("GET", "/products", token=token_a)
        total = r.json["total"]
        check(r.status == 200 and r.json["page"] == 1 and r.json["limit"] == 20
              and len(r.json["items"]) == min(20, total), "первая страница: page=1, limit=20 по умолчанию")
        check(total >= 21, "в каталоге больше одной страницы (%d товаров)" % total)
        p = r.json["items"][0]
        check(isinstance(p["specs"], dict) and isinstance(p["offers"], list) and isinstance(p["priceHistory"], list),
              "specs, offers, priceHistory приходят как JSON-объект и массивы")
        check(all(k in p["offers"][0] for k in ("storeId", "price", "inStock")), "предложение: storeId, price, inStock")
        first_ids = [i["id"] for i in r.json["items"]]
        r = call("GET", "/products?page=2&limit=5", token=token_a)
        check(r.status == 200 and r.json["page"] == 2 and r.json["limit"] == 5 and len(r.json["items"]) == 5
              and not set(i["id"] for i in r.json["items"]) & set(first_ids[:5]),
              "page=2&limit=5: другая страница нужного размера")
        r = call("GET", "/products?limit=1000", token=token_a)
        check(r.json["limit"] == 100, "limit ограничен сверху (100)")
        r = call("GET", "/products?page=-3&limit=abc", token=token_a)
        check(r.status == 200 and r.json["page"] == 1 and r.json["limit"] == 20, "мусор в page/limit \u2192 значения по умолчанию")

        tag = "ЧекТовар%s" % stamp[-6:]
        new_product = {
            "name": tag + " Смартфон",
            "brand": "TestBrand",
            "category": "Тест-Категория" + stamp[-6:],
            "specs": {"Память": "8 ГБ"},
            "offers": [{"storeId": store_id, "price": 999}, {"storeId": store_id2, "price": 899, "oldPrice": 1099}],
        }
        r = call("POST", "/products", {"name": "x"}, token_a)
        check(r.status == 400 and error_code(r) == "VALIDATION_ERROR", "создание без category/offers \u2192 400")
        r = call("POST", "/products", dict(new_product, offers=[{"storeId": 999999, "price": 10}]), token_a)
        check(r.status == 400, "предложение с несуществующим магазином \u2192 400")
        r = call("POST", "/products", dict(new_product, offers=[{"storeId": store_id, "price": -5}]), token_a)
        check(r.status == 400, "отрицательная цена \u2192 400")
        r = call("POST", "/products", dict(new_product, offers=[{"storeId": store_id, "price": 10, "inStock": False}]), token_a)
        check(r.status == 400, "ни одного предложения в наличии \u2192 400")
        r = call("POST", "/products", dict(new_product, specs={"Память": 8}), token_a)
        check(r.status == 400, "specs не из строк \u2192 400")
        r = call("POST", "/products", dict(new_product, offers=[{"storeId": store_id, "price": 10},
                                                                {"storeId": store_id, "price": 9}]), token_a)
        check(r.status == 400, "два предложения одного магазина \u2192 400")
        r = call("POST", "/products", new_product, token_a)
        check(r.status == 201 and r.json["id"] > 0, "создание \u2192 201, id выдал сервер")
        pid = r.json["id"]
        check(r.json["priceHistory"] == [899], "история цены по умолчанию = минимальная цена")
        cheapest = next(o for o in r.json["offers"] if o["storeId"] == store_id2)
        check(cheapest["price"] == 899 and cheapest["oldPrice"] == 1099, "oldPrice сохраняется")
        r = call("GET", "/products?search=" + urllib.parse.quote(tag.lower()), token=token_a)
        check(r.status == 200 and r.json["total"] == 1 and r.json["items"][0]["id"] == pid,
              "поиск по названию без учёта регистра (кириллица)")
        r = call("GET", "/products?search=" + urllib.parse.quote(("Тест-Категория" + stamp[-6:]).lower()), token=token_a)
        check(r.status == 200 and r.json["total"] == 1, "поиск по категории без учёта регистра")
        r = call("GET", "/products?search=testbrand", token=token_a)
        check(r.status == 200 and any(i["id"] == pid for i in r.json["items"]), "поиск по бренду")
        r = call("GET", "/products?search=" + urllib.parse.quote("zzzнет-такого-%s" % stamp), token=token_a)
        check(r.status == 200 and r.json["total"] == 0 and r.json["items"] == [], "ничего не найдено \u2192 пустой конверт")
        r = call("GET", "/products/%d" % pid, token=token_b)
        check(r.status == 200 and r.json["name"].startswith(tag), "каталог общий: GET /products/{id} другим пользователем")
        r = call("GET", "/products/999999", token=token_a)
        check(r.status == 404 and error_code(r) == "NOT_FOUND", "несуществующий товар \u2192 404")
        r = call("PUT", "/products/%d" % pid, dict(new_product, name=tag + " Планшет"), token_a)
        check(r.status == 200 and r.json["name"].endswith("Планшет"), "PUT \u2192 200")
        r = call("PUT", "/products/999999", new_product, token_a)
        check(r.status == 404, "PUT несуществующего \u2192 404")
        r = call("PUT", "/products/%d" % pid, {"name": "x"}, token_a)
        check(r.status == 400, "PUT с неверным телом \u2192 400")

    def sec_6():
        nonlocal token_a, token_b, store_id, store_id2, pid, tag, new_product, item
        if token_a is None and 6 > 1:
            raise RuntimeError("нет token-а: не прошла регистрация в первом разделе")
        r = call("GET", "/wishlist")
        check(r.status == 401, "без token-а \u2192 401")
        r = call("GET", "/wishlist", token=token_a)
        check(r.status == 200 and r.json["total"] == 0 and r.json["items"] == [], "у нового пользователя пусто")
        item = {"productId": pid, "storeId": store_id, "targetPrice": 800}
        r = call("POST", "/wishlist", {"productId": 999999, "storeId": store_id, "targetPrice": 10}, token_a)
        check(r.status == 400 and error_code(r) == "VALIDATION_ERROR", "несуществующий товар \u2192 400")
        r = call("POST", "/wishlist", {"productId": pid, "storeId": 999999, "targetPrice": 10}, token_a)
        check(r.status == 400, "несуществующий магазин \u2192 400")
        r = call("POST", "/wishlist", dict(item, targetPrice=-1), token_a)
        check(r.status == 400, "отрицательная желаемая цена \u2192 400")
        r = call("POST", "/wishlist", dict(item, notify="yes"), token_a)
        check(r.status == 400, "notify не boolean \u2192 400")
        r = call("POST", "/wishlist", {"productId": pid}, token_a)
        check(r.status == 400, "без storeId/targetPrice \u2192 400")
        r = call("POST", "/wishlist", item, token_a)
        check(r.status == 201 and r.json["id"] > 0 and r.json["notify"] is True and r.json["targetPrice"] == 800,
              "создание \u2192 201, id выдал сервер, notify по умолчанию true")
        wid = r.json["id"]
        r = call("GET", "/wishlist?search=" + urllib.parse.quote(tag.lower()), token=token_a)
        check(r.status == 200 and r.json["total"] == 1 and r.json["items"][0]["id"] == wid,
              "поиск по названию товара без учёта регистра")
        r = call("GET", "/wishlist/%d" % wid, token=token_a)
        check(r.status == 200 and r.json["productId"] == pid, "GET /wishlist/{id} \u2192 200")
        r = call("PUT", "/wishlist/%d" % wid, dict(item, targetPrice=750, notify=False), token_a)
        check(r.status == 200 and r.json["targetPrice"] == 750 and r.json["notify"] is False, "PUT \u2192 200")
        r = call("GET", "/wishlist/%d" % wid, token=token_b)
        check(r.status == 404 and error_code(r) == "NOT_FOUND", "чужое слежение \u2192 404, а не 403")
        r = call("PUT", "/wishlist/%d" % wid, item, token_b)
        check(r.status == 404, "PUT чужого слежения \u2192 404")
        r = call("DELETE", "/wishlist/%d" % wid, token=token_b)
        check(r.status == 404, "DELETE чужого слежения \u2192 404")
        r = call("GET", "/wishlist", token=token_b)
        check(r.status == 200 and r.json["total"] == 0, "другой пользователь своих слежений не видит чужих")
        r = call("DELETE", "/wishlist/%d" % wid, token=token_a)
        check(r.status == 204 and not r.raw, "DELETE \u2192 204 без тела")
        r = call("DELETE", "/wishlist/%d" % wid, token=token_a)
        check(r.status == 404, "повторный DELETE \u2192 404")

    def sec_7():
        nonlocal token_a, token_b, store_id, store_id2, pid, tag, new_product, item
        if token_a is None and 7 > 1:
            raise RuntimeError("нет token-а: не прошла регистрация в первом разделе")
        r = call("POST", "/wishlist", item, token_a)
        wid2 = r.json["id"]
        r = call("DELETE", "/products/%d" % pid, token=token_a)
        check(r.status == 204 and not r.raw, "DELETE товара \u2192 204 без тела")
        r = call("GET", "/wishlist/%d" % wid2, token=token_a)
        check(r.status == 404, "слежения за удалённым товаром удалены вместе с ним")
        r = call("GET", "/products/%d" % pid, token=token_a)
        check(r.status == 404, "удалённый товар \u2192 404")

    sections = [
        ("Базовый контракт шаблона: health и аутентификация", sec_1),
        ("Базовый контракт шаблона: notes (пример сущности)", sec_2),
        ("Базовый контракт шаблона: files (multipart)", sec_3),
        ("Сущность темы: stores", sec_4),
        ("Сущность темы: products", sec_5),
        ("Сущность темы: wishlist (слежения, свои у каждого пользователя)", sec_6),
        ("Связи и уборка", sec_7),
    ]
    for title, fn in sections:
        section(title)
        try:
            fn()
        except urllib.error.URLError:
            raise  # сервер недоступен — сообщит верхний уровень
        except Exception as err:  # сбой раздела не обрывает остальные
            check(False, "проверки раздела прерваны: %s: %s" % (type(err).__name__, err))

    total_checks = passed + failed
    print()
    if failed == 0:
        print("PASS \u2014 %d/%d checks passed" % (passed, total_checks))
        return 0
    print("FAIL \u2014 %d of %d checks failed" % (failed, total_checks))
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except urllib.error.URLError as err:
        print("\n\u2717 Не удалось подключиться к серверу %s: %s" % (BASE, err.reason))
        print("  Проверьте, что сервер запущен, и адрес --base-url.")
        sys.exit(2)