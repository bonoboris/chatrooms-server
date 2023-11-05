from chatrooms.database.connections import DB
from fastapi.testclient import TestClient
from psycopg.pq import ConnStatus


def test_app_status(client: TestClient):
    resp = client.get("/status")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_db_conn(empty_db: DB):
    assert empty_db.info.user == "test"
    assert empty_db.info.status == ConnStatus.OK
