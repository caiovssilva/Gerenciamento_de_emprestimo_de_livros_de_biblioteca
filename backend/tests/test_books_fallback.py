import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app as app_module
import api.books as books_module


def test_list_books_falls_back_to_local_data_when_supabase_is_unavailable(monkeypatch):
    def failing_client():
        raise OSError("[Errno -2] Name or service not known")

    monkeypatch.setattr(books_module, "get_client", failing_client)

    with app_module.app.test_request_context("/api/books/?q=&genre="):
        response = books_module.list_books()

    assert response.status_code == 200
    data = json.loads(response.get_data(as_text=True))
    assert isinstance(data, list)
    assert data


def test_delete_book_with_loan_history_does_not_delete_book_or_touch_students(monkeypatch):
    queried_tables = []

    class Query:
        def __init__(self, table):
            self.table = table
            self.action = "select"

        def select(self, *_columns):
            self.action = "select"
            return self

        def eq(self, *_args):
            return self

        def update(self, _payload):
            self.action = "update"
            return self

        def delete(self):
            self.action = "delete"
            return self

    class Client:
        def table(self, name):
            queried_tables.append(name)
            return Query(name)

    def fake_sb_exec(query):
        if query.table == "emprestimos":
            return [{"id": "loan-1", "devolvido_em": "2026-10-01"}]
        if query.action == "delete":
            raise AssertionError("A exclusão física apagaria o histórico em cascata")
        return []

    monkeypatch.setattr(books_module, "get_client", lambda: Client())
    monkeypatch.setattr(books_module, "sb_exec", fake_sb_exec)
    monkeypatch.setattr(books_module, "table_ok", lambda *_args: True)
    monkeypatch.setattr(books_module, "has_deleted_at", lambda *_args: False)

    with app_module.app.test_request_context("/api/books/book-1", method="DELETE"):
        response, status = books_module.delete_book("book-1")

    assert status == 409
    assert "histórico" in response.get_json()["error"]
    assert "alunos" not in queried_tables
