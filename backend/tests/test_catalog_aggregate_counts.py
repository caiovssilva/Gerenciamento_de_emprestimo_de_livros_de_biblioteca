import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import api.genres as genres_module
import api.rooms as rooms_module
from app import app


class FakeQuery:
    def __init__(self, table_name):
        self.table_name = table_name

    def select(self, *_columns):
        return self

    def order(self, *_args, **_kwargs):
        return self

    def is_(self, *_args):
        return self


class FakeClient:
    def table(self, table_name):
        return FakeQuery(table_name)


def test_genre_counts_use_one_books_query(monkeypatch):
    query_tables = []
    genres = [
        {"id": "g1", "nome": "Fantasia"},
        {"id": "g2", "nome": "História"},
        {"id": "g3", "nome": "Poesia"},
    ]
    books = [
        {"genero_id": "g1"},
        {"genero_id": "g1"},
        {"genero_id": "g2"},
    ]

    def fake_sb_exec(query):
        query_tables.append(query.table_name)
        return genres if query.table_name == "generos" else books

    monkeypatch.setattr(genres_module, "get_client", FakeClient)
    monkeypatch.setattr(genres_module, "table_ok", lambda *_args: True)
    monkeypatch.setattr(genres_module, "sb_exec", fake_sb_exec)
    monkeypatch.setattr(genres_module, "read_json", lambda _path: [])

    with app.app_context():
        response = genres_module.list_genres()

    assert response.get_json() == [
        {"id": "g1", "nome": "Fantasia", "total_livros": 2},
        {"id": "g2", "nome": "História", "total_livros": 1},
        {"id": "g3", "nome": "Poesia", "total_livros": 0},
    ]
    assert query_tables == ["generos", "livros"]


def test_room_counts_use_one_students_query(monkeypatch):
    query_tables = []
    rooms = [
        {"id": "r1", "nome": "Sala 1"},
        {"id": "r2", "nome": "Sala 2"},
        {"id": "r3", "nome": "Sala 3"},
    ]
    students = [
        {"sala_id": "r1"},
        {"sala_id": "r1"},
        {"sala_id": "r2"},
        {"sala_id": None},
    ]

    def fake_sb_exec(query):
        query_tables.append(query.table_name)
        return rooms if query.table_name == "salas" else students

    monkeypatch.setattr(rooms_module, "get_client", FakeClient)
    monkeypatch.setattr(rooms_module, "table_ok", lambda *_args: True)
    monkeypatch.setattr(rooms_module, "has_deleted_at", lambda *_args: False)
    monkeypatch.setattr(rooms_module, "sb_exec", fake_sb_exec)
    monkeypatch.setattr(rooms_module, "read_json", lambda _path: [])

    with app.app_context():
        response = rooms_module.list_rooms()

    assert response.get_json() == [
        {"id": "r1", "nome": "Sala 1", "total_alunos": 2},
        {"id": "r2", "nome": "Sala 2", "total_alunos": 1},
        {"id": "r3", "nome": "Sala 3", "total_alunos": 0},
    ]
    assert query_tables == ["salas", "alunos"]