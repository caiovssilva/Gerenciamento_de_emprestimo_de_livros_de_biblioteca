import base64
import os
import sys
from io import BytesIO

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import app
import api.students as students_module
import api.controle as controle_module
import scanner.routes as scanner_module
import utils


@pytest.fixture()
def client():
    app.config.update(TESTING=True)
    with app.test_client() as client:
        yield client


def _make_qr_image(data: str) -> str:
    import qrcode

    qr = qrcode.QRCode(version=1, box_size=6, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def test_get_book_and_student_by_id(client):
    book_response = client.post(
        "/api/books/",
        json={"titulo": "Livro QR Teste", "autor": "Autor Teste", "exemplares": 1},
    )
    assert book_response.status_code == 201
    book = book_response.get_json()

    student_response = client.post(
        "/api/students/",
        json={"nome": "Aluno QR", "turma": "INF3A", "carteirinha": "ALUQR001"},
    )
    assert student_response.status_code == 201
    student = student_response.get_json()

    get_book_response = client.get(f"/api/books/{book['id']}")
    assert get_book_response.status_code == 200
    assert get_book_response.get_json()["id"] == book["id"]

    get_student_response = client.get(f"/api/students/{student['id']}")
    assert get_student_response.status_code == 200
    assert get_student_response.get_json()["id"] == student["id"]


def test_qr_decode_resolves_student_by_id(client):
    student_response = client.post(
        "/api/students/",
        json={"nome": "Aluno QR Decode", "turma": "INF3B", "carteirinha": "ALUQR002"},
    )
    assert student_response.status_code == 201
    student = student_response.get_json()

    qr_image = _make_qr_image(student["id"])
    decode_response = client.post("/api/qr/decode", json={"image": qr_image})

    assert decode_response.status_code == 200
    payload = decode_response.get_json()
    assert payload["type"] == "student"
    assert payload["data"]["id"] == student["id"]


def test_self_service_qr_decode_only_returns_registered_exemplar(monkeypatch, client):
    exemplar_qr = "EXEMPLAR-book-1-EX-001-copy-1"
    settings = {
        **controle_module.DEFAULT_SETTINGS,
        "enabled": True,
        "allow_borrow": True,
    }
    monkeypatch.setattr(controle_module, "get_self_service_settings", lambda: settings)

    class HealthQuery:
        def select(self, *_columns):
            return self

        def limit(self, _count):
            return self

    class HealthClient:
        def table(self, _name):
            return HealthQuery()

    monkeypatch.setattr(utils, "get_client", lambda: HealthClient())
    monkeypatch.setattr(utils, "sb_exec", lambda _query: [])
    monkeypatch.setattr(scanner_module, "_resolve_qr", lambda code: {
        "type": "book" if code == exemplar_qr else "student",
        "data": ({
            "id": "book-1",
            "titulo": "Título privado",
            "exemplar_code": "001",
            "exemplar_id": "copy-1",
        } if code == exemplar_qr else {
            "id": "student-other",
            "nome": "Outro aluno",
            "carteirinha": "OTHER-CARD",
        }),
    })

    with client.session_transaction() as current_session:
        current_session["access_scope"] = "self_service"
        current_session["student_id"] = "student-1"

    card_response = client.post("/api/qr/decode", json={"image": _make_qr_image("OTHER-CARD")})
    exemplar_response = client.post("/api/qr/decode", json={"image": _make_qr_image(exemplar_qr)})

    assert card_response.status_code == 200
    assert card_response.get_json()["type"] == "unknown"
    assert card_response.get_json()["data"] is None
    assert exemplar_response.status_code == 200
    assert exemplar_response.get_json()["type"] == "book"
    assert exemplar_response.get_json()["data"] == {
        "id": "book-1",
        "exemplar_code": "001",
        "exemplar_id": "copy-1",
    }


def test_get_student_resolves_dotted_card_number_without_uuid_lookup(monkeypatch):
    student = {
        "id": "student-uuid",
        "nome": "Aluno da carteirinha",
        "carteirinha": "185548.1.32021194",
        "turma": "INF3A",
    }

    class Query:
        def __init__(self):
            self.field = None
            self.value = None

        def select(self, *_columns):
            return self

        def eq(self, field, value):
            self.field = field
            self.value = value
            return self

    query = Query()

    class Client:
        def table(self, _name):
            return query

    def execute(current_query):
        assert current_query.field == "carteirinha"
        return [student] if current_query.value == student["carteirinha"] else []

    monkeypatch.setattr(students_module, "get_client", lambda: Client())
    monkeypatch.setattr(students_module, "table_ok", lambda *_args: True)
    monkeypatch.setattr(students_module, "sb_exec", execute)

    with app.test_request_context("/api/students/185548.1.32021194"):
        response = students_module.get_student("185548.1.32021194")

    assert response.status_code == 200
    assert response.get_json()["id"] == "student-uuid"


def test_self_service_qr_decode_exposes_only_registered_exemplar_data(client, monkeypatch):
    import api.controle as controle_module
    import scanner.routes as scanner_module
    import utils

    class Query:
        def select(self, *_columns):
            return self

        def limit(self, _count):
            return self

        def execute(self):
            return []

    class DatabaseClient:
        def table(self, _name):
            return Query()

    settings = {
        **controle_module.DEFAULT_SETTINGS,
        "enabled": True,
        "allow_return": True,
    }
    monkeypatch.setattr(controle_module, "get_self_service_settings", lambda: settings)
    monkeypatch.setattr(utils, "get_client", lambda: DatabaseClient())
    monkeypatch.setattr(scanner_module, "_resolve_qr", lambda code: {
        "type": "student" if code == "CARD-SECRET" else "book",
        "data": {
            "id": "student-secret" if code == "CARD-SECRET" else "book-1",
            "nome": "Dados privados",
            "titulo": "Livro cadastrado",
            "exemplar_code": None if code == "CARD-SECRET" else "004",
            "exemplar_id": None if code == "CARD-SECRET" else "copy-secret",
        },
    })

    with client.session_transaction() as flask_session:
        flask_session["access_scope"] = "self_service"

    student_response = client.post(
        "/api/qr/decode", json={"image": _make_qr_image("CARD-SECRET")},
    )
    exemplar_response = client.post(
        "/api/qr/decode", json={"image": _make_qr_image("EXEMPLAR-book-1-EX-004-copy-secret")},
    )

    assert student_response.status_code == 200
    assert student_response.get_json()["type"] == "unknown"
    assert student_response.get_json()["data"] is None
    assert exemplar_response.status_code == 200
    assert exemplar_response.get_json()["type"] == "book"
    assert exemplar_response.get_json()["data"] == {
        "id": "book-1",
        "exemplar_code": "004",
        "exemplar_id": "copy-secret",
    }