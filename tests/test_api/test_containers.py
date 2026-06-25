from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.database import init_main_db, init_lake_db
from backend.app.seed import seed_if_empty

client = TestClient(app)


def setup_module():
    init_main_db()
    init_lake_db()
    seed_if_empty()


class TestContainerAPI:
    def test_list_containers(self):
        resp = client.get("/api/containers")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 5

    def test_get_container(self):
        resp = client.get("/api/containers/1")
        assert resp.status_code == 200
        assert resp.json()["id"] == 1

    def test_get_container_not_found(self):
        resp = client.get("/api/containers/9999")
        assert resp.status_code == 404

    def test_create_container(self):
        resp = client.post("/api/containers", json={
            "name": "Test Container",
            "description": "A test",
            "schema_def": {
                "fields": [
                    {"name": "title", "type": "string", "description": "Title", "selector": "h1", "selector_type": "css", "required": True}
                ]
            },
        })
        assert resp.status_code == 201
        assert resp.json()["name"] == "Test Container"

    def test_update_container(self):
        resp = client.put("/api/containers/1", json={
            "description": "Updated description",
        })
        assert resp.status_code == 200
        assert resp.json()["description"] == "Updated description"

    def test_delete_container(self):
        resp = client.post("/api/containers", json={
            "name": "Delete Me",
            "description": "",
            "schema_def": {"fields": []},
        })
        cid = resp.json()["id"]
        resp = client.delete(f"/api/containers/{cid}")
        assert resp.status_code == 200
        resp = client.get(f"/api/containers/{cid}")
        assert resp.status_code == 404
