import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import api.books as books_module
import api.loans as loans_module
import scanner.routes as scanner_module
import utils
from app import app


def _book_with_five_copies():
    book_id = "book-1"
    metadata = []
    for number in range(1, 6):
        code = f"{number:03d}"
        exemplar_id = f"{book_id}-EX-{code}-uuid-{number}"
        metadata.append({
            "id": exemplar_id,
            "code": code,
            "qr_data": f"EXEMPLAR-{exemplar_id}",
        })
    return {
        "id": book_id,
        "titulo": "Livro de teste",
        "autor": "Autoria",
        "exemplares": 5,
        "exemplares_ids": [item["id"] for item in metadata],
        "exemplares_meta": metadata,
    }


class FakeQuery:
    def __init__(self, table, book, loans):
        self.table_name = table
        self.book = book
        self.loans = loans
        self.action = "select"
        self.filters = {}
        self.payload = None

    def select(self, *_columns):
        self.action = "select"
        return self

    def eq(self, field, value):
        self.filters[field] = value
        return self

    def is_(self, *_args):
        return self

    def update(self, payload):
        self.action = "update"
        self.payload = payload
        return self


class FakeClient:
    def __init__(self, book, loans):
        self.book = book
        self.loans = loans
        self.queried_tables = []

    def table(self, table_name):
        self.queried_tables.append(table_name)
        return FakeQuery(table_name, self.book, self.loans)


def _install_fake_database(monkeypatch, book, loans):
    client = FakeClient(book, loans)

    def fake_sb_exec(query):
        if query.table_name == "livros":
            if query.action == "update":
                book.update(query.payload)
                return [book]
            return [book] if query.filters.get("id") == book["id"] else []
        if query.table_name == "emprestimos":
            return [loan for loan in loans if loan.get("livro_id") == book["id"]]
        raise AssertionError(f"Consulta inesperada à tabela {query.table_name}")

    monkeypatch.setattr(books_module, "get_client", lambda: client)
    monkeypatch.setattr(books_module, "sb_exec", fake_sb_exec)
    monkeypatch.setattr(books_module, "table_ok", lambda *_args: True)
    return client


def test_delete_one_exemplar_preserves_other_ids_and_return_history(monkeypatch):
    book = _book_with_five_copies()
    original_other_copies = [item.copy() for item in book["exemplares_meta"] if item["code"] != "002"]
    history = [{
        "id": "loan-2",
        "livro_id": book["id"],
        "exemplar": "002",
        "exemplar_id": book["exemplares_meta"][1]["qr_data"],
        "devolvido_em": "2026-10-01",
    }]
    client = _install_fake_database(monkeypatch, book, history)

    with app.test_request_context("/api/books/book-1/exemplars/002", method="DELETE"):
        response = books_module.delete_exemplar("book-1", "002")

    updated = response.get_json()
    assert response.status_code == 200
    assert updated["exemplares"] == 4
    assert [item["code"] for item in updated["exemplares_meta"]] == ["001", "003", "004", "005"]
    assert updated["exemplares_meta"] == original_other_copies
    assert history[0]["exemplar"] == "002"
    assert "alunos" not in client.queried_tables

    removed_qr = "EXEMPLAR-book-1-EX-002-uuid-2"
    remaining_qr = "EXEMPLAR-book-1-EX-004-uuid-4"
    assert not scanner_module._is_known_exemplar_qr(updated, removed_qr, "002")
    assert scanner_module._is_known_exemplar_qr(updated, remaining_qr, "004")

    monkeypatch.setattr(loans_module, "sb_exec", lambda _query: [])
    available = loans_module._available_copies(
        client, book["id"], updated["exemplares"], updated["exemplares_ids"], updated["exemplares_meta"]
    )
    assert [item["code"] for item in available] == ["001", "003", "004", "005"]


def test_delete_exemplar_is_rejected_while_that_copy_is_on_loan(monkeypatch):
    book = _book_with_five_copies()
    original_metadata = [item.copy() for item in book["exemplares_meta"]]
    active_loan = [{
        "id": "loan-active",
        "livro_id": book["id"],
        "exemplar": "002",
        "exemplar_id": book["exemplares_meta"][1]["qr_data"],
        "devolvido_em": None,
    }]
    _install_fake_database(monkeypatch, book, active_loan)

    with app.test_request_context("/api/books/book-1/exemplars/002", method="DELETE"):
        result = books_module.delete_exemplar("book-1", "002")

    response, status = result
    assert status == 409
    assert "emprestado" in response.get_json()["error"]
    assert book["exemplares_meta"] == original_metadata


def test_increasing_copy_count_appends_new_codes_without_changing_existing_qrs(monkeypatch):
    book = _book_with_five_copies()
    book["exemplares_meta"] = [item for item in book["exemplares_meta"] if item["code"] != "002"]
    book["exemplares_ids"] = [item["id"] for item in book["exemplares_meta"]]
    book["exemplares"] = len(book["exemplares_meta"])
    previous = [item.copy() for item in book["exemplares_meta"]]
    client = _install_fake_database(monkeypatch, book, [])

    with app.test_request_context(
        "/api/books/book-1", method="PUT", json={"exemplares": 5}
    ):
        response = books_module.update_book("book-1")

    updated = response.get_json()
    assert response.status_code == 200
    assert updated["exemplares"] == 5
    assert updated["exemplares_meta"][:len(previous)] == previous
    assert [item["code"] for item in updated["exemplares_meta"]] == ["001", "003", "004", "005", "006"]
    assert updated["exemplares_ids"] == [item["id"] for item in updated["exemplares_meta"]]
    assert updated["exemplares_meta"][-1]["qr_data"].startswith("EXEMPLAR-book-1-EX-006-")
    assert client.queried_tables == ["livros", "livros"]

    monkeypatch.setattr(utils, "get_client", lambda: client)
    monkeypatch.setattr(utils, "sb_exec", lambda _query: [book])
    generated_qrs = []
    monkeypatch.setattr(
        scanner_module,
        "_build_card",
        lambda **kwargs: generated_qrs.append(kwargs["qr_data"]) or "image-data",
    )
    with app.test_request_context("/api/qr/card/book/book-1"):
        response = scanner_module.book_card("book-1")

    assert response.status_code == 200
    assert len(response.get_json()["cards"]) == 5
    assert updated["exemplares_meta"][-1]["qr_data"] in generated_qrs


def test_copy_count_cannot_shrink_and_renumber_existing_exemplars(monkeypatch):
    book = _book_with_five_copies()
    original_metadata = [item.copy() for item in book["exemplares_meta"]]
    _install_fake_database(monkeypatch, book, [])

    with app.test_request_context(
        "/api/books/book-1", method="PUT", json={"exemplares": 3}
    ):
        result = books_module.update_book("book-1")

    response, status = result
    assert status == 409
    assert "removendo cada exemplar" in response.get_json()["error"]
    assert book["exemplares_meta"] == original_metadata