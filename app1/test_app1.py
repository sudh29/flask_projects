import pytest
try:
    from app1.app import app, stores
except ImportError:
    from app import app, stores


@pytest.fixture
def client():
    app.config["TESTING"] = True
    # Save original stores and restore after test
    original_stores = [
        {"name": "beautiful store", "items": [{"name": "flowers", "price": 100}]},
        {"name": "beautiful store 2", "items": [{"name": "books", "price": 100}]},
    ]
    stores.clear()
    stores.extend([
        {"name": s["name"], "items": list(s["items"])}
        for s in original_stores
    ])
    with app.test_client() as client:
        yield client
    stores.clear()
    stores.extend([
        {"name": s["name"], "items": list(s["items"])}
        for s in original_stores
    ])


def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Flask Store API" in response.data or b"html" in response.data.lower()


def test_api_info(client):
    response = client.get("/api")
    assert response.status_code == 200
    data = response.get_json()
    assert "endpoints" in data
    assert data["version"] == "1.0.0"


def test_get_all_stores(client):
    response = client.get("/store")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["count"] == 2
    assert len(data["stores"]) == 2


def test_create_store_success(client):
    response = client.post("/store", json={"name": "New Bakery"})
    assert response.status_code == 201
    data = response.get_json()
    assert data["success"] is True
    assert data["store"]["name"] == "New Bakery"
    assert data["store"]["items"] == []


def test_create_store_non_json(client):
    response = client.post("/store", data="name=New Bakery")
    assert response.status_code == 415


def test_create_store_missing_or_empty_name(client):
    res1 = client.post("/store", json={})
    assert res1.status_code == 400

    res2 = client.post("/store", json={"name": "   "})
    assert res2.status_code == 400


def test_create_store_duplicate(client):
    response = client.post("/store", json={"name": "beautiful store"})
    assert response.status_code == 409
    data = response.get_json()
    assert data["success"] is False


def test_get_store_by_name(client):
    response = client.get("/store/beautiful store")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["store"]["name"] == "beautiful store"


def test_get_store_not_found(client):
    response = client.get("/store/non_existent_store")
    assert response.status_code == 404
    data = response.get_json()
    assert data["success"] is False


def test_add_item_to_store_success(client):
    response = client.post(
        "/store/beautiful store/item",
        json={"name": "roses", "price": 49.99},
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["success"] is True
    assert data["item"]["name"] == "roses"
    assert data["item"]["price"] == 49.99


def test_add_item_non_existent_store(client):
    response = client.post(
        "/store/missing_store/item",
        json={"name": "roses", "price": 49.99},
    )
    assert response.status_code == 404


def test_add_item_validation(client):
    # Missing price
    res1 = client.post("/store/beautiful store/item", json={"name": "roses"})
    assert res1.status_code == 400

    # Negative price
    res2 = client.post("/store/beautiful store/item", json={"name": "roses", "price": -5})
    assert res2.status_code == 400

    # Invalid price type
    res3 = client.post("/store/beautiful store/item", json={"name": "roses", "price": "free"})
    assert res3.status_code == 400

    # Duplicate item
    client.post("/store/beautiful store/item", json={"name": "tulip", "price": 10})
    res4 = client.post("/store/beautiful store/item", json={"name": "tulip", "price": 15})
    assert res4.status_code == 409


def test_get_store_items(client):
    response = client.get("/store/beautiful store/item")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["count"] == 1
    assert data["items"][0]["name"] == "flowers"


def test_delete_store(client):
    res_del = client.delete("/store/beautiful store")
    assert res_del.status_code == 200
    assert res_del.get_json()["success"] is True

    # Confirm store no longer exists
    res_check = client.get("/store/beautiful store")
    assert res_check.status_code == 404

    # Second delete returns 404
    res_del2 = client.delete("/store/beautiful store")
    assert res_del2.status_code == 404
