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
    assert b"Log out" in response.data
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
        "start_date": (datetime.datetime.now() + datetime.timedelta(days=10)).date(),
        "end_date": (datetime.datetime.now() + datetime.timedelta(days=15)).date(),
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


@pytest.mark.parametrize(
    "redirect_url, expected",
    [
        ("/reservations/create", f"/calendar/{datetime.datetime.now().year}/{datetime.datetime.now().month}/"),
        ("/calendar/2024/6/", f"/calendar/{datetime.datetime.now().year}/{datetime.datetime.now().month}/"),
        ("/calendar/invalid/input", f"/calendar/{datetime.datetime.now().year}/{datetime.datetime.now().month}/"),
    ],
)
def test_create_with_redirect(client, auth, app, redirect_url, expected):
    # assert that creating a reservation redirects to calendar view
    data = {
        "number_of_guests": "2",
        "start_date": (datetime.datetime.now() + datetime.timedelta(days=10)).date(),
        "end_date": (datetime.datetime.now() + datetime.timedelta(days=15)).date(),
        "reservation_notes": "Early breakfast.",
        "status_id": "2",
        "room_id": "1",
        "guest_id": "2",
    }

    auth.login()
    assert client.get(f"/reservations/create?redirect={redirect_url}").status_code == 200
    response = client.post(f"/reservations/create?redirect={redirect_url}", data=data)

    with app.app_context():
        db = get_db()
        count = db.execute("SELECT COUNT(id) FROM reservations").fetchone()[0]
        assert count == 3

    assert response.headers["Location"] == expected + "?reservation_id=3"


