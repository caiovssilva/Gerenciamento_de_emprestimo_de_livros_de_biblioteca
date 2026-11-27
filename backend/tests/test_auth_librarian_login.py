import os
import sys

import bcrypt
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import app
import api.auth as auth_module
import utils


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
            self._updated = False

        def select(self, *args, **kwargs):
            return self

        def eq(self, field, value):
            self._filters[field] = value
            return self

        def in_(self, field, values):
            self._filters[field] = values
            return self

        def limit(self, _count):
            return self

        def update(self, _values):
            self._updated = True
            return self

        def execute(self):
            if self._updated:
                return []
            rows = [row for users in self._rows.values() for row in users]
            return [
                row for row in rows
                if all(
                    row.get(field) in value if isinstance(value, (list, tuple, set)) else row.get(field) == value
                    for field, value in self._filters.items()
                )
            ]

    class FakeClient:
        def table(self, name):
            return FakeQuery(users_by_login if name == "usuarios" else {})

    return FakeClient()


def _patch_client(monkeypatch, users):
    fake_client = _make_fake_client(users)
    monkeypatch.setattr(auth_module, "get_client", lambda: fake_client)
    monkeypatch.setattr(utils, "get_client", lambda: fake_client)


def _user_row(login, nome, senha):
    return {"id": f"usr_{login}", "login": login, "nome": nome, "senha": senha}


def test_login_as_admin_returns_admin_access(client, monkeypatch):
    users = {
        "admin": [_user_row("admin", "Administrador", bcrypt.hashpw(b"narceu2026", bcrypt.gensalt()).decode())],
    }
    _patch_client(monkeypatch, users)

    response = client.post(
        "/api/auth/login",
        json={"login": "admin", "password": "narceu2026"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["access"] == "admin"
    assert payload["login"] == "admin"


def test_login_as_biblioteca_alias_returns_librarian_access(client, monkeypatch):
    users = {
        "biblioteca": [_user_row("biblioteca", "Bibliotecária", "narceu2026")],
    }
    _patch_client(monkeypatch, users)

    response = client.post(
        "/api/auth/login",
        json={"login": "bibliotecario", "password": "narceu2026"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["access"] == "librarian"
    assert payload["login"] == "biblioteca"


def test_login_with_plain_text_password(client, monkeypatch):
    users = {
        "admin": [_user_row("admin", "Administrador", "narceu2026")],
    }
    _patch_client(monkeypatch, users)

    response = client.post(
        "/api/auth/login",
        json={"login": "admin", "password": "narceu2026"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["access"] == "admin"
    assert payload["login"] == "admin"


def test_login_returns_database_unavailable_when_supabase_is_offline(client, monkeypatch):
    def unavailable_client():
        raise ConnectionError("Supabase indisponível")

    monkeypatch.setattr(utils, "get_client", unavailable_client)

    response = client.post(
        "/api/auth/login",
        json={"login": "admin", "password": "narceu2026"},
    )

    assert response.status_code == 503
    assert response.get_json()["code"] == "DATABASE_UNAVAILABLE"
