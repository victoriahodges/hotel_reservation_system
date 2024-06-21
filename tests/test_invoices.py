from datetime import datetime

import pytest
from reservation_system.db import get_db


def test_index(client, auth):
    response = client.get("/invoices/")
    assert b'href="/auth/login"' in response.data
    assert b"Alice Johnson" not in response.data
    assert b"Edit" not in response.data
    assert response.headers["Location"] == "/auth/login"

    auth.login()
    response = client.get("/invoices/")
    assert b"Log out" in response.data
    assert b"Alice Johnson" in response.data
    assert b"785.00" in response.data
    assert b"2024-05-30 12:59 by test" in response.data
    assert b'href="/invoices/2/view"' in response.data


@pytest.mark.parametrize(
    "path, method",
    [
        ("/invoices/create", "post"),
        ("/invoices/1/view", "get"),
        ("/invoices/1/update", "post"),
    ],
)
def test_login_required(client, path, method):
    if method == "get":
        response = client.get(path)
        assert response.headers["Location"] == "/auth/login"
    if method == "post":
        response = client.post(path)
        assert response.headers["Location"] == "/auth/login"


@pytest.mark.parametrize(
    "path, method",
    [
        ("/invoices/3/view", "get"),
        ("/invoices/3/create", "post"),
    ],
)
def test_record_exists(client, auth, path, method):
    # test data only has 2 records, expects record 3 not found
    auth.login()
    if method == "get":
        assert client.get(path).status_code == 404
    if method == "post":
        assert client.post(path).status_code == 404


def test_create(client, auth, app):
    data = {
        "reservation_id": 1,
    }

    auth.login()
    # no page is returned when generating an invoice
    assert client.get("/invoices/create").status_code == 302
    client.post("/invoices/create", data=data)

    with app.app_context():
        db = get_db()
        count = db.execute("SELECT COUNT(id) FROM invoices").fetchone()[0]
        assert count == 2


@pytest.mark.parametrize(
    "redirect_url, expected",
    [
        ("/calendar/2024/6", "/calendar/2024/6/?reservation_id=1"),
        ("/calendar/2024/5", "/calendar/2024/5/?reservation_id=1"),
        ("", "/invoices/"),
    ],
)
def test_create_with_redirect(client, auth, app, redirect_url, expected):
    data = {
        "reservation_id": 1,
    }

    auth.login()
    assert client.get(f"/invoices/create?redirect={redirect_url}").status_code == 302

    response = client.post(f"/invoices/create?redirect={redirect_url}", data=data)

    with app.app_context():
        db = get_db()
        count = db.execute("SELECT COUNT(id) FROM invoices").fetchone()[0]
        assert count == 2

    assert response.headers["Location"] == expected


@pytest.mark.skip(reason="endpoint not written yet")
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


@pytest.mark.skip(reason="endpoint not written yet")
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


@pytest.mark.skip(reason="endpoint not written yet")
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


@pytest.mark.skip(reason="endpoint not written yet")
def test_delete(client, auth, app):
    auth.login()
    response = client.post("/guests/1/delete")
    assert response.headers["Location"] == "/guests/"

    with app.app_context():
        db = get_db()
        post = db.execute("SELECT * FROM guests WHERE id = 1").fetchone()
        assert post is None
