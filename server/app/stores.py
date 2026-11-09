from typing import Optional

from fastapi import APIRouter, Depends, Request

from .auth import require_auth
from .db import conn
from .errors import json_response, not_found

router = APIRouter()


def _to_json(row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "website": row["website"],
        "productsTracked": row["products_tracked"],
        "lastSync": row["last_sync"],
    }


def _int_or(value: Optional[str], default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@router.get("/stores")
async def list_stores(request: Request, user_id: int = Depends(require_auth)):
    """GET /stores?page=1&limit=20&search=  -> {items, page, limit, total}"""
    query = request.query_params
    page = max(_int_or(query.get("page"), 1), 1)
    limit = min(max(_int_or(query.get("limit"), 20), 1), 100)
    search = query.get("search", "")

    where = "ULOWER(name) LIKE ULOWER(?) OR ULOWER(website) LIKE ULOWER(?)"
    args = ("%" + search + "%", "%" + search + "%")

    total = conn.execute(
        "SELECT COUNT(*) AS n FROM stores WHERE " + where, args
    ).fetchone()["n"]
    rows = conn.execute(
        "SELECT * FROM stores WHERE " + where + " ORDER BY id LIMIT ? OFFSET ?",
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


@router.get("/stores/{store_id}")
async def get_store(store_id: str, user_id: int = Depends(require_auth)):
    """GET /stores/{id} -> 200 store | 404"""
    try:
        sid = int(store_id)
    except (TypeError, ValueError):
        raise not_found("Store not found")
    row = conn.execute("SELECT * FROM stores WHERE id = ?", (sid,)).fetchone()
    if row is None:
        raise not_found("Store not found")
    return json_response(_to_json(row))
