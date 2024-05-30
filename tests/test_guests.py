import pytest
from reservation_system.db import get_db


def test_index(client, auth):
    response = client.get("/")
    assert b"Log In" in response.data
    assert b"Register" in response.data

    auth.login()
    response = client.get("/")
    assert b"Log Out" in response.data
    assert b"Alice Johnson" in response.data
    assert b"alice.johnson@example.com" in response.data
    assert b"2024-05-30 12:59 by test" in response.data
    assert b'href="/1/update"' in response.data


@pytest.mark.parametrize(
    "path",
    (
        "/create",
        "/1/update",
        "/1/delete",
    ),
)
def test_login_required(client, path):
    response = client.post(path)
    assert response.headers["Location"] == "/auth/login"


@pytest.mark.parametrize(
    "path",
    (
        "/2/update",
        "/2/delete",
    ),
)
def test_exists_required(client, auth, path):
    auth.login()
    assert client.post(path).status_code == 404


def test_create(client, auth, app):
    data = {
        "name": "Any Name",
        "email": "anyemail@example.com",
        "telephone": "+44 123456789",
        "address_1": "123 Any Street",
        "address_2": "Anywhere",
        "city": "Anytown",
        "county": "Someshire",
        "postcode": "AB12 3CD",
        "notes": "",
    }

    auth.login()
    assert client.get("/create").status_code == 200
    client.post("/create", data=data)

    with app.app_context():
        db = get_db()
        count = db.execute("SELECT COUNT(id) FROM guests").fetchone()[0]
        assert count == 2


def test_update(client, auth, app):
    data = {
        "name": "Any Name",
        "email": "updated@example.com",
        "telephone": "+44 123456789",
        "address_1": "123 Any Street",
        "address_2": "Anywhere",
        "city": "Anytown",
        "county": "Someshire",
        "postcode": "AB12 3CD",
        "notes": "Some notes",
    }

    auth.login()
    assert client.get("/1/update").status_code == 200
    res = client.post("/1/update", data=data)
    assert res.status_code == 302

    with app.app_context():
        db = get_db()
        guest = db.execute("SELECT * FROM guests WHERE id = 1").fetchone()
        assert guest["email"] == "updated@example.com"
        assert guest["notes"] == "Some notes"


@pytest.mark.parametrize(
    "path",
    (
        "/create",
        "/1/update",
    ),
)
def test_create_update_validate(client, auth, path):
    data = {
        "name": "",
        "email": "anyemail@example.com",
        "telephone": "+44 123456789",
        "address_1": "123 Any Street",
        "address_2": "Anywhere",
        "city": "Anytown",
        "county": "Someshire",
        "postcode": "AB12 3CD",
        "notes": "",
    }
    auth.login()
    response = client.post(path, data=data)
    assert b"Name is required." in response.data


def test_delete(client, auth, app):
    auth.login()
    response = client.post("/1/delete")
    assert response.headers["Location"] == "/"

    with app.app_context():
        db = get_db()
        post = db.execute("SELECT * FROM guests WHERE id = 1").fetchone()
        assert post is None
