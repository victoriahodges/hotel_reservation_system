import pytest
from reservation_system.db import get_db


def test_index(client, auth):
    response = client.get("/rooms/")
    assert b'href="/auth/login"' in response.data
    assert b"Room Type" not in response.data
    assert b"Edit" not in response.data
    assert response.headers["Location"] == "/auth/login"

    auth.login()
    response = client.get("/rooms/")
    assert b"Log out" in response.data
    assert b"Room Type" in response.data
    assert b"101" in response.data
    assert b"Superior Double" in response.data
    assert b'href="/rooms/1/update"' in response.data


@pytest.mark.parametrize(
    "path",
    (
        "/rooms/create",
        "/rooms/1/update",
        "/rooms/1/delete",
    ),
)
def test_login_required(client, path):
    response = client.post(path)
    assert response.headers["Location"] == "/auth/login"


@pytest.mark.parametrize(
    "path",
    (
        "/rooms/3/update",
        "/rooms/3/delete",
    ),
)
def test_record_exists(client, auth, path):
    # test data only has 2 records, expects record 3 not found
    auth.login()
    assert client.post(path).status_code == 404


def test_create(client, auth, app):
    data = {
        "room_number": "102",
        "room_type": "1",
    }

    auth.login()
    assert client.get("/rooms/create").status_code == 200
    client.post("/rooms/create", data=data)

    with app.app_context():
        db = get_db()
        count = db.execute("SELECT COUNT(id) FROM rooms").fetchone()[0]
        assert count == 3


def test_update(client, auth, app):
    data = {
        "room_number": "102",
        "room_type": "3",
    }

    auth.login()
    assert client.get("/rooms/1/update").status_code == 200
    res = client.post("/rooms/1/update", data=data)
    assert res.status_code == 302

    with app.app_context():
        db = get_db()
        res = db.execute("SELECT * FROM rooms WHERE id = 1").fetchone()
        assert res["room_number"] == 102
        assert res["room_type"] == 3


@pytest.mark.parametrize(
    "path",
    (
        "/rooms/create",
        "/rooms/1/update",
    ),
)
def test_create_update_validate(client, auth, path):
    data = {
        "room_number": "",
        "room_type": "",
    }
    auth.login()
    response = client.post(path, data=data)
    assert b"Room Number is required." in response.data
    assert b"Room Type is required." in response.data


def test_delete(client, auth, app):
    auth.login()
    response = client.post("/rooms/1/delete")
    assert response.headers["Location"] == "/rooms/"

    with app.app_context():
        db = get_db()
        post = db.execute("SELECT * FROM rooms WHERE id = 1").fetchone()
        assert post is None
