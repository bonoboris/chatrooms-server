from chatrooms.database.connections import DB
from fastapi.testclient import TestClient


async def test_login(client: TestClient, db: DB):
    resp = client.get("/users/current")
    assert resp.status_code == 401

    resp = client.post("/login", data={"username": "user", "password": "pass"})
    assert resp.is_success
    data = resp.json()
    assert "token_type" in data
    assert "access_token" in data
    token = data["token_type"] + " " + data["access_token"]

    resp = client.get("/users/current", headers={"Authorization": token})
    assert resp.status_code == 200


async def test_login_bad_username(client: TestClient, db: DB):
    resp = client.post("/login", data={"username": "who_dis", "password": "pass"})
    assert resp.is_error


async def test_login_bad_password(client: TestClient, db: DB):
    resp = client.post("/login", data={"username": "user", "password": "motdepasse"})
    assert resp.is_error
