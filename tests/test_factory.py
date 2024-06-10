from reservation_system import create_app


def test_config():
    assert not create_app().testing
    assert create_app({"TESTING": True}).testing


def test_index(client, auth):
    response = client.get("/")
    assert b"Homepage" not in response.data

    auth.login()
    response = client.get("/")
    assert b"Homepage" in response.data
