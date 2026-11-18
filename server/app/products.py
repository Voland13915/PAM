from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Request, Response

from . import catalog
from .auth import require_auth
from .db import conn
from .errors import json_response, not_found, read_json_body, string_field, validation_error

router = APIRouter()

_IN_STOCK = (
    "EXISTS (SELECT 1 FROM offers o WHERE o.product_id = products.id AND o.in_stock = 1)"
)


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


@router.get("/products")
async def list_products(request: Request, user_id: int = Depends(require_auth)):
    query = request.query_params
    page = max(_int_or(query.get("page"), 1), 1)
    limit = min(max(_int_or(query.get("limit"), 20), 1), 100)
    search = query.get("search", "")

    where = (
        "(ULOWER(name) LIKE ULOWER(?) OR ULOWER(brand) LIKE ULOWER(?) "
        "OR ULOWER(category) LIKE ULOWER(?)) AND " + _IN_STOCK
    )
    pattern = "%" + search + "%"
    args = (pattern, pattern, pattern)

    total = conn.execute(
        "SELECT COUNT(*) AS n FROM products WHERE " + where, args
    ).fetchone()["n"]
    rows = conn.execute(
        "SELECT * FROM products WHERE " + where + " ORDER BY id LIMIT ? OFFSET ?",
        args + (limit, (page - 1) * limit),
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
