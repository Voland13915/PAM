import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, Request, Response

from . import catalog, gallery
from .auth import require_auth
from .db import conn, time_limit
from .errors import (
    ApiError, json_response, not_found, read_json_body, string_field, validation_error,
)

router = APIRouter()

def _find(id_param: str):
    try:
        product_id = int(id_param)
    except (TypeError, ValueError):
        return None
    return conn.execute(
        "SELECT * FROM products WHERE id = ?", (product_id,)
    ).fetchone()


def _int_or(value: Optional[str], default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _parse_body(body: Dict[str, Any]) -> Dict[str, Any]:
    name = string_field(body, "name")
    if name is None:
        raise validation_error("name is required")
    category = string_field(body, "category")
    if category is None:
        raise validation_error("category is required")
    brand = body["brand"].strip() if isinstance(body.get("brand"), str) else ""

    specs = body.get("specs", {})
    if not isinstance(specs, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in specs.items()
    ):
        raise validation_error("specs must be an object of strings")

    raw_offers = body.get("offers")
    if not isinstance(raw_offers, list) or not raw_offers:
        raise validation_error("offers must be a non-empty array")
    store_ids = {r["id"] for r in conn.execute("SELECT id FROM stores").fetchall()}
    offers: List[Dict[str, Any]] = []
    for offer in raw_offers:
        if not isinstance(offer, dict):
            raise validation_error("every offer must be an object")
        store_id = offer.get("storeId")
        price = offer.get("price")
        old_price = offer.get("oldPrice")
        in_stock = offer.get("inStock", True)
        if not isinstance(store_id, int) or store_id not in store_ids:
            raise validation_error("offer.storeId must reference an existing store")
        if any(o["storeId"] == store_id for o in offers):
            raise validation_error("every offer must have a different storeId")
        if not _is_number(price) or price <= 0:
            raise validation_error("offer.price must be a positive number")
        if old_price is not None and (not _is_number(old_price) or old_price <= 0):
            raise validation_error("offer.oldPrice must be a positive number")
        if not isinstance(in_stock, bool):
            raise validation_error("offer.inStock must be a boolean")
        offers.append(
            {"storeId": store_id, "price": price, "oldPrice": old_price, "inStock": in_stock}
        )
    if not any(o["inStock"] for o in offers):
        raise validation_error("at least one offer must be in stock")

    return {"name": name, "brand": brand, "category": category,
            "specs": specs, "offers": offers}


def _save_offers(product_id: int, offers: List[Dict[str, Any]]) -> None:
    existing = {
        r["store_id"]: r["external_id"]
        for r in conn.execute(
            "SELECT store_id, external_id FROM offers WHERE product_id = ?",
            (product_id,),
        ).fetchall()
    }
    for o in offers:
        external_id = existing.get(o["storeId"], "manual-%d" % product_id)
        catalog.upsert_offer(
            product_id, o["storeId"], external_id, o["price"],
            old_price=o["oldPrice"], in_stock=o["inStock"],
        )
    keep = [o["storeId"] for o in offers]
    conn.execute(
        "DELETE FROM offers WHERE product_id = ? AND store_id NOT IN (%s)"
        % ",".join("?" * len(keep)),
        (product_id, *keep),
    )


_CATALOG = (
    "SELECT * FROM (SELECT p.*, COALESCE(a.stock_min, a.any_min) AS best_price, "
    "a.available AS available, a.stores AS stores, a.discount AS discount "
    "FROM products p JOIN (SELECT product_id, "
    "MIN(CASE WHEN in_stock = 1 THEN price END) AS stock_min, "
    "MIN(price) AS any_min, "
    "MAX(CASE WHEN in_stock = 1 THEN 1 ELSE 0 END) AS available, "
    "COUNT(DISTINCT CASE WHEN in_stock = 1 THEN store_id END) AS stores, "
    "MAX(CASE WHEN in_stock = 1 AND old_price > price "
    "THEN (old_price - price) / old_price END) AS discount "
    "FROM offers GROUP BY product_id) a ON a.product_id = p.id) c "
    "WHERE c.best_price IS NOT NULL"
)

QUERY_SECONDS = 10.0


def _too_slow() -> ApiError:
    return ApiError(503, "QUERY_TIMEOUT",
                    "Каталог отвечал слишком долго — попробуйте изменить фильтры")


_SORTS = {
    "default": "c.available DESC, c.stores DESC, c.name COLLATE NOCASE",
    "price_asc": "c.available DESC, c.best_price ASC, c.name COLLATE NOCASE",
    "price_desc": "c.available DESC, c.best_price DESC, c.name COLLATE NOCASE",
    "discount": "c.available DESC, COALESCE(c.discount, 0) DESC, c.best_price ASC",
    "name": "c.available DESC, c.name COLLATE NOCASE",
}


def _float_or(value: Optional[str]) -> Optional[float]:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None


def _filters(query) -> Dict[str, Any]:
    brands = [b.strip().lower() for b in query.get("brand", "").split(",") if b.strip()]
    return {
        "words": [w for w in query.get("search", "").lower().split() if w],
        "category": query.get("category", "").strip(),
        "brands": brands,
        "store": _int_or(query.get("store"), 0),
        "min_price": _float_or(query.get("min_price")),
        "max_price": _float_or(query.get("max_price")),
        "discount": query.get("discount") in ("1", "true"),
        "multi": query.get("multi") in ("1", "true"),
        "unavailable": query.get("unavailable") in ("1", "true"),
    }


def _where(f: Dict[str, Any], skip: tuple = ()) -> Tuple[str, List[Any]]:
    parts: List[str] = []
    args: List[Any] = []
    if not f["unavailable"]:
        parts.append("c.available = 1")
    for word in f["words"]:
        parts.append(
            "(ULOWER(c.name) LIKE ? OR ULOWER(c.brand) LIKE ? OR ULOWER(c.category) LIKE ? "
            "OR EXISTS (SELECT 1 FROM offers o WHERE o.product_id = c.id "
            "AND ULOWER(o.title) LIKE ?))"
        )
        args += ["%" + word + "%"] * 4
    if f["category"] and "category" not in skip:
        parts.append("c.category = ?")
        args.append(f["category"])
    if f["brands"] and "brand" not in skip:
        parts.append("ULOWER(c.brand) IN (%s)" % ",".join("?" * len(f["brands"])))
        args += f["brands"]
    if f["store"] and "store" not in skip:
        parts.append(
            "EXISTS (SELECT 1 FROM offers o WHERE o.product_id = c.id "
            "AND o.store_id = ?" + ("" if f["unavailable"] else " AND o.in_stock = 1") + ")"
        )
        args.append(f["store"])
    if f["min_price"] is not None and "price" not in skip:
        parts.append("c.best_price >= ?")
        args.append(f["min_price"])
    if f["max_price"] is not None and "price" not in skip:
        parts.append("c.best_price <= ?")
        args.append(f["max_price"])
    if f["discount"]:
        parts.append("c.discount > 0")
    if f["multi"]:
        parts.append("c.stores >= 2")
    return "".join(" AND " + p for p in parts), args


@router.get("/products/facets")
async def product_facets(request: Request, user_id: int = Depends(require_auth)):
    try:
        with time_limit(QUERY_SECONDS):
            return _facets(_filters(request.query_params))
    except sqlite3.OperationalError as exc:
        if "interrupt" in str(exc):
            raise _too_slow()
        raise


def _facets(f: Dict[str, Any]):

    where, args = _where(f, skip=("category",))
    categories = conn.execute(
        "SELECT c.category AS name, COUNT(*) AS n FROM (" + _CATALOG + where + ") c "
        "GROUP BY c.category ORDER BY n DESC", args,
    ).fetchall()

    where, args = _where(f, skip=("brand",))
    brands = conn.execute(
        "SELECT MIN(c.brand) AS name, COUNT(*) AS n FROM (" + _CATALOG + where + ") c "
        "WHERE c.brand != '' GROUP BY ULOWER(c.brand) ORDER BY n DESC, name", args,
    ).fetchall()

    where, args = _where(f, skip=("store",))
    stores = conn.execute(
        "SELECT o.store_id AS id, COUNT(DISTINCT c.id) AS n FROM (" + _CATALOG + where + ") c "
        "JOIN offers o ON o.product_id = c.id"
        + ("" if f["unavailable"] else " AND o.in_stock = 1") + " GROUP BY o.store_id", args,
    ).fetchall()

    where, args = _where(f, skip=("price",))
    prices = conn.execute(
        "SELECT MIN(c.best_price) AS lo, MAX(c.best_price) AS hi FROM (" + _CATALOG + where
        + ") c", args,
    ).fetchone()

    where, args = _where(f)
    total = conn.execute(
        "SELECT COUNT(*) AS n FROM (" + _CATALOG + where + ") c", args
    ).fetchone()["n"]

    return json_response({
        "categories": [{"name": r["name"], "count": r["n"]} for r in categories],
        "brands": [{"name": r["name"], "count": r["n"]} for r in brands],
        "stores": [{"id": r["id"], "count": r["n"]} for r in stores],
        "minPrice": prices["lo"],
        "maxPrice": prices["hi"],
        "total": total,
    })


@router.get("/products")
async def list_products(request: Request, user_id: int = Depends(require_auth)):
    try:
        with time_limit(QUERY_SECONDS):
            return _list(request.query_params)
    except sqlite3.OperationalError as exc:
        if "interrupt" in str(exc):
            raise _too_slow()
        raise


def _list(query):
    page = max(_int_or(query.get("page"), 1), 1)
    limit = min(max(_int_or(query.get("limit"), 20), 1), 100)
    order = _SORTS.get(query.get("sort", "default"), _SORTS["default"])
    where, args = _where(_filters(query))

    total = conn.execute(
        "SELECT COUNT(*) AS n FROM (" + _CATALOG + where + ") c", args
    ).fetchone()["n"]
    rows = conn.execute(
        _CATALOG + where + " ORDER BY " + order + " LIMIT ? OFFSET ?",
        args + [limit, (page - 1) * limit],
    ).fetchall()

    return json_response(
        {
            "items": [catalog.product_to_json(row) for row in rows],
            "page": page,
            "limit": limit,
            "total": total,
        }
    )


@router.post("/products")
async def create_product(request: Request, user_id: int = Depends(require_auth)):
    body = await read_json_body(request)
    if body is None:
        raise validation_error("Body must be a JSON object")
    fields = _parse_body(body)
    with catalog.transaction():
        product_id = catalog.create_product(
            fields["name"], fields["brand"], fields["category"], fields["specs"]
        )
        _save_offers(product_id, fields["offers"])
    return json_response(catalog.product_to_json(_find(str(product_id))), status=201)


@router.get("/products/{product_id}")
async def get_product(product_id: str, user_id: int = Depends(require_auth)):
    row = _find(product_id)
    if row is None:
        raise not_found("Product not found")
    return json_response(catalog.product_to_json(row))


@router.get("/products/{product_id}/images")
async def get_product_images(product_id: str, color: str = "",
                             user_id: int = Depends(require_auth)):
    row = _find(product_id)
    if row is None:
        raise not_found("Product not found")
    images = await gallery.product_images_async(row["id"], color.strip().lower())
    return json_response({"images": images})


@router.put("/products/{product_id}")
async def update_product(
    product_id: str, request: Request, user_id: int = Depends(require_auth)
):
    row = _find(product_id)
    if row is None:
        raise not_found("Product not found")
    body = await read_json_body(request)
    if body is None:
        raise validation_error("Body must be a JSON object")
    fields = _parse_body(body)
    with catalog.transaction():
        catalog.update_product(
            row["id"], fields["name"], fields["brand"], fields["category"], fields["specs"]
        )
        _save_offers(row["id"], fields["offers"])
    return json_response(catalog.product_to_json(_find(str(row["id"]))))


@router.delete("/products/{product_id}")
async def delete_product(product_id: str, user_id: int = Depends(require_auth)):
    row = _find(product_id)
    if row is None:
        raise not_found("Product not found")
    conn.execute("DELETE FROM products WHERE id = ?", (row["id"],))
    return Response(status_code=204)
