"""Тесты запускаются на временной базе: DB_PATH задаётся до импорта app."""
import os
import sys
import tempfile
from pathlib import Path

_TMP = tempfile.mkdtemp(prefix="techprice-test-")
os.environ["DB_PATH"] = str(Path(_TMP) / "test.db")
os.environ.setdefault("SEED_DEMO", "1")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client() -> TestClient:
    c = TestClient(app)
    r = c.post("/auth/register",
               json={"email": "test@example.com", "password": "secret", "name": "Test"})
    c.headers["Authorization"] = "Bearer " + r.json()["token"]
    return c
