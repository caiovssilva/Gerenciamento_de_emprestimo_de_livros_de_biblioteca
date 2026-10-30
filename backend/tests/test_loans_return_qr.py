import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import api.loans as loans_module
import scanner.routes as scanner_module
import utils
from app import app


class FakeQuery:
    def __init__(self, loan):
        self.loan = loan
        self.action = "select"
        self.payload = None

    def select(self, *_columns):
        self.action = "select"
        return self

    def update(self, payload):
        self.action = "update"
        self.payload = payload
        return self

    def eq(self, _field, value):
        self.loan_id = value
        return self


class FakeSupabase:
    def __init__(self, loan):
        self.loan = loan

    def table(self, _table_name):
        return FakeQuery(self.loan)


def _call_return(monkeypatch, payload, trusted_self_service=False):
    loan = {
        "id": "loan-1",
        "livro_id": "book-1",
        "aluno_id": "student-1",
        "exemplar": "002",
        "exemplar_id": "book-1-EX-002-uuid",
        "devolvido_em": None,
    }
    client = FakeSupabase(loan)

    def fake_sb_exec(query):
        if query.action == "select":
            return [loan] if query.loan_id == loan["id"] else []
        if query.action == "update":
            loan.update(query.payload)
            return [loan]
        return []

    monkeypatch.setattr(loans_module, "get_client", lambda: client)
    monkeypatch.setattr(loans_module, "sb_exec", fake_sb_exec)
    with app.test_request_context("/api/loans/loan-1/return", method="POST", json=payload):
        result = loans_module.return_loan("loan-1", trusted_self_service=trusted_self_service)
    response, status = result if isinstance(result, tuple) else (result, 200)
    return response.get_json(), status, loan


def test_return_requires_exemplar_qr(monkeypatch):
    result, status, loan = _call_return(monkeypatch, {})

    assert status == 400
    assert "QR" in result["error"]
    assert loan["devolvido_em"] is None


def test_return_rejects_qr_for_another_exemplar(monkeypatch):
    result, status, loan = _call_return(monkeypatch, {"exemplar_qr": "EXEMPLAR-book-1-EX-001-uuid"})

    assert status == 403
    assert "não corresponde" in result["error"]
    assert loan["devolvido_em"] is None


def test_return_rejects_same_exemplar_number_from_another_book(monkeypatch):
    result, status, loan = _call_return(monkeypatch, {"exemplar_qr": "EXEMPLAR-book-2-EX-002-uuid"})

    assert status == 403
    assert "não corresponde" in result["error"]
    assert loan["devolvido_em"] is None


def test_return_accepts_matching_exemplar_qr(monkeypatch):
    result, status, loan = _call_return(monkeypatch, {"exemplar_qr": "EXEMPLAR-book-1-EX-002-uuid"})

    assert status == 200
    assert result["devolvido_em"]
    assert loan["devolvido_em"] == result["devolvido_em"]


def test_return_accepts_authenticated_self_service_without_qr(monkeypatch):
    result, status, loan = _call_return(monkeypatch, {}, trusted_self_service=True)

    assert status == 200
    assert result["devolvido_em"]
    assert loan["devolvido_em"] == result["devolvido_em"]


def test_return_accepts_same_copy_code_with_legacy_identifier(monkeypatch):
    result, status, loan = _call_return(monkeypatch, {"exemplar_qr": "EXEMPLAR-book-1-EX-002-reprinted-card"})

    assert status == 200
    assert result["devolvido_em"]
    assert loan["devolvido_em"] == result["devolvido_em"]


def test_return_accepts_raw_exemplar_id_from_legacy_card(monkeypatch):
    result, status, loan = _call_return(monkeypatch, {"exemplar_qr": "book-1-EX-002-uuid"})

    assert status == 200
    assert result["devolvido_em"]
    assert loan["devolvido_em"] == result["devolvido_em"]


def test_exemplar_match_normalizes_numeric_code_padding():
    assert loans_module._matches_loan_exemplar_qr(
        {"livro_id": "book-1", "exemplar": "2", "exemplar_id": "legacy-id"},
        "EXEMPLAR-book-1-EX-002-reprinted-card",
    )


def _call_renew(monkeypatch, payload, trusted_self_service=False):
    import api.controle as controle_module

    loan = {
        "id": "loan-1",
        "livro_id": "book-1",
        "aluno_id": "student-1",
        "exemplar": "002",
        "exemplar_id": "book-1-EX-002-uuid",
        "data_devolucao_prevista": "2026-10-15",
        "renovacoes": 0,
        "devolvido_em": None,
    }
    client = FakeSupabase(loan)

    def fake_sb_exec(query):
        if query.action == "select":
            return [loan] if query.loan_id == loan["id"] else []
        if query.action == "update":
            loan.update(query.payload)
            return [loan]
        return []

    monkeypatch.setattr(loans_module, "get_client", lambda: client)
    monkeypatch.setattr(loans_module, "sb_exec", fake_sb_exec)
    monkeypatch.setattr(controle_module, "get_self_service_settings", lambda: {"renewal_days": 7})
    with app.test_request_context("/api/loans/loan-1/renew", method="POST", json=payload):
        result = loans_module.renew_loan("loan-1", trusted_self_service=trusted_self_service)
    response, status = result if isinstance(result, tuple) else (result, 200)
    return response.get_json(), status, loan


def test_renew_requires_exemplar_qr(monkeypatch):
    result, status, loan = _call_renew(monkeypatch, {})

    assert status == 400
    assert "QR" in result["error"]
    assert loan["renovacoes"] == 0


def test_renew_rejects_qr_for_another_exemplar(monkeypatch):
    result, status, loan = _call_renew(monkeypatch, {"exemplar_qr": "EXEMPLAR-book-1-EX-001-uuid"})

    assert status == 403
    assert "não corresponde" in result["error"]
    assert loan["renovacoes"] == 0


def test_renew_accepts_matching_exemplar_qr(monkeypatch):
    result, status, loan = _call_renew(monkeypatch, {"exemplar_qr": "EXEMPLAR-book-1-EX-002-uuid"})

    assert status == 200
    assert result["renovacoes"] == 1
    assert loan["renovacoes"] == 1


def test_renew_accepts_authenticated_self_service_without_qr(monkeypatch):
    result, status, loan = _call_renew(monkeypatch, {}, trusted_self_service=True)

    assert status == 200
    assert result["renovacoes"] == 1
    assert loan["renovacoes"] == 1


def test_legacy_book_cards_get_unique_qr_per_copy(monkeypatch):
    book = {
        "id": "book-legacy",
        "titulo": "Livro antigo",
        "autor": "Autoria",
        "exemplares": 2,
    }

    class Query:
        def select(self, *_columns):
            return self

        def eq(self, *_args):
            return self

    class Client:
        def table(self, _table_name):
            return Query()

    monkeypatch.setattr(utils, "get_client", lambda: Client())
    monkeypatch.setattr(utils, "sb_exec", lambda _query: [book])
    generated_qrs = []

    def fake_build_card(**kwargs):
        generated_qrs.append(kwargs["qr_data"])
        return "image-data"

    monkeypatch.setattr(scanner_module, "_build_card", fake_build_card)
    with app.test_request_context("/api/qr/card/book/book-legacy"):
        response = scanner_module.book_card("book-legacy")

    assert response.status_code == 200
    assert generated_qrs == [
        "EXEMPLAR-book-legacy-EX-001-book-legacy-001",
        "EXEMPLAR-book-legacy-EX-002-book-legacy-002",
    ]