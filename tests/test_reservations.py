import datetime
import pytest
from reservation_system.db import get_db


def test_index(client, auth):
    response = client.get("/reservations/")
    assert b'href="/auth/login"' in response.data
    assert b"Reservations" not in response.data
    assert b"Edit" not in response.data
    assert response.headers["Location"] == "/auth/login"

    auth.login()
    response = client.get("/reservations/")
    assert b"Log Out" in response.data
    assert b"Alice Johnson" in response.data
    assert b"101" in response.data
    assert b"130.0" in response.data
    assert b'href="/reservations/1/update"' in response.data


@pytest.mark.parametrize(
    "path",
    (
        "/reservations/create",
        "/reservations/1/update",
        "/reservations/1/delete",
    ),
)
def test_login_required(client, path):
    response = client.post(path)
    assert response.headers["Location"] == "/auth/login"


@pytest.mark.parametrize(
    "path",
    (
        "/reservations/3/update",
        "/reservations/3/delete",
    ),
)
def test_record_exists(client, auth, path):
    # test data only has 2 records, expects record 3 not found
    auth.login()
    assert client.post(path).status_code == 404


def test_create(client, auth, app):
    data = {
        "number_of_guests": "2",
        "start_date": "2024-05-17",
        "end_date": "2024-05-20",
        "reservation_notes": "Early breakfast.",
        "status_id": "2",
        "room_id": "1",
        "guest_id": "2",
    }

    auth.login()
    assert client.get("/reservations/create").status_code == 200
    client.post("/reservations/create", data=data)

    with app.app_context():
        db = get_db()
        count = db.execute("SELECT COUNT(id) FROM reservations").fetchone()[0]
        assert count == 3


def test_update(client, auth, app):
    data = {
        "number_of_guests": "1",
        "start_date": "2024-05-18",
        "end_date": "2024-06-28",
        "reservation_notes": "Early breakfast.",
        "status_id": "2",
        "guest_id": "1",
        "room_id": "2",
    }

    auth.login()
    assert client.get("/reservations/1/update").status_code == 200
    res = client.post("/reservations/1/update", data=data)
    assert res.status_code == 302

    with app.app_context():
        db = get_db()
        res = db.execute("SELECT * FROM reservations WHERE id = 1").fetchone()
        assert res["start_date"] == datetime.date(2024, 5, 18)
        assert res["end_date"] == datetime.date(2024, 6, 28)
        assert res["reservation_notes"] == "Early breakfast."
        assert res["number_of_guests"] == 1

        res = db.execute("SELECT * FROM join_guests_reservations WHERE reservation_id = 1").fetchone()
        assert res["guest_id"] == 1

        res = db.execute("SELECT * FROM join_rooms_reservations WHERE reservation_id = 1").fetchone()
        assert res["room_id"] == 2


@pytest.mark.parametrize(
    "path",
    (
        "/reservations/create",
        "/reservations/1/update",
    ),
)
def test_create_update_validate(client, auth, path):
    data = {
        "number_of_guests": "",
        "start_date": "",
        "end_date": "",
        "reservation_notes": "",
        "status_id": "2",
        "guest_id": "",
        "room_id": "2",
    }
    auth.login()
    response = client.post(path, data=data)
    assert b"Number Of Guests is required." in response.data
    assert b"Start Date is required." in response.data
    assert b"End Date is required." in response.data
    assert b"Guest Id is required." in response.data


def test_delete(client, auth, app):
    auth.login()
    response = client.post("/reservations/1/delete")
    assert response.headers["Location"] == "/reservations/"

    with app.app_context():
        db = get_db()
        post = db.execute("SELECT * FROM reservations WHERE id = 1").fetchone()
        assert post is None
        post = db.execute("SELECT * FROM join_guests_reservations WHERE reservation_id = 1").fetchone()
        assert post is None
        post = db.execute("SELECT * FROM join_rooms_reservations WHERE reservation_id = 1").fetchone()
        assert post is None
