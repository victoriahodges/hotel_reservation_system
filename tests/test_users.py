import pytest
from flask import g, session
from reservation_system.db import get_db
from werkzeug.security import check_password_hash


def test_index(client, auth):
    response = client.get("/users/")
    assert b'href="/auth/login"' in response.data
    assert b"Username" not in response.data
    assert b"Edit" not in response.data
    assert response.headers["Location"] == "/auth/login"

    auth.login()
    response = client.get("/users/")
    assert b"Log out" in response.data
    assert b"Username" in response.data
    assert b"test" in response.data
    assert b'href="/users/1/update"' in response.data


@pytest.mark.parametrize(
    "path",
    (
        "/users/create",
        "/users/1/update",
        "/users/1/delete",
    ),
)
def test_login_required(client, path):
    response = client.post(path)
    assert response.headers["Location"] == "/auth/login"


@pytest.mark.parametrize(
    "path",
    (
        "/users/3/update",
        "/users/3/delete",
    ),
)
def test_record_exists(client, auth, path):
    # test data only has 2 records, expects record 3 not found
    auth.login()
    assert client.post(path).status_code == 404


def test_create(client, auth, app):
    data = {
        "username": "test_username",
        "password": "password",
    }

    auth.login()
    assert client.get("/users/create").status_code == 200
    client.post("/users/create", data=data)

    with app.app_context():
        db = get_db()
        count = db.execute("SELECT COUNT(id) FROM users").fetchone()[0]
        assert count == 3


def test_update(client, auth, app):
    data = {
        "username": "test_username",
        "password": "password123",
    }

    auth.login()
    assert client.get("/users/1/update").status_code == 200
    res = client.post("/users/1/update", data=data)
    assert res.status_code == 302

    with app.app_context():
        db = get_db()
        res = db.execute("SELECT * FROM users WHERE id = 1").fetchone()
        assert res["username"] == "test_username"
        assert check_password_hash(res["password"], data["password"])


@pytest.mark.parametrize(
    "path",
    (
        "/users/create",
        "/users/1/update",
    ),
)
def test_create_update_validate(client, auth, path):
    data = {
        "username": "",
        "password": "",
    }

    auth.login()
    response = client.post(path, data=data)
    assert b"Username is required." in response.data
    assert b"Password is required." in response.data


@pytest.mark.parametrize(
    "path",
    (
        "/users/create",
        "/users/2/update",
    ),
)
def test_create_already_registered_validate(client, auth, path):
    data = {
        "username": "test",
        "password": "password",
    }

    auth.login()
    response = client.post(path, data=data)
    assert b"already registered." in response.data


def test_delete_other_user(client, auth, app):
    auth.login()
    response = client.post("/users/2/delete")
    assert response.headers["Location"] == "/users/"

    with app.app_context():
        db = get_db()
        post = db.execute("SELECT * FROM users WHERE id = 2").fetchone()
        assert post is None


def test_delete_logged_in(client, auth, app):
    # Cannot delete users if they are already logged in
    auth.login()
    with client:
        client.get("/")
        assert session["user_id"] == 1
        assert g.user["username"] == "test"

    response = client.post("/users/1/delete", follow_redirects=True)
    assert b"User currently logged in." in response.data

    with app.app_context():
        db = get_db()
        post = db.execute("SELECT * FROM users WHERE id = 1").fetchone()
        assert post["username"] == "test"
