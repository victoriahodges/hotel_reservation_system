from datetime import datetime

import pytest
from reservation_system.db import get_db


def test_index(client, auth):
    response = client.get("/guests/")
    assert b'href="/auth/login"' in response.data
    assert b"Alice Johnson" not in response.data
    assert b"Edit" not in response.data
    assert response.headers["Location"] == "/auth/login"

    auth.login()
    response = client.get("/guests/")
    assert b"Log out" in response.data
    assert b"Alice Johnson" in response.data
    assert b"alice.johnson@example.com" in response.data
    assert b"2024-05-30 12:59 by test" in response.data
    assert b'href="/guests/1/update"' in response.data


@pytest.mark.parametrize(
    "path",
    (
        "/guests/create",
        "/guests/1/update",
        "/guests/1/delete",
    ),
)
def test_login_required(client, path):
    response = client.post(path)
    assert response.headers["Location"] == "/auth/login"


@pytest.mark.parametrize(
    "path",
    (
        "/guests/3/update",
        "/guests/3/delete",
    ),
)
def test_record_exists(client, auth, path):
    # test data only has 2 records, expects record 3 not found
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
        "guest_notes": "",
    }

    auth.login()
    assert client.get("/guests/create").status_code == 200
    client.post("/guests/create", data=data)

    with app.app_context():
        db = get_db()
        count = db.execute("SELECT COUNT(id) FROM guests").fetchone()[0]
        assert count == 3


@pytest.mark.parametrize(
    "redirect_url, expected",
    [
        ("/reservations/create", "/reservations/create?guest_id=3"),
        ("/calendar/2024/6", "/guests/"),
        ("", "/guests/"),
    ],
)
def test_create_with_redirect(client, auth, app, redirect_url, expected):
    data = {
        "name": "Any Name",
        "email": "anyemail@example.com",
        "telephone": "+44 123456789",
        "address_1": "123 Any Street",
        "address_2": "Anywhere",
        "city": "Anytown",
        "county": "Someshire",
        "postcode": "AB12 3CD",
        "guest_notes": "",
    }

    auth.login()
    assert client.get(f"/guests/create?redirect={redirect_url}").status_code == 200

    response = client.post(f"/guests/create?redirect={redirect_url}", data=data)

    with app.app_context():
        db = get_db()
        count = db.execute("SELECT COUNT(id) FROM guests").fetchone()[0]
        assert count == 3

    assert response.headers["Location"] == expected


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
        "guest_notes": "Some notes",
    }

    auth.login()
    assert client.get("/guests/1/update").status_code == 200
    response = client.post("/guests/1/update", data=data)
    assert response.status_code == 302

    with app.app_context():
        db = get_db()
        result = db.execute("SELECT * FROM guests WHERE id = 1").fetchone()
        assert result["email"] == "updated@example.com"
        assert result["guest_notes"] == "Some notes"


@pytest.mark.parametrize(
    "redirect_url, expected",
    [
        ("/reservations/create", "/reservations/create"),
        (
            f"/calendar/{datetime.now().year}/{datetime.now().month}",
            f"/calendar/{datetime.now().year}/{datetime.now().month}/",
        ),
        ("/calendar/2024/6/", "/calendar/2024/6/"),
        ("", "/guests/"),
    ],
)
def test_update_with_redirect(client, auth, app, redirect_url, expected):
    data = {
        "name": "Any Name",
        "email": "updated@example.com",
        "telephone": "+44 123456789",
        "address_1": "123 Any Street",
        "address_2": "Anywhere",
        "city": "Anytown",
        "county": "Someshire",
        "postcode": "AB12 3CD",
        "guest_notes": "Some notes",
    }

    auth.login()
    assert client.get(f"/guests/1/update?redirect={redirect_url}").status_code == 200
    response = client.post(f"/guests/1/update?redirect={redirect_url}", data=data)
    assert response.status_code == 302

    with app.app_context():
        db = get_db()
        result = db.execute("SELECT * FROM guests WHERE id = 1").fetchone()
        assert result["email"] == "updated@example.com"
        assert result["guest_notes"] == "Some notes"

    assert response.headers["Location"] == expected


@pytest.mark.parametrize(
    "path",
    (
        "/guests/create",
        "/guests/1/update",
    ),
)
def test_create_update_validate(client, auth, path):
    data = {
        "name": "",
        "email": "anyemail@example.com",
        "telephone": "+44 123456789",
        "address_1": "123 Any Street",
        "address_2": "Anywhere",
        "city": "",
        "county": "Someshire",
        "postcode": "AB12 3CD",
        "guest_notes": "",
    }
    auth.login()
    response = client.post(path, data=data)
    assert b"Name is required." in response.data
    assert b"City is required." in response.data


def test_delete(client, auth, app):
    auth.login()
    response = client.post("/guests/1/delete")
    assert response.headers["Location"] == "/guests/"

    with app.app_context():
        db = get_db()
        post = db.execute("SELECT * FROM guests WHERE id = 1").fetchone()
        assert post is None
