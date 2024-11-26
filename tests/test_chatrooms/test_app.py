from fastapi import status
from fastapi.testclient import TestClient
from psycopg.pq import ConnStatus

from chatrooms.database.connections import DB


def test_app_status(client: TestClient):
    resp = client.get("/status")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json() == {"status": "ok"}


async def test_db_conn(empty_db: DB):
    assert empty_db.info.status == ConnStatus.OK
