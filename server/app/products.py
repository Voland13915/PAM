import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Request, Response

from .auth import require_auth
from .db import conn, now_iso
from .errors import json_response, not_found, read_json_body, string_field, validation_error

router = APIRouter()


def _to_json(row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "brand": row["brand"],
        "category": row["category"],
        "specs": json.loads(row["specs"]),
        "offers": json.loads(row["offers"]),
        "priceHistory": json.loads(row["price_history"]),
        "createdAt": row["created_at"],
    }


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
    """Validates a product body; raises 400 VALIDATION_ERROR on bad input."""
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

    history = body.get("priceHistory")
    if history is None or history == []:
        history = [min(o["price"] for o in offers if o["inStock"])]
    if not isinstance(history, list) or not all(_is_number(p) and p > 0 for p in history):
        raise validation_error("priceHistory must be an array of positive numbers")

    return {
        "name": name,
        "brand": brand,
        "category": category,
        "specs": json.dumps(specs, ensure_ascii=False),
        "offers": json.dumps(offers, ensure_ascii=False),
        "price_history": json.dumps(history),
    }


@router.get("/products")
async def list_products(request: Request, user_id: int = Depends(require_auth)):
    """GET /products?page=1&limit=20&search=  -> {items, page, limit, total}

    search matches name, brand or category, case-insensitively (Cyrillic too).
    """
    query = request.query_params
    page = max(_int_or(query.get("page"), 1), 1)
    limit = min(max(_int_or(query.get("limit"), 20), 1), 100)
    search = query.get("search", "")

    where = (
        "ULOWER(name) LIKE ULOWER(?) OR ULOWER(brand) LIKE ULOWER(?) "
        "OR ULOWER(category) LIKE ULOWER(?)"
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
            "items": [_to_json(row) for row in rows],
            "page": page,
            "limit": limit,
            "total": total,
        }
    )


@router.post("/products")
async def create_product(request: Request, user_id: int = Depends(require_auth)):
    """POST /products  {name, brand, category, specs, offers, priceHistory} -> 201"""
    body = await read_json_body(request)
    if body is None:
        raise validation_error("Body must be a JSON object")
    fields = _parse_body(body)
    cursor = conn.execute(
        "INSERT INTO products (name, brand, category, specs, offers, price_history, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            fields["name"], fields["brand"], fields["category"], fields["specs"],
            fields["offers"], fields["price_history"], now_iso(),
        ),
    )
    row = _find(str(cursor.lastrowid))
    return json_response(_to_json(row), status=201)


@router.get("/products/{product_id}")
async def get_product(product_id: str, user_id: int = Depends(require_auth)):
    """GET /products/{id} -> 200 product | 404"""
    row = _find(product_id)
    if row is None:
        raise not_found("Product not found")
    return json_response(_to_json(row))


@router.put("/products/{product_id}")
async def update_product(
    product_id: str, request: Request, user_id: int = Depends(require_auth)
):
    """PUT /products/{id}  {...same body as POST} -> 200 updated product | 404"""
    row = _find(product_id)
    if row is None:
        raise not_found("Product not found")
    body = await read_json_body(request)
    if body is None:
        raise validation_error("Body must be a JSON object")
    fields = _parse_body(body)
    conn.execute(
        "UPDATE products SET name = ?, brand = ?, category = ?, specs = ?, "
        "offers = ?, price_history = ? WHERE id = ?",
        (
            fields["name"], fields["brand"], fields["category"], fields["specs"],
            fields["offers"], fields["price_history"], row["id"],
        ),
    )
    return json_response(_to_json(_find(str(row["id"]))))


@router.delete("/products/{product_id}")
async def delete_product(product_id: str, user_id: int = Depends(require_auth)):
    """DELETE /products/{id} -> 204 | 404. Price alerts on it go too."""
    row = _find(product_id)
    if row is None:
        raise not_found("Product not found")
    conn.execute("DELETE FROM wishlist WHERE product_id = ?", (row["id"],))
    conn.execute("DELETE FROM products WHERE id = ?", (row["id"],))
    return Response(status_code=204)
