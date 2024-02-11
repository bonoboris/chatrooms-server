import pytest
from fastapi import status
from fastapi.testclient import TestClient

pytestmark = pytest.mark.usefixtures("db")


async def test_login(client: TestClient):
    resp = client.get("/users/current")
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    resp = client.post("/login", data={"username": "user", "password": "pass"})
    assert resp.is_success
    data = resp.json()
    assert "token_type" in data
    assert "access_token" in data
    token = data["token_type"] + " " + data["access_token"]

    resp = client.get("/users/current", headers={"Authorization": token})
    assert resp.status_code == status.HTTP_200_OK


async def test_login_bad_username(client: TestClient):
    resp = client.post("/login", data={"username": "who_dis", "password": "pass"})
    assert resp.is_error


async def test_login_bad_password(client: TestClient):
    resp = client.post("/login", data={"username": "user", "password": "motdepasse"})
    assert resp.is_error
