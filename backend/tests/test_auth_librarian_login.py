import crypt as unix_crypt
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import app
import api.auth as auth_module


@pytest.fixture()
def client():
    app.config.update(TESTING=True)
    with app.test_client() as client:
        yield client


def _make_fake_client(users_by_login):
    class FakeQuery:
        def __init__(self, rows):
            self._rows = rows
            self._filters = {}

        def select(self, *args, **kwargs):
            return self

        def eq(self, field, value):
            self._filters[field] = value
            return self

        def execute(self):
            login = self._filters.get("login")
            return self._rows.get(login, [])

    class FakeClient:
        def table(self, name):
            assert name == "usuarios"
            return FakeQuery(users_by_login)

    return FakeClient()


def _user_row(login, nome, senha):
    return {"id": f"usr_{login}", "login": login, "nome": nome, "senha": senha}


def test_login_as_admin_returns_admin_access(client, monkeypatch):
    users = {
        "admin": [_user_row("admin", "Administrador", unix_crypt.crypt("narceu2026", unix_crypt.mksalt()))],
    }
    monkeypatch.setattr(auth_module, "get_client", lambda: _make_fake_client(users))

    response = client.post(
        "/api/auth/login",
        json={"login": "admin", "password": "narceu2026"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["access"] == "admin"
    assert payload["login"] == "admin"


def test_login_as_bibliotecario_returns_librarian_access(client, monkeypatch):
    users = {
        "bibliotecario": [_user_row("bibliotecario", "Bibliotecário", unix_crypt.crypt("biblioteca123", unix_crypt.mksalt()))],
    }
    monkeypatch.setattr(auth_module, "get_client", lambda: _make_fake_client(users))

    response = client.post(
        "/api/auth/login",
        json={"login": "bibliotecario", "password": "biblioteca123"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["access"] == "librarian"
    assert payload["login"] == "bibliotecario"
