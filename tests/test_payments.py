import pytest
from reservation_system.db import get_db


def test_index(client, auth):
    response = client.get("/payments/")
    assert b'href="/auth/login"' in response.data
    assert b"Amount" not in response.data
    assert b"Edit" not in response.data
    assert response.headers["Location"] == "/auth/login"

    auth.login()
    response = client.get("/payments/")
    assert b"Log out" in response.data
    assert b"Amount" in response.data
    assert b"90" in response.data
    assert b"00001" in response.data
    assert b'href="/payments/1/update' in response.data


@pytest.mark.parametrize(
    "path",
    (
        "/payments/create",
        "/payments/1/update",
    ),
)
def test_login_required(client, path):
    response = client.post(path)
    assert response.headers["Location"] == "/auth/login"


def test_record_exists(client, auth):
    # test data only has 2 records, expects record 3 not found
    auth.login()
    assert client.post("/payments/2/update", follow_redirects=False).status_code == 404


def test_create(client, auth, app):
    data = {
        "invoice_id": "1",
        "amount": "100",
    }

    auth.login()
    assert client.get("/payments/create?invoice_id=1").status_code == 200
    client.post("/payments/create", data=data)

    with app.app_context():
        db = get_db()
        count = db.execute("SELECT COUNT(id) FROM payments").fetchone()[0]
        assert count == 2


def test_update(client, auth, app):
    data = {
        "invoice_id": "1",
        "amount": "50",
    }

    auth.login()
    assert client.get("/payments/1/update").status_code == 200
    res = client.post("/payments/1/update", data=data)
    assert res.status_code == 302

    with app.app_context():
        db = get_db()
        res = db.execute("SELECT * FROM payments WHERE id = 1").fetchone()
        assert res["invoice_id"] == 1
        assert res["amount"] == 50


@pytest.mark.parametrize(
    "path",
    (
        "/payments/create?invoice_id=1",
        "/payments/1/update",
    ),
)
def test_create_update_validate(client, auth, path):
    data = {
        "invoice_id": "1",
        "amount": "",
    }
    auth.login()
    response = client.post(path, data=data, follow_redirects=True)
    assert b"Amount is required." in response.data
