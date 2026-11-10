from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Request, Response

from .auth import require_auth
from .db import conn, now_iso
from .errors import json_response, not_found, read_json_body, validation_error

router = APIRouter()


def _to_json(row) -> dict:
    return {
        "id": row["id"],
        "productId": row["product_id"],
        "storeId": row["store_id"],
        "targetPrice": row["target_price"],
        "notify": bool(row["notify"]),
        "createdAt": row["created_at"],
    }


def _find(user_id: int, id_param: str):
    try:
        item_id = int(id_param)
    except (TypeError, ValueError):
        return None
    return conn.execute(
        "SELECT * FROM wishlist WHERE id = ? AND user_id = ?", (item_id, user_id)
    ).fetchone()


def _int_or(value: Optional[str], default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_body(body: Dict[str, Any]) -> Dict[str, Any]:
    product_id = body.get("productId")
    store_id = body.get("storeId")
    target = body.get("targetPrice")
    notify = body.get("notify", True)

    if not isinstance(product_id, int) or isinstance(product_id, bool):
        raise validation_error("productId is required")
    if conn.execute("SELECT 1 FROM products WHERE id = ?", (product_id,)).fetchone() is None:
        raise validation_error("productId must reference an existing product")
    if not isinstance(store_id, int) or isinstance(store_id, bool):
        raise validation_error("storeId is required")
    if conn.execute("SELECT 1 FROM stores WHERE id = ?", (store_id,)).fetchone() is None:
        raise validation_error("storeId must reference an existing store")
    if not isinstance(target, (int, float)) or isinstance(target, bool) or target <= 0:
        raise validation_error("targetPrice must be a positive number")
    if not isinstance(notify, bool):
        raise validation_error("notify must be a boolean")
    return {
        "product_id": product_id,
        "store_id": store_id,
        "target_price": float(target),
        "notify": 1 if notify else 0,
    }


@router.get("/wishlist")
async def list_wishlist(request: Request, user_id: int = Depends(require_auth)):
    query = request.query_params
    page = max(_int_or(query.get("page"), 1), 1)
    limit = min(max(_int_or(query.get("limit"), 20), 1), 100)
    search = query.get("search", "")

    where = (
        "w.user_id = ? AND (ULOWER(p.name) LIKE ULOWER(?) "
        "OR ULOWER(p.brand) LIKE ULOWER(?))"
    )
    args = (user_id, "%" + search + "%", "%" + search + "%")
    base = "FROM wishlist w JOIN products p ON p.id = w.product_id WHERE " + where

    total = conn.execute("SELECT COUNT(*) AS n " + base, args).fetchone()["n"]
    rows = conn.execute(
        "SELECT w.* " + base + " ORDER BY w.id LIMIT ? OFFSET ?",
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


@router.post("/wishlist")
async def create_item(request: Request, user_id: int = Depends(require_auth)):
    body = await read_json_body(request)
    if body is None:
        raise validation_error("Body must be a JSON object")
    fields = _parse_body(body)
    cursor = conn.execute(
        "INSERT INTO wishlist (user_id, product_id, store_id, target_price, notify, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (
            user_id, fields["product_id"], fields["store_id"],
            fields["target_price"], fields["notify"], now_iso(),
        ),
    )
    return json_response(_to_json(_find(user_id, str(cursor.lastrowid))), status=201)


@router.get("/wishlist/{item_id}")
async def get_item(item_id: str, user_id: int = Depends(require_auth)):
    row = _find(user_id, item_id)
    if row is None:
        raise not_found("Wishlist item not found")
    return json_response(_to_json(row))


@router.put("/wishlist/{item_id}")
async def update_item(
    item_id: str, request: Request, user_id: int = Depends(require_auth)
):
    row = _find(user_id, item_id)
    if row is None:
        raise not_found("Wishlist item not found")
    body = await read_json_body(request)
    if body is None:
        raise validation_error("Body must be a JSON object")
    fields = _parse_body(body)
    conn.execute(
        "UPDATE wishlist SET product_id = ?, store_id = ?, target_price = ?, notify = ? "
        "WHERE id = ?",
        (
            fields["product_id"], fields["store_id"], fields["target_price"],
            fields["notify"], row["id"],
        ),
    )
    return json_response(_to_json(_find(user_id, str(row["id"]))))


@router.delete("/wishlist/{item_id}")
async def delete_item(item_id: str, user_id: int = Depends(require_auth)):
    row = _find(user_id, item_id)
    if row is None:
        raise not_found("Wishlist item not found")
    conn.execute("DELETE FROM wishlist WHERE id = ?", (row["id"],))
    return Response(status_code=204)
