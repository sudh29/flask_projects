from datetime import time, date
import io
import pytest
from app3.app import app, is_time_in_range, extract_data, extract_items


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


SAMPLE_CSV = b"""itemname,available_timings,exclude_dates,exclude_days
Dosa,"07:00-11:00,16:00-21:00","25-12-2024","Monday"
Pizza,"12:00-23:00","","Sunday"
LateNightSnack,"22:00-03:00","",""
"""


def test_is_time_in_range_normal():
    start = time(8, 0)
    end = time(18, 0)

    assert is_time_in_range(start, end, time(12, 0)) is True
    assert is_time_in_range(start, end, time(8, 0)) is True
    assert is_time_in_range(start, end, time(18, 0)) is True
    assert is_time_in_range(start, end, time(7, 59)) is False
    assert is_time_in_range(start, end, time(18, 1)) is False


def test_is_time_in_range_midnight_spanning():
    start = time(22, 0)
    end = time(2, 0)

    assert is_time_in_range(start, end, time(23, 0)) is True
    assert is_time_in_range(start, end, time(1, 0)) is True
    assert is_time_in_range(start, end, time(22, 0)) is True
    assert is_time_in_range(start, end, time(2, 0)) is True
    assert is_time_in_range(start, end, time(12, 0)) is False
    assert is_time_in_range(start, end, time(21, 59)) is False


def test_extract_data():
    result = extract_data(SAMPLE_CSV)
    assert "Dosa" in result
    assert "Pizza" in result
    assert "LateNightSnack" in result
    assert result["Dosa"]["available_timings"] == "07:00-11:00,16:00-21:00"
    assert result["Dosa"]["exclude_dates"] == "25-12-2024"
    assert result["Dosa"]["exclude_days"] == "Monday"


def test_extract_items_date_exclusion():
    data = extract_data(SAMPLE_CSV)
    # On 25-12-2024 (excluded for Dosa) at 08:00 on Wednesday
    items = extract_items(data, time(8, 0), date(2024, 12, 25), "Wednesday")
    assert "Dosa" not in items

    # On 26-12-2024 at 08:00 on Thursday (not excluded)
    items_next_day = extract_items(data, time(8, 0), date(2024, 12, 26), "Thursday")
    assert "Dosa" in items_next_day


def test_extract_items_day_exclusion():
    data = extract_data(SAMPLE_CSV)
    # On Monday (excluded for Dosa)
    items_mon = extract_items(data, time(8, 0), date(2024, 12, 23), "Monday")
    assert "Dosa" not in items_mon

    # On Sunday (excluded for Pizza)
    items_sun = extract_items(data, time(14, 0), date(2024, 12, 22), "Sunday")
    assert "Pizza" not in items_sun


def test_extract_items_midnight_spanning():
    data = extract_data(SAMPLE_CSV)
    # LateNightSnack at 23:30
    items = extract_items(data, time(23, 30), date(2024, 12, 24), "Tuesday")
    assert "LateNightSnack" in items

    # LateNightSnack at 02:30
    items_early = extract_items(data, time(2, 30), date(2024, 12, 24), "Tuesday")
    assert "LateNightSnack" in items_early

    # LateNightSnack at 04:00 (closed)
    items_closed = extract_items(data, time(4, 0), date(2024, 12, 24), "Tuesday")
    assert "LateNightSnack" not in items_closed


def test_index_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"html" in response.data.lower()


def test_set_time_api(client):
    response = client.get("/api/set-time")
    assert response.status_code == 200
    data = response.get_json()
    assert "current_time" in data
    # Check cookie was set
    assert "current_time" in response.headers.get("Set-Cookie", "")


def test_menu_missing_file(client):
    response = client.post("/Menu/")
    assert response.status_code == 400
    assert b"No file part" in response.data


def test_menu_missing_cookie(client):
    data = {"data": (io.BytesIO(SAMPLE_CSV), "menu.csv")}
    response = client.post("/Menu/", data=data, content_type="multipart/form-data")
    assert response.status_code == 400
    assert b"No current time set in cookies" in response.data


def test_menu_with_valid_cookie_available(client):
    # Set current time to a Tuesday 08:30 (when Dosa is available)
    timestamp = "2024-12-24T08:30:00"
    client.set_cookie("current_time", timestamp)

    data = {"data": (io.BytesIO(SAMPLE_CSV), "menu.csv")}
    response = client.post("/Menu/", data=data, content_type="multipart/form-data")
    assert response.status_code == 200
    res_json = response.get_json()
    assert "Dosa" in res_json["Item available"]
    assert "Pizza" not in res_json["Item available"]


def test_menu_with_valid_cookie_none_available(client):
    # Set current time to 04:00 (when nothing is available)
    timestamp = "2024-12-24T04:00:00"
    client.set_cookie("current_time", timestamp)

    data = {"data": (io.BytesIO(SAMPLE_CSV), "menu.csv")}
    response = client.post("/Menu/", data=data, content_type="multipart/form-data")
    assert response.status_code == 200
    res_json = response.get_json()
    assert res_json["Item available"] is None
