import base64
import os
import sys
from io import BytesIO

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import app


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