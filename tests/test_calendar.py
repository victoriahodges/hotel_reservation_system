from datetime import datetime

import pytest

# from reservation_system.db import get_db


def test_index(client, auth):
    response = client.get("/calendar/")
    assert b'href="/auth/login"' in response.data
    assert b"Booking Details" not in response.data
    assert b"Edit" not in response.data
    assert response.headers["Location"] == "/auth/login"

    auth.login()
    response = client.get("/calendar/")
    year = datetime.now().year
    month = datetime.now().month
    redirect_url = f'href="/calendar/{year}/{month}/"'
    assert redirect_url.encode("utf-8") in response.data
    assert b"Booking Details" not in response.data
    assert b"Edit" not in response.data
    assert response.headers["Location"] == f"/calendar/{year}/{month}/"


@pytest.mark.parametrize(
    "path",
    (
        "/calendar/2024/6/",
        "/calendar/2024/2/",
        "/calendar/2024/12/",
    ),
)
def test_login_required(client, path):
    response = client.get(path)
    assert response.headers["Location"] == "/auth/login"


def test_calendar(client, auth):
    response = client.get("/calendar/2024/5/")
    assert response.headers["Location"] == "/auth/login"
    auth.login()
    response = client.get("/calendar/2024/5/")
    assert response.status_code == 200
    assert b"Edit" in response.data
    assert b"May 2024" in response.data
    assert b'href="/calendar/2024/4/"' in response.data
    assert b'href="/calendar/2024/6/"' in response.data
    assert b"Alice Johnson" in response.data
    assert b"Chris Brown" in response.data
