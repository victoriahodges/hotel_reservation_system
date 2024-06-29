import pytest
from reservation_system.db import get_db


@pytest.mark.parametrize(
    "path",
    (
        "/invoice_items/create",
        "/invoice_items/1/update",
        "/invoice_items/1/delete",
    ),
)
def test_login_required(client, path):
    response = client.post(path)
    assert response.headers["Location"] == "/auth/login"


@pytest.mark.parametrize(
    "path",
    (
        "/invoice_items/6/update",
        "/invoice_items/6/delete",
    ),
)
def test_record_exists(client, auth, path):
    # test data only has 2 records, expects record 3 not found
    data = {"reservation_id": 3, "invoice_id": 3}

    auth.login()
    assert client.post(path, data=data).status_code == 404


def test_create(client, auth, app):
    data = {
        "invoice_id": 2,
        "item_description": "Drinks",
        "price": 23.00,
        "quantity": 2,
    }

    auth.login()
    assert client.get("/invoice_items/create?invoice_id=2").status_code == 200
    client.post("/invoice_items/create", data=data)

    with app.app_context():
        db = get_db()
        count = db.execute("SELECT COUNT(id) FROM invoice_items").fetchone()[0]
        assert count == 6


def test_update(client, auth, app):
    data = {
        "invoice_id": 2,
        "item_description": "Drinks",
        "price": 23.00,
        "quantity": 2,
    }

    auth.login()
    assert client.get("/invoice_items/2/update").status_code == 200
    res = client.post("/invoice_items/2/update", data=data)
    assert res.status_code == 302

    with app.app_context():
        db = get_db()
        res = db.execute("SELECT * FROM invoice_items WHERE id = 2").fetchone()
        assert res["item_description"] == "Drinks"
        assert res["total"] == 46.0


@pytest.mark.parametrize(
    "path",
    (
        "/invoice_items/create?invoice_id=2",
        "/invoice_items/2/update",
    ),
)
def test_create_update_validate(client, auth, path):
    data = {
        "invoice_id": 2,
        "item_description": "",
        "price": 23.00,
        "quantity": 2,
    }
    auth.login()
    response = client.post(path, data=data)
    assert b"Item Description is required." in response.data


def test_delete(client, auth, app):
    data = {"reservation_id": 2, "invoice_id": 2}

    auth.login()
    response = client.post("/invoice_items/2/delete", data=data)
    assert response.headers["Location"] == "/invoices/2/view?reservation_id=2"

    with app.app_context():
        db = get_db()
        post = db.execute("SELECT * FROM invoice_items WHERE id = 2").fetchone()
        assert post is None
