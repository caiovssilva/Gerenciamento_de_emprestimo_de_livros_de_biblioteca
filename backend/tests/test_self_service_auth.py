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

    def order(self, *_args, **_kwargs):
        return self

    def is_(self, field, value):
        self.filters[field] = None if value == "null" else value
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
        health = test_client.get("/api/health")
        readiness = test_client.get("/api/ready")
        forbidden = test_client.get("/api/reports/data")

    assert history.status_code == 200
    assert health.status_code == 200
    assert health.get_json()["status"] == "ok"
    assert readiness.status_code == 200
    assert readiness.get_json()["database"] == "conectado"
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


def test_librarian_card_can_enter_restricted_self_service(monkeypatch):
    client = FakeClient({
        "livros": [],
        "alunos": [{"id": "staff-1", "nome": "Bibliotecário", "carteirinha": "STAFF-1", "is_librarian": True}],
    })
    monkeypatch.setattr(auth_module, "get_client", lambda: client)
    monkeypatch.setattr(utils, "get_client", lambda: client)
    monkeypatch.setitem(app.config, "SECRET_KEY", "test-secret-that-is-not-default")

    with app.test_client() as test_client:
        response = test_client.post("/api/auth/self-service/login", json={"code": "STAFF-1"})

    assert response.status_code == 200
    assert response.get_json()["access"] == "self_service"


def test_self_service_card_lookup_normalizes_input_and_false_librarian_flag(monkeypatch):
    client = FakeClient({
        "livros": [],
        "alunos": [{
            "id": "student-1",
            "nome": "Ana",
            "carteirinha": "CARD-1",
            "is_librarian": "false",
        }],
    })
    monkeypatch.setattr(auth_module, "get_client", lambda: client)
    monkeypatch.setitem(app.config, "SECRET_KEY", "test-secret-that-is-not-default")

    with app.test_client() as test_client:
        response = test_client.post("/api/auth/self-service/login", json={"code": " card-1 "})

    assert response.status_code == 200
    assert response.get_json()["name"] == "Ana"


def test_self_service_card_lookup_tolerates_card_formatting(monkeypatch):
    client = FakeClient({
        "livros": [],
        "alunos": [{
            "id": "student-1",
            "nome": "Ana",
            "carteirinha": "185548.1.32021194",
        }],
    })
    monkeypatch.setattr(auth_module, "get_client", lambda: client)
    monkeypatch.setitem(app.config, "SECRET_KEY", "test-secret-that-is-not-default")

    with app.test_client() as test_client:
        response = test_client.post(
            "/api/auth/self-service/login",
            json={"code": "185548 1 32021194"},
        )

    assert response.status_code == 200
    assert response.get_json()["name"] == "Ana"


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


def test_self_service_can_login_decode_qr_and_load_runtime_config(monkeypatch):
    import api.controle as controle_module

    settings = {
        **controle_module.DEFAULT_SETTINGS,
        "enabled": True,
        "allow_return": True,
    }
    client = FakeClient({
        "livros": [],
        "alunos": [{"id": "student-1", "nome": "Ana", "carteirinha": "CARD-1"}],
        "usuarios": [],
    })
    monkeypatch.setattr(auth_module, "get_client", lambda: client)
    monkeypatch.setattr(utils, "get_client", lambda: client)
    monkeypatch.setattr(controle_module, "get_self_service_settings", lambda: settings)
    monkeypatch.setitem(app.config, "SECRET_KEY", "test-secret-that-is-not-default")

    with app.test_client() as test_client:
        login = test_client.post("/api/auth/self-service/login", json={"code": "CARD-1"})
        headers = {"Authorization": f"Bearer {login.get_json()['token']}"}
        staff_login = test_client.post(
            "/api/auth/login",
            json={"login": "unknown-user", "password": "invalid"},
            headers=headers,
        )
        qr_decode = test_client.post(
            "/api/qr/decode", json={"image": "invalid-image-data"}, headers=headers,
        )
        settings_response = test_client.get("/api/controle/autoatendimento", headers=headers)
        config_responses = [
            test_client.get(path, headers=headers)
            for path in (
                "/api/auth/config/supabase",
                "/api/config/supabase",
                "/api/auth/supabase-config",
                "/api/supabase-config",
            )
        ]

    assert login.status_code == 200
    assert staff_login.status_code == 401
    assert qr_decode.status_code == 400
    assert settings_response.status_code == 200
    assert [response.status_code for response in config_responses] == [200, 200, 200, 200]


