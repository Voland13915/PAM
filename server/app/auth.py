import os
import time
from typing import Optional

import bcrypt
import jwt  # PyJWT
from fastapi import APIRouter, Depends, Request

from .db import conn, now_iso
from .errors import (
    email_taken,
    json_response,
    read_json_body,
    string_field,
    unauthorized,
    validation_error,
)

JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-me")

TOKEN_LIFETIME_SECONDS = 7 * 24 * 60 * 60  # 7 days

router = APIRouter()

def issue_token(user_id: int) -> str:
    now = int(time.time())
    return jwt.encode(
        {"sub": str(user_id), "iat": now, "exp": now + TOKEN_LIFETIME_SECONDS},
        JWT_SECRET,
        algorithm="HS256",
    )


def verify_token(token: str) -> Optional[int]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        return None


async def require_auth(request: Request) -> int:
    header = request.headers.get("authorization", "")
    if not header.startswith("Bearer "):
        raise unauthorized()
    user_id = verify_token(header[len("Bearer "):])
    if user_id is None:
        raise unauthorized()
    return user_id

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode(
        "ascii"
    )


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"), stored_hash.encode("ascii")
        )
    except ValueError:
        return False

@router.post("/auth/register")
async def register(request: Request):
    body = await read_json_body(request)
    if body is None:
        raise validation_error("Body must be a JSON object")

    email = string_field(body, "email")
    password = string_field(body, "password")
    name = string_field(body, "name")
    if email is None or "@" not in email:
        raise validation_error("A valid email is required")
    if password is None:
        raise validation_error("password is required")
    if name is None:
        raise validation_error("name is required")

    existing = conn.execute(
        "SELECT id FROM users WHERE email = ?", (email,)
    ).fetchone()
    if existing is not None:
        raise email_taken()

    cursor = conn.execute(
        "INSERT INTO users (email, password_hash, name, created_at) "
        "VALUES (?, ?, ?, ?)",
        (email, hash_password(password), name, now_iso()),
    )
    user_id = cursor.lastrowid

    return json_response(
        {
            "token": issue_token(user_id),
            "user": {"id": user_id, "email": email, "name": name},
        },
        status=201,
    )


@router.post("/auth/login")
async def login(request: Request):
    body = await read_json_body(request)
    email = None if body is None else string_field(body, "email")
    password = None if body is None else string_field(body, "password")
    if email is None or password is None:
        raise unauthorized("Invalid email or password")

    user = conn.execute(
        "SELECT * FROM users WHERE email = ?", (email,)
    ).fetchone()
    if user is None:
        raise unauthorized("Invalid email or password")

    if not verify_password(password, user["password_hash"]):
        raise unauthorized("Invalid email or password")

    return json_response(
        {
            "token": issue_token(user["id"]),
            "user": {
                "id": user["id"],
                "email": user["email"],
                "name": user["name"],
            },
        }
    )


@router.get("/me")
async def me(user_id: int = Depends(require_auth)):
    user = conn.execute(
        "SELECT id, email, name FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    if user is None:
        raise unauthorized()
    return json_response(
        {"id": user["id"], "email": user["email"], "name": user["name"]}
    )
