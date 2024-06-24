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
    assert b'href="/invoices/1/view?reservation_id=2"' in response.data


@pytest.mark.parametrize(
    "path, method",
    [
        ("/invoices/create", "post"),
        ("/invoices/1/view", "get"),
    ],
)
def test_login_required(client, path, method):
    if method == "get":
        response = client.get(path)
        assert response.headers["Location"] == "/auth/login"
    if method == "post":
        response = client.post(path)
        assert response.headers["Location"] == "/auth/login"


def test_view(client, auth):
    auth.login()
    response = client.get("/invoices/1/view?reservation_id=2")
    assert response.status_code == 200

    assert b"Alice Johnson" in response.data
    assert b"785.00" in response.data


def test_view_invoice_does_not_exist(client, auth):
    auth.login()
    response = client.get("/invoices/2/view", follow_redirects=True)

    assert b"Invoice #00002 does not exist." in response.data


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


def test_create_invoice_exists(client, auth):
    data = {
        "reservation_id": 2,
    }
    auth.login()
    # no page is returned when generating an invoice
    assert client.get("/invoices/create").status_code == 302
    response = client.post("/invoices/create", data=data, follow_redirects=True)

    assert b"Invoice #00001 already exists on another booking." in response.data


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


def test_delete(client, auth, app):
    auth.login()
    response = client.post("/invoices/1/delete")
    assert response.headers["Location"] == "/invoices/"

    with app.app_context():
        db = get_db()
        post = db.execute("SELECT * FROM invoices WHERE id = 1").fetchone()
        assert post is None
