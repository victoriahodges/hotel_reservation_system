import pytest
from reservation_system.db import get_db


def test_index(client, auth):
    response = client.get("/special_offers/")
    assert b'href="/auth/login"' in response.data
    assert b"Room Type" not in response.data
    assert b"Edit" not in response.data
    assert response.headers["Location"] == "/auth/login"

    auth.login()
    response = client.get("/special_offers/")
    assert b"Log out" in response.data
    assert b"Room Type" in response.data
    assert b"120" in response.data
    assert b"Superior Double" in response.data
    assert b'href="/special_offers/1/update"' in response.data


@pytest.mark.parametrize(
    "path",
    (
        "/special_offers/create",
        "/special_offers/1/update",
        "/special_offers/1/delete",
    ),
)
def test_login_required(client, path):
    response = client.post(path)
    assert response.headers["Location"] == "/auth/login"


@pytest.mark.parametrize(
    "path",
    (
        "/special_offers/3/update",
        "/special_offers/3/delete",
    ),
)
def test_record_exists(client, auth, path):
    # test data only has 2 records, expects record 3 not found
    auth.login()
    assert client.post(path).status_code == 404


def test_create(client, auth, app):
    data = {
        "title": "Some test offer",
        "room_type": 1,
        "price_per_night": 55,
        "start_date": "2024-09-01",
        "end_date": "2024-09-30",
        "is_enabled": 1,
    }

    auth.login()
    assert client.get("/special_offers/create").status_code == 200
    client.post("/special_offers/create", data=data)

    with app.app_context():
        db = get_db()
        count = db.execute("SELECT COUNT(id) FROM special_offers").fetchone()[0]
        assert count == 3


def test_update(client, auth, app):
    data = {
        "title": "Some test offer",
        "room_type": 1,
        "price_per_night": 55,
        "start_date": "2024-09-01",
        "end_date": "2024-09-30",
        "is_enabled": 0,
    }

    auth.login()
    assert client.get("/special_offers/1/update").status_code == 200
    res = client.post("/special_offers/1/update", data=data)
    assert res.status_code == 302

    with app.app_context():
        db = get_db()
        res = db.execute("SELECT * FROM special_offers WHERE id = 1").fetchone()
        assert res["title"] == "Some test offer"
        assert res["room_type"] == 1


@pytest.mark.parametrize(
    "path",
    (
        "/special_offers/create",
        "/special_offers/1/update",
    ),
)
def test_create_update_validate(client, auth, path):
    data = {
        "title": "",
        "room_type": 1,
        "price_per_night": "",
        "start_date": "2024-09-01",
        "end_date": "2024-09-30",
        "is_enabled": 0,
    }
    auth.login()
    response = client.post(path, data=data)
    assert b"Title is required." in response.data
    assert b"Price Per Night is required." in response.data


def test_delete(client, auth, app):
    auth.login()
    response = client.post("/special_offers/1/delete")
    assert response.headers["Location"] == "/special_offers/"

    with app.app_context():
        db = get_db()
        post = db.execute("SELECT * FROM special_offers WHERE id = 1").fetchone()
        assert post is None
