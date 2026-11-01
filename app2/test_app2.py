import pytest
from unittest.mock import patch, MagicMock
import requests

try:
    from app2.app import app
except ImportError:
    from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


MOCK_SO_RESPONSE = {
    "items": [
        {
            "title": "How to mock in pytest?",
            "link": "https://stackoverflow.com/q/12345",
            "answer_count": 0,
            "tags": ["python", "pytest"],
            "score": 5,
            "creation_date": 1700000000,
        },
        {
            "title": "Already answered question",
            "link": "https://stackoverflow.com/q/99999",
            "answer_count": 2,
            "tags": ["python"],
            "score": 10,
            "creation_date": 1699990000,
        },
        {
            "title": "Another unanswered question",
            "link": "https://stackoverflow.com/q/54321",
            "answer_count": 0,
            "tags": ["flask"],
            "score": 1,
            "creation_date": 1700000500,
        },
    ]
}


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "healthy"}


@patch("app2.app.requests.get")
def test_api_questions_success(mock_get, client):
    mock_response = MagicMock()
    mock_response.json.return_value = MOCK_SO_RESPONSE
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    response = client.get("/api/questions")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["count"] == 2
    titles = [q["title"] for q in data["questions"]]
    assert "How to mock in pytest?" in titles
    assert "Another unanswered question" in titles
    assert "Already answered question" not in titles


@patch("app2.app.requests.get")
def test_api_questions_error(mock_get, client):
    mock_get.side_effect = requests.RequestException("Network timeout")

    response = client.get("/api/questions")
    assert response.status_code == 500
    data = response.get_json()
    assert data["success"] is False
    assert "Network timeout" in data["error"]


@patch("app2.app.requests.get")
def test_index_page_success(mock_get, client):
    mock_response = MagicMock()
    mock_response.json.return_value = MOCK_SO_RESPONSE
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    response = client.get("/")
    assert response.status_code == 200
    assert b"How to mock in pytest?" in response.data
    assert b"Another unanswered question" in response.data


@patch("app2.app.requests.get")
def test_index_page_error(mock_get, client):
    mock_get.side_effect = requests.RequestException("API Down")

    response = client.get("/")
    assert response.status_code == 500
    data = response.get_json()
    assert data["success"] is False
    assert "API Down" in data["error"]
