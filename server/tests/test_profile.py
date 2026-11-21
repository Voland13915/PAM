import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def user() -> TestClient:
    c = TestClient(app)
    email = "profile-%d@example.com" % id(c)
    r = c.post("/auth/register", json={"email": email, "password": "secret1", "name": "Old"})
    c.headers["Authorization"] = "Bearer " + r.json()["token"]
    c.email = email
    return c


def test_rename(user):
    r = user.patch("/me", json={"name": "  Даниил  "})
    assert r.status_code == 200
    assert r.json()["name"] == "Даниил"
    assert user.get("/me").json()["name"] == "Даниил"


def test_rename_rejects_empty_and_long(user):
    assert user.patch("/me", json={"name": "   "}).status_code == 400
    assert user.patch("/me", json={"name": "x" * 61}).status_code == 400
    assert user.get("/me").json()["name"] == "Old"


def test_rename_requires_token():
    assert TestClient(app).patch("/me", json={"name": "X"}).status_code == 401


def test_change_password(user):
    r = user.post("/me/password", json={"currentPassword": "secret1", "newPassword": "newpass"})
    assert r.status_code == 200
    login = TestClient(app).post("/auth/login", json={"email": user.email, "password": "newpass"})
    assert login.status_code == 200
    old = TestClient(app).post("/auth/login", json={"email": user.email, "password": "secret1"})
    assert old.status_code == 401


def test_change_password_wrong_current(user):
    r = user.post("/me/password", json={"currentPassword": "nope", "newPassword": "newpass"})
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "WRONG_PASSWORD"


def test_change_password_too_short(user):
    r = user.post("/me/password", json={"currentPassword": "secret1", "newPassword": "123"})
    assert r.status_code == 400
