import pytest
from reservation_system.db import get_db


def test_index(client, auth):
    response = client.get("/reservation_status/")
    assert b'href="/auth/login"' in response.data
    assert b"confirmed by email" not in response.data
    assert b"Edit" not in response.data
    assert response.headers["Location"] == "/auth/login"

    auth.login()
    response = client.get("/reservation_status/")
    assert b"Log out" in response.data
    assert b"Confirmed" in response.data
    assert b"Guest has checked into their room." in response.data
    assert b'href="/reservation_status/1/update"' in response.data


@pytest.mark.parametrize(
    "path",
    (
        "/reservation_status/create",
        "/reservation_status/1/update",
        "/reservation_status/1/delete",
    ),
)
def test_login_required(client, path):
    response = client.post(path)
    assert response.headers["Location"] == "/auth/login"


@pytest.mark.parametrize(
    "path",
    (
        "/reservation_status/3/update",
        "/reservation_status/3/delete",
    ),
)
def test_record_exists(client, auth, path):
    # test data only has 2 records, expects record 3 not found
    auth.login()
    assert client.post(path).status_code == 404


def test_create(client, auth, app):
    data = {
        "status": "Cancelled",
        "description": "Booking was cancelled",
        "bg_color": "#f66151",
    }

    auth.login()
    assert client.get("/reservation_status/create").status_code == 200
    client.post("/reservation_status/create", data=data)

    with app.app_context():
        db = get_db()
        count = db.execute("SELECT COUNT(id) FROM reservation_status").fetchone()[0]
        assert count == 3


def test_update(client, auth, app):
    data = {
        "status": "Cancelled",
        "description": "Booking was cancelled",
        "bg_color": "#f66151",
    }

    auth.login()
    assert client.get("/reservation_status/1/update").status_code == 200
    res = client.post("/reservation_status/1/update", data=data)
    assert res.status_code == 302

    with app.app_context():
        db = get_db()
        res = db.execute("SELECT * FROM reservation_status WHERE id = 1").fetchone()
        assert res["status"] == "Cancelled"
        assert res["bg_color"] == "#f66151"


@pytest.mark.parametrize(
    "path",
    (
        "/reservation_status/create",
        "/reservation_status/1/update",
    ),
)
def test_create_update_validate(client, auth, path):
    data = {
        "status": "",
        "description": "",
        "bg_color": "#f66151",
    }
    auth.login()
    response = client.post(path, data=data)
    assert b"Status is required." in response.data


def test_delete(client, auth, app):
    auth.login()
    response = client.post("/reservation_status/1/delete")
    assert response.headers["Location"] == "/reservation_status/"

    with app.app_context():
        db = get_db()
        post = db.execute("SELECT * FROM reservation_status WHERE id = 1").fetchone()
        assert post is None