def test_update(client, auth, app):
    data = {
        "number_of_guests": "1",
        "start_date": (datetime.datetime.now() + datetime.timedelta(days=10)).date(),
        "end_date": (datetime.datetime.now() + datetime.timedelta(days=15)).date(),
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
        assert res["start_date"] == (datetime.datetime.now() + datetime.timedelta(days=10)).date()
        assert res["end_date"] == (datetime.datetime.now() + datetime.timedelta(days=15)).date()
        assert res["reservation_notes"] == "Early breakfast."
        assert res["number_of_guests"] == 1

        res = db.execute("SELECT * FROM join_guests_reservations WHERE reservation_id = 1").fetchone()
        assert res["guest_id"] == 1

        res = db.execute("SELECT * FROM join_rooms_reservations WHERE reservation_id = 1").fetchone()
        assert res["room_id"] == 2


@pytest.mark.parametrize(
    "redirect_url, expected",
    [
        ("/reservations/create", f"/calendar/{datetime.datetime.now().year}/{datetime.datetime.now().month}/"),
        ("/calendar/2024/6/", f"/calendar/{datetime.datetime.now().year}/{datetime.datetime.now().month}/"),
        ("/calendar/invalid/input", f"/calendar/{datetime.datetime.now().year}/{datetime.datetime.now().month}/"),
    ],
)
def test_update_with_redirect(client, auth, app, redirect_url, expected):
    # assert that updating a reservation redirects to calendar view
    data = {
        "number_of_guests": "2",
        "start_date": (datetime.datetime.now() + datetime.timedelta(days=10)).date(),
        "end_date": (datetime.datetime.now() + datetime.timedelta(days=15)).date(),
        "reservation_notes": "Early breakfast.",
        "status_id": "2",
        "room_id": "1",
        "guest_id": "2",
    }

    auth.login()
    assert client.get("/reservations/1/update").status_code == 200
    response = client.post("/reservations/1/update", data=data)
    assert response.status_code == 302

    assert response.headers["Location"] == expected + "?reservation_id=1"


@pytest.mark.parametrize(
    "path",
    (
        "/reservations/create",
        "/reservations/1/update",
    ),
)
def test_create_update_validate_form_fields(client, auth, path):
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


@pytest.mark.parametrize(
    "start_date, end_date, room_id",
    [
        ("2024-05-15", "2024-05-24", "1"),  # outside
        ("2024-05-18", "2024-05-20", "1"),  # inside
        ("2024-05-15", "2024-05-19", "1"),  # start_date overlap
        ("2024-05-19", "2024-05-24", "1"),  # end_date overlap
        ("2024-05-18", "2024-05-27", "2"),  # outside
        ("2024-05-21", "2024-05-23", "2"),  # inside
        ("2024-05-18", "2024-05-23", "2"),  # start_date overl
        ("2024-05-23", "2024-05-27", "2"),  # end_date overlap
    ],
)
def test_create_validate_collisions(client, auth, start_date, end_date, room_id):
    data = {
        "number_of_guests": "2",
        "start_date": start_date,
        "end_date": end_date,
        "reservation_notes": "",
        "status_id": "2",
        "guest_id": "2",
        "room_id": room_id,
    }
    auth.login()
    response = client.post("/reservations/create", data=data)
    assert b"BOOKING COLLISION" in response.data


@pytest.mark.parametrize(
    "start_date, end_date",
    [
        (8, 16),  # outside
        (10, 14),  # inside
        (8, 11),  # start_date overlap
        (13, 16),  # end_date overlap
    ],
)
def test_update_validate_collisions(client, auth, start_date, end_date):
    create_data = {
        "number_of_guests": "2",
        "start_date": (datetime.datetime.now() + datetime.timedelta(days=10)).date(),
        "end_date": (datetime.datetime.now() + datetime.timedelta(days=15)).date(),
        "reservation_notes": "",
        "status_id": "2",
        "guest_id": "2",
        "room_id": "1",
    }
    update_data = {
        "number_of_guests": "2",
        "start_date": (datetime.datetime.now() + datetime.timedelta(days=start_date)).date(),
        "end_date": (datetime.datetime.now() + datetime.timedelta(days=end_date)).date(),
        "reservation_notes": "Moved booking",
        "status_id": "2",
        "guest_id": "2",
        "room_id": "1",
    }
    auth.login()
    response = client.post("/reservations/create", data=create_data)
    response = client.post("/reservations/1/update", data=update_data)
    assert b"BOOKING COLLISION" in response.data


@pytest.mark.parametrize(
    "path, start_date, end_date",
    [
        ("/reservations/create", 15, 10),
        ("/reservations/create", 10, 10),
        ("/reservations/1/update", 15, 10),
        ("/reservations/1/update", 10, 10),
    ],
)
def test_create_validate_end_date_before_start_date(client, auth, path, start_date, end_date):
    data = {
        "number_of_guests": "2",
        "start_date": (datetime.datetime.now() + datetime.timedelta(days=start_date)).date(),
        "end_date": (datetime.datetime.now() + datetime.timedelta(days=end_date)).date(),
        "reservation_notes": "",
        "status_id": "2",
        "guest_id": "1",
        "room_id": "1",
    }
    auth.login()
    response = client.post(path, data=data)
    assert b"DATE ERROR: Check-out date cannot be before or same as check-in date." in response.data


@pytest.mark.parametrize(
    "path, start_date, end_date",
    [
        ("/reservations/create", "2023-05-17", "2023-05-20"),
        ("/reservations/create", "2024-05-01", "2024-05-05"),
    ],
)
def test_create_validate_booking_in_the_past(client, auth, path, start_date, end_date):
    data = {
        "number_of_guests": "2",
        "start_date": start_date,
        "end_date": end_date,
        "reservation_notes": "",
        "status_id": "2",
        "guest_id": "1",
        "room_id": "1",
    }
    auth.login()
    response = client.post(path, data=data)
    assert b"DATE ERROR: Check-in or check-out dates cannot be in the past." in response.data


def test_delete(client, auth, app):
    data = {"redirect": ""}
    auth.login()
    response = client.post("/reservations/1/delete", data=data)
    assert response.headers["Location"] == "/reservations/"

    with app.app_context():
        db = get_db()
        post = db.execute("SELECT * FROM reservations WHERE id = 1").fetchone()
        assert post is None
        post = db.execute("SELECT * FROM join_guests_reservations WHERE reservation_id = 1").fetchone()
        assert post is None
        post = db.execute("SELECT * FROM join_rooms_reservations WHERE reservation_id = 1").fetchone()
        assert post is None


@pytest.mark.parametrize(
    "redirect, expected",
    [
        ("/calendar/2024/5", "/calendar/2024/5/"),
        ("/reservations/create", "/reservations/create"),
    ],
)
def test_delete_redirect(client, auth, app, redirect, expected):
    data = {"redirect": redirect}
    auth.login()
    response = client.post(f"/reservations/1/delete?redirect={redirect}", data=data)
    assert response.headers["Location"] == expected

    with app.app_context():
        db = get_db()
        post = db.execute("SELECT * FROM reservations WHERE id = 1").fetchone()
        assert post is None
        post = db.execute("SELECT * FROM join_guests_reservations WHERE reservation_id = 1").fetchone()
        assert post is None
        post = db.execute("SELECT * FROM join_rooms_reservations WHERE reservation_id = 1").fetchone()
        assert post is None
