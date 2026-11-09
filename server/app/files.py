import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, Request, Response

from .auth import require_auth
from .db import BASE_DIR, conn, now_iso
from .errors import json_response, not_found, validation_error

MAX_UPLOAD_BYTES = 5 * 1024 * 1024

UPLOADS_DIR = BASE_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter()


def _too_large():
    return validation_error(
        "File too large: the upload limit is 5 MB (%d bytes)" % MAX_UPLOAD_BYTES
    )


@router.post("/files")
async def upload_file(request: Request, user_id: int = Depends(require_auth)):
    declared = request.headers.get("content-length")
    if declared is not None and declared.isdigit():
        if int(declared) > MAX_UPLOAD_BYTES:
            raise _too_large()

    boundary = _multipart_boundary(request.headers.get("content-type", ""))
    if boundary is None:
        raise validation_error("Expected a multipart/form-data body")
    received: List[bytes] = []
    total = 0
    async for chunk in request.stream():
        total += len(chunk)
        if total > MAX_UPLOAD_BYTES:
            raise _too_large()
        received.append(chunk)
    body = b"".join(received)
    try:
        parts = _parse_multipart(body, boundary)
    except ValueError:
        raise validation_error("Malformed multipart/form-data body")

    for headers, content in parts:
        params = _disposition_params(headers.get("content-disposition", ""))
        if params.get("name") != "file":
            continue

        name = params.get("filename") or "file"
        mime_type = headers.get("content-type", "application/octet-stream")

        safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
        stored_path = UPLOADS_DIR / ("%d_%s" % (time.time_ns() // 1000, safe_name))
        stored_path.write_bytes(content)

        cursor = conn.execute(
            "INSERT INTO files (user_id, name, mime_type, size, path, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, name, mime_type, len(content), str(stored_path), now_iso()),
        )
        file_id = cursor.lastrowid

        return json_response(
            {
                "id": file_id,
                "url": "/files/%d" % file_id,
                "name": name,
                "size": len(content),
                "mimeType": mime_type,
            },
            status=201,
        )

    raise validation_error("Missing multipart field 'file'")


@router.get("/files/{file_id}")
async def download_file(file_id: str):
    try:
        parsed_id = int(file_id)
    except ValueError:
        raise not_found("File not found")

    row = conn.execute(
        "SELECT * FROM files WHERE id = ?", (parsed_id,)
    ).fetchone()
    if row is None:
        raise not_found("File not found")

    stored = Path(row["path"])
    if not stored.exists():
        raise not_found("File not found")

    return Response(
        content=stored.read_bytes(),
        headers={
            "Content-Type": row["mime_type"],
            "X-Content-Type-Options": "nosniff",
            "Content-Disposition": "attachment",
            "Content-Security-Policy": "default-src 'none'; sandbox",
        },
    )

def _multipart_boundary(content_type: str) -> Optional[str]:
    if not content_type.lower().startswith("multipart/form-data"):
        return None
    match = re.search(r'boundary=(?:"([^"]+)"|([^;\s]+))', content_type)
    if match is None:
        return None
    return match.group(1) or match.group(2)


def _parse_multipart(
    body: bytes, boundary: str
) -> List[Tuple[Dict[str, str], bytes]]:
    delimiter = b"--" + boundary.encode("utf-8")
    sections = body.split(delimiter)
    if len(sections) < 2 or not sections[-1].startswith(b"--"):
        raise ValueError("missing or unterminated boundary")

    parts = []
    for section in sections[1:-1]:
        if not section.startswith(b"\r\n") or not section.endswith(b"\r\n"):
            raise ValueError("part is not CRLF-delimited")
        section = section[2:-2]

        head, separator, content = section.partition(b"\r\n\r\n")
        if not separator:
            raise ValueError("part has no header/content separator")

        headers: Dict[str, str] = {}
        for line in head.split(b"\r\n"):
            name, colon, value = line.decode("latin-1").partition(":")
            if not colon:
                raise ValueError("malformed part header")
            headers[name.strip().lower()] = value.strip()
        parts.append((headers, content))
    return parts


def _disposition_params(value: str) -> Dict[str, str]:
    params = {}
    for piece in value.split(";")[1:]:
        key, equals, val = piece.strip().partition("=")
        if equals:
            params[key.strip().lower()] = val.strip().strip('"')
    return params
