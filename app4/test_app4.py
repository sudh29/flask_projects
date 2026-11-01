import pytest
import app4.app as app4_module
from app4.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    # Reset in-memory database
    app4_module.todos_db = [
        {"id": 1, "title": "Finish this task", "status": False},
        {"id": 2, "title": "Finish that task", "status": True},
    ]
    app4_module.next_id = 3
    with app.test_client() as client:
        yield client
    app4_module.todos_db = [
        {"id": 1, "title": "Finish this task", "status": False},
        {"id": 2, "title": "Finish that task", "status": True},
    ]
    app4_module.next_id = 3


def test_index_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"html" in response.data.lower()


def test_swagger_json_spec(client):
    response = client.get("/api/swagger.json")
    assert response.status_code == 200
    data = response.get_json()
    assert "openapi" in data
    assert data["openapi"] == "3.0.2"
    assert "paths" in data
    assert "/todo" in data["paths"]


def test_legacy_todo_endpoint(client):
    response = client.get("/todo")
    assert response.status_code == 200
    data = response.get_json()
    assert "todo_list" in data
    assert len(data["todo_list"]) == 2
    assert data["todo_list"][0]["title"] == "Finish this task"


def test_get_todos_api(client):
    response = client.get("/api/todo")
    assert response.status_code == 200
    data = response.get_json()
    assert "todo_list" in data
    assert len(data["todo_list"]) == 2


def test_create_todo_success(client):
    response = client.post("/api/todo", json={"title": "Write unit tests"})
    assert response.status_code == 201
    data = response.get_json()
    assert data["id"] == 3
    assert data["title"] == "Write unit tests"
    assert data["status"] is False

    # Verify it is in list
    res_list = client.get("/api/todo")
    assert len(res_list.get_json()["todo_list"]) == 3


def test_create_todo_missing_title(client):
    res1 = client.post("/api/todo", json={})
    assert res1.status_code == 400
    assert "Title is required" in res1.get_json()["error"]


def test_update_todo_status_and_title(client):
    # Toggle status
    res = client.patch("/api/todo/1", json={"status": True, "title": "Updated task"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["id"] == 1
    assert data["status"] is True
    assert data["title"] == "Updated task"


def test_update_todo_not_found(client):
    res = client.patch("/api/todo/999", json={"status": True})
    assert res.status_code == 404
    assert "Todo not found" in res.get_json()["error"]


def test_delete_todo_success(client):
    res = client.delete("/api/todo/1")
    assert res.status_code == 200
    assert "Todo deleted successfully" in res.get_json()["message"]

    # Verify count decremented
    res_list = client.get("/api/todo")
    assert len(res_list.get_json()["todo_list"]) == 1
    assert res_list.get_json()["todo_list"][0]["id"] == 2


def test_delete_todo_not_found(client):
    res = client.delete("/api/todo/999")
    assert res.status_code == 404
    assert "Todo not found" in res.get_json()["error"]


def test_swagger_docs_endpoint(client):
    res = client.get("/docs")
    assert res.status_code == 200
    assert b"Swagger" in res.data or b"swagger" in res.data or b"html" in res.data.lower()

    res_index = client.get("/docs/index.html")
    assert res_index.status_code == 200
