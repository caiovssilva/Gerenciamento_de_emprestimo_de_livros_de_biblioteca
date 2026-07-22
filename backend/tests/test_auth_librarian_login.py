import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import app


@pytest.fixture()
def client():
    app.config.update(TESTING=True)
    with app.test_client() as client:
        yield client


def test_login_as_admin_returns_admin_access(client):
    response = client.post(
        "/api/auth/login",
        json={"login": "admin", "password": "narceu2026"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["access"] == "admin"
    assert payload["login"] == "admin"


def test_login_as_biblioteca_returns_librarian_access(client):
    response = client.post(
        "/api/auth/login",
        json={"login": "biblioteca", "password": "narceu2026"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["access"] == "librarian"
    assert payload["login"] == "biblioteca"
