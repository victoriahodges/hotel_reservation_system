from io import BytesIO

import pytest
from reservation_system.db import get_db


def test_index(client, auth):
    response = client.get("/room_types/")
    assert b'href="/auth/login"' in response.data
    assert b"King-size bed, bath, sea views" not in response.data
    assert b"Edit" not in response.data
    assert response.headers["Location"] == "/auth/login"

    auth.login()
    response = client.get("/room_types/")
    assert b"Log out" in response.data
    assert b"Superior Double" in response.data
    assert b"King-size bed, bath, sea views" in response.data
    assert b'href="/room_types/1/update"' in response.data


@pytest.mark.parametrize(
    "path",
    (
        "/room_types/create",
        "/room_types/1/update",
        "/room_types/1/delete",
    ),
)
def test_login_required(client, path):
    response = client.post(path)
    assert response.headers["Location"] == "/auth/login"


@pytest.mark.parametrize(
    "path",
    (
        "/room_types/3/update",
        "/room_types/3/delete",
    ),
)
def test_record_exists(client, auth, path):
    # test data only has 2 records, expects record 3 not found
    auth.login()
    assert client.post(path).status_code == 404


def test_create(client, auth, app):
    data = {
        "type_name": "Single",
        "base_price_per_night": "95",
        "amenities": "Single bed, sea views, shower",
        "max_occupants": "1",
    }
    data["photo"] = (BytesIO(b"abcdef"), "test.jpg")

    auth.login()
    assert client.get("/room_types/create").status_code == 200
    client.post("/room_types/create", data=data, content_type="multipart/form-data")

    with app.app_context():
        db = get_db()
        count = db.execute("SELECT COUNT(id) FROM room_types").fetchone()[0]
        assert count == 3


def test_update(client, auth, app):
    data = {
        "type_name": "Single",
        "base_price_per_night": "95",
        "amenities": "Single bed, sea views, shower",
        "max_occupants": "1",
    }
    data["photo"] = (BytesIO(b"abcdef"), "test.jpg")

    auth.login()
    assert client.get("/room_types/1/update").status_code == 200
    res = client.post("/room_types/1/update", data=data, content_type="multipart/form-data")
    assert res.status_code == 302

    with app.app_context():
        db = get_db()
        res = db.execute("SELECT * FROM room_types WHERE id = 1").fetchone()
        assert res["type_name"] == "Single"
        assert res["max_occupants"] == 1


@pytest.mark.parametrize(
    "path",
    (
        "/room_types/create",
        "/room_types/1/update",
    ),
)
def test_create_update_validate(client, auth, path):
    data = {
        "type_name": "",
        "base_price_per_night": "",
        "amenities": "Single bed, sea views, shower",
        "max_occupants": "",
    }
    data["photo"] = (BytesIO(b"abcdef"), "test.jpg")

    auth.login()
    response = client.post(path, data=data, content_type="multipart/form-data")
    assert b"Type Name is required." in response.data
    assert b"Base Price Per Night is required." in response.data
    assert b"Max Occupants is required." in response.data


@pytest.mark.parametrize(
    "path, extension",
    [
        ("/room_types/create", "pdf"),
        ("/room_types/1/update", "txt"),
    ],
)
def test_create_update_allowed_extensions_validate(client, auth, path, extension):
    data = {
        "type_name": "Single",
        "base_price_per_night": "95",
        "amenities": "Single bed, sea views, shower",
        "max_occupants": "1",
    }
    data["photo"] = (BytesIO(b"abcdef"), f"test.{extension}")

    auth.login()
    response = client.post(path, data=data, content_type="multipart/form-data")
    assert b"Not a valid file type." in response.data


@pytest.mark.parametrize(
    "path, key, filename, photo_bytes, expected",
    [
        ("/room_types/create", "", "test.jpg", b"abcdef", b"No photo part found"),
        ("/room_types/create", "photo", "", b"abcdef", b"No selected photo"),
        ("/room_types/create", "photo", "test.jpg", b"", b"Invalid file"),
        ("/room_types/1/update", "", "test.jpg", b"abcdef", b"No photo part found"),
        ("/room_types/1/update", "photo", "", b"abcdef", b"No selected photo"),
        ("/room_types/1/update", "photo", "test.jpg", b"", b"Invalid file"),
    ],
)
def test_create_update_photo_upload_validate(client, auth, path, key, filename, photo_bytes, expected):
    data = {
        "type_name": "Single",
        "base_price_per_night": "95",
        "amenities": "Single bed, sea views, shower",
        "max_occupants": "1",
    }
    data[key] = (BytesIO(photo_bytes), filename)

    auth.login()
    response = client.post(path, data=data, content_type="multipart/form-data")
    assert expected in response.data


def test_delete(client, auth, app):
    auth.login()
    response = client.post("/room_types/1/delete")
    assert response.headers["Location"] == "/room_types/"

    with app.app_context():
        db = get_db()
        post = db.execute("SELECT * FROM room_types WHERE id = 1").fetchone()
        assert post is None