def test_self_service_can_browse_books_and_create_only_own_loan(monkeypatch):
    import api.loans as loans_module

    client = FakeClient({
        "livros": [{
            "id": "book-1",
            "titulo": "Livro disponível",
            "exemplares": 1,
            "exemplares_meta": [{
                "id": "copy-1",
                "code": "001",
                "qr_data": "EXEMPLAR-book-1-EX-001-copy-1",
            }],
        }],
        "alunos": [
            {"id": "student-1", "nome": "Ana", "carteirinha": "CARD-1"},
            {"id": "student-2", "nome": "Bia", "carteirinha": "CARD-2"},
        ],
        "emprestimos": [],
    })
    monkeypatch.setattr(auth_module, "get_client", lambda: client)
    monkeypatch.setattr(utils, "get_client", lambda: client)
    monkeypatch.setattr(loans_module, "get_client", lambda: client)
    monkeypatch.setattr(loans_module, "_available_copies_from_rows", lambda *_args: [{"code": "001", "id": "copy-1"}])
    monkeypatch.setitem(app.config, "SECRET_KEY", "test-secret-that-is-not-default")

    captured = {}

    def create_record(body, forced_student_id=None, created_by_override=None):
        captured.update(body=body, student_id=forced_student_id, created_by=created_by_override)
        from flask import jsonify
        return jsonify({"aluno_id": forced_student_id, "livro_id": body["livro_id"]}), 201

    monkeypatch.setattr(loans_module, "_create_loan_record", create_record)

    with app.test_client() as test_client:
        login = test_client.post("/api/auth/self-service/login", json={"code": "CARD-1"})
        headers = {"Authorization": f"Bearer {login.get_json()['token']}"}
        books = test_client.get("/api/auth/self-service/books", headers=headers)
        loan = test_client.post(
            "/api/auth/self-service/loans",
            json={"exemplar_qr": "EXEMPLAR-book-1-EX-001-copy-1", "aluno_id": "student-2"},
            headers=headers,
        )
        generic_book_qr = test_client.post(
            "/api/auth/self-service/loans",
            json={"exemplar_qr": "book-1"},
            headers=headers,
        )
        blocked_catalog = test_client.get("/api/books/", headers=headers)
        blocked_renewal = test_client.post("/api/loans/loan-own/renew", json={}, headers=headers)

    assert books.status_code == 200
    assert books.get_json() == [{"id": "book-1", "titulo": "Livro disponível", "autor": "", "isbn": "", "available_copies": 1}]
    assert loan.status_code == 201
    assert loan.get_json()["aluno_id"] == "student-1"
    assert generic_book_qr.status_code == 400
    assert captured["student_id"] == "student-1"
    assert captured["created_by"] == "autoatendimento"
    assert captured["body"] == {
        "livro_id": "book-1",
        "exemplar": "001",
        "dias": 7,
        "observacao": "",
    }
    assert blocked_catalog.status_code == 403
    assert blocked_renewal.status_code == 403


def test_self_service_cannot_renew_another_students_loan(monkeypatch):
    client = FakeClient({
        "livros": [],
        "alunos": [{"id": "student-1", "nome": "Ana", "carteirinha": "CARD-1"}],
        "emprestimos": [{"id": "loan-other", "aluno_id": "student-2"}],
    })
    monkeypatch.setattr(auth_module, "get_client", lambda: client)
    monkeypatch.setattr(utils, "get_client", lambda: client)
    monkeypatch.setitem(app.config, "SECRET_KEY", "test-secret-that-is-not-default")

    with app.test_client() as test_client:
        login = test_client.post("/api/auth/self-service/login", json={"code": "CARD-1"})
        token = login.get_json()["token"]
        response = test_client.post(
            "/api/auth/self-service/loans/loan-other/renew",
            json={"dias": 1},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 403
    assert "não pertence" in response.get_json()["error"]


def test_renewal_ignores_client_days_and_uses_admin_setting(monkeypatch):
    import api.controle as controle_module
    import api.loans as loans_module

    loan = {
        "id": "loan-1",
        "data_devolucao_prevista": "2026-10-15",
        "renovacoes": 0,
        "devolvido_em": None,
    }

    class Query:
        action = "select"

        def select(self, *_columns):
            self.action = "select"
            return self

        def update(self, values):
            self.action = "update"
            self.values = values
            return self

        def eq(self, *_args):
            return self

    class Client:
        def table(self, _name):
            return Query()

    def execute(query):
        if query.action == "update":
            loan.update(query.values)
        return [loan]

    monkeypatch.setattr(controle_module, "get_self_service_settings", lambda: {
        **controle_module.DEFAULT_SETTINGS,
        "renewal_days": 21,
    })
    monkeypatch.setattr(loans_module, "get_client", lambda: Client())
    monkeypatch.setattr(loans_module, "sb_exec", execute)

    with app.test_request_context(
        "/api/loans/loan-1/renew",
        method="POST",
        json={"dias": 1},
    ):
        response = loans_module.renew_loan("loan-1")

    assert response.get_json()["data_devolucao_prevista"] == utils.add_days("2026-10-15", 21)