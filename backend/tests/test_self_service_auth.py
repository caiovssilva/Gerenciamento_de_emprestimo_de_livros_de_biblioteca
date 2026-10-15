import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import api.auth as auth_module
import utils
from app import app


class FakeQuery:
    def __init__(self, rows):
        self.rows = rows
        self.filters = {}

    def select(self, *_columns):
        return self

    def eq(self, field, value):
        self.filters[field] = value
        return self

    def in_(self, field, values):
        self.filters[field] = values
        return self

    def limit(self, _count):
        return self

    def execute(self):
        return [
            row for row in self.rows
            if all(
                row.get(key) in value if isinstance(value, (list, tuple, set)) else row.get(key) == value
                for key, value in self.filters.items()
            )
        ]


class FakeClient:
    def __init__(self, data):
        self.data = data

    def table(self, name):
        return FakeQuery(self.data.get(name, []))


def test_self_service_history_is_bound_to_authenticated_student(monkeypatch):
    data = {
        "livros": [{"id": "book-1", "titulo": "Livro do aluno"}],
        "alunos": [
            {"id": "student-1", "nome": "Ana", "carteirinha": "CARD-1", "turma": "A"},
            {"id": "student-2", "nome": "Bia", "carteirinha": "CARD-2", "turma": "B"},
        ],
        "emprestimos": [
            {"aluno_id": "student-1", "livro_id": "book-1", "data_emprestimo": "2026-01-01"},
            {"aluno_id": "student-2", "livro_id": "book-1", "data_emprestimo": "2026-01-02"},
        ],
    }
    client = FakeClient(data)
    monkeypatch.setattr(auth_module, "get_client", lambda: client)
    monkeypatch.setattr(utils, "get_client", lambda: client)
    monkeypatch.setitem(app.config, "SECRET_KEY", "test-secret-that-is-not-default")

    with app.test_client() as test_client:
        login = test_client.post("/api/auth/self-service/login", json={"code": "CARD-1"})
        assert login.status_code == 200
        token = login.get_json()["token"]

        history = test_client.get(
            "/api/auth/self-service/history?student_id=student-2",
            headers={"Authorization": f"Bearer {token}"},
        )
        forbidden = test_client.get("/api/reports/data")

    assert history.status_code == 200
    payload = history.get_json()
    assert payload["student"]["name"] == "Ana"
    assert payload["student"]["card"] == "CARD-1"
    assert len(payload["history"]) == 1
    assert payload["history"][0]["loan_date"] == "2026-01-01"
    assert forbidden.status_code == 403


def test_self_service_history_requires_valid_token(monkeypatch):
    client = FakeClient({"livros": []})
    monkeypatch.setattr(utils, "get_client", lambda: client)
    monkeypatch.setitem(app.config, "SECRET_KEY", "test-secret-that-is-not-default")

    with app.test_client() as test_client:
        response = test_client.get("/api/auth/self-service/history")

    assert response.status_code == 401


def test_traditional_staff_login_still_requires_valid_password(monkeypatch):
    client = FakeClient({
        "livros": [],
        "usuarios": [{"id": "admin-1", "login": "admin", "nome": "Admin", "senha": "secret"}],
    })
    monkeypatch.setattr(auth_module, "get_client", lambda: client)
    monkeypatch.setattr(utils, "get_client", lambda: client)

    with app.test_client() as test_client:
        accepted = test_client.post("/api/auth/login", json={"login": "admin", "password": "secret"})
        rejected = test_client.post("/api/auth/login", json={"login": "admin", "password": "wrong"})

    assert accepted.status_code == 200
    assert accepted.get_json()["access"] == "admin"
    assert rejected.status_code == 401


def test_librarian_card_cannot_enter_as_common_student(monkeypatch):
    client = FakeClient({
        "livros": [],
        "alunos": [{"id": "staff-1", "nome": "Bibliotecário", "carteirinha": "STAFF-1", "is_librarian": True}],
    })
    monkeypatch.setattr(auth_module, "get_client", lambda: client)
    monkeypatch.setattr(utils, "get_client", lambda: client)
    monkeypatch.setitem(app.config, "SECRET_KEY", "test-secret-that-is-not-default")

    with app.test_client() as test_client:
        response = test_client.post("/api/auth/self-service/login", json={"code": "STAFF-1"})

    assert response.status_code == 401


def test_self_service_allows_only_own_history_and_logout(monkeypatch):
    client = FakeClient({
        "livros": [],
        "alunos": [
            {"id": "student-1", "nome": "Ana", "carteirinha": "CARD-1"},
            {"id": "student-2", "nome": "Bia", "carteirinha": "CARD-2"},
        ],
        "emprestimos": [
            {"id": "loan-own", "aluno_id": "student-1"},
            {"id": "loan-other", "aluno_id": "student-2"},
        ],
    })
    monkeypatch.setattr(auth_module, "get_client", lambda: client)
    monkeypatch.setattr(utils, "get_client", lambda: client)
    monkeypatch.setitem(app.config, "SECRET_KEY", "test-secret-that-is-not-default")

    with app.test_client() as test_client:
        login = test_client.post("/api/auth/self-service/login", json={"code": "CARD-1"})
        token = login.get_json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        history = test_client.get("/api/auth/self-service/history", headers=headers)
        catalog = test_client.get("/api/books/?q=&genre=", headers=headers)
        create_loan = test_client.post(
            "/api/loans/", json={"aluno_id": "student-1", "livro_id": "book-1"}, headers=headers,
        )
        renew_loan = test_client.post("/api/loans/loan-own/renew", json={}, headers=headers)
        logout = test_client.post("/api/auth/self-service/logout")

    assert history.status_code == 200
    assert catalog.status_code == 403
    assert create_loan.status_code == 403
    assert renew_loan.status_code == 403
    assert logout.status_code == 200