from typing import Any

import pytest
from chatrooms.database.connections import DB
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _use_user_app(user_app: FastAPI):  # pyright: ignore[reportUnusedFunction]
    pass


async def test_create_todo(client: TestClient, db: DB):
    payload = {"status": "in progress", "description": "test the API"}
    resp = client.post("/todos", json=payload)
    assert resp.is_success
    data = resp.json()
    assert "status" in data
    assert data["status"] == payload["status"]
    assert "description" in data
    assert data["description"] == payload["description"]
    assert "id" in data
    id = data["id"]

    cur = await db.execute("SELECT * FROM todos WHERE created_by = %s", [id])
    todo_db = await cur.fetchone()
    assert todo_db is not None
    assert "status" in todo_db
    assert todo_db["status"] == payload["status"]
    assert "description" in todo_db
    assert todo_db["description"] == payload["description"]


async def test_get_todos(client: TestClient):
    resp = client.get("/todos")
    assert resp.is_success
    data: list[dict[str, Any]] = resp.json()
    assert isinstance(data, list)
    assert len(data) == 1


async def test_get_todos_another_user(client: TestClient, another_user_app: FastAPI):
    resp = client.get("/todos")
    assert resp.is_success
    data: list[dict[str, Any]] = resp.json()
    assert isinstance(data, list)
    assert len(data) == 0


async def test_update_doto(client: TestClient, db: DB):
    payload = client.get("/todos").json()[0]
    id = payload.pop("id")
    payload["description"] = "Updated description"
    resp = client.put(f"/todos/{id}", json=payload)
    assert resp.is_success
    data = resp.json()
    assert "status" in data
    assert data["status"] == payload["status"]
    assert "description" in data
    assert data["description"] == payload["description"]
    assert "id" in data
    id = data["id"]

    cur = await db.execute("SELECT * FROM todos WHERE created_by = %s", [id])
    todo_db = await cur.fetchone()
    assert todo_db is not None
    assert "status" in todo_db
    assert todo_db["status"] == payload["status"]
    assert "description" in todo_db
    assert todo_db["description"] == payload["description"]
