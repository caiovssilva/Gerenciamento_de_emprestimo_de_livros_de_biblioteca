import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app as app_module
import api.books as books_module


def test_create_book_generates_distinct_ids_and_qr_codes_for_same_title(monkeypatch):
    saved = []

    def fake_read_json(path):
        return []

    def fake_write_json(path, data):
        saved.append(list(data))

    monkeypatch.setattr(books_module, "get_client", lambda: object())
    monkeypatch.setattr(books_module, "table_ok", lambda sb, table: False)
    monkeypatch.setattr(books_module, "read_json", fake_read_json)
    monkeypatch.setattr(books_module, "write_json", fake_write_json)

    with app_module.app.test_client() as client:
        first = client.post(
            "/api/books/",
            json={"titulo": "Mesmo Livro", "autor": "Mesmo Autor", "exemplares": 2},
        )
        second = client.post(
            "/api/books/",
            json={"titulo": "Mesmo Livro", "autor": "Mesmo Autor", "exemplares": 2},
        )

    assert first.status_code == 201
    assert second.status_code == 201

    first_data = first.get_json()
    second_data = second.get_json()

    assert first_data["id"] != second_data["id"]
    assert first_data["exemplares_ids"][0] != second_data["exemplares_ids"][0]