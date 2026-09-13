import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import api.books as books


@pytest.fixture(autouse=True)
def clear_isbn_cache():
    books._ISBN_CACHE.clear()
    books._ISBN_CACHE_TIMESTAMPS.clear()
    yield
    books._ISBN_CACHE.clear()
    books._ISBN_CACHE_TIMESTAMPS.clear()


def test_validate_isbn10_and_isbn13_with_formatting():
    books._validate_isbn(books._normalize_isbn("0-306-40615-2"))
    books._validate_isbn(books._normalize_isbn("978 85 7683 130 3"))
    books._validate_isbn(books._normalize_isbn("0-8044-2957-X"))


@pytest.mark.parametrize("isbn", ["0-306-40615-3", "9788576831302", "978857683130X"])
def test_invalid_checksum_is_rejected_before_lookup(isbn):
    with pytest.raises(ValueError):
        books._lookup_isbn(isbn)


def test_fallback_complements_partial_data_and_caches_only_complete_result(monkeypatch):
    calls = []

    def google(_isbn):
        calls.append("google")
        return {"isbn": "9788576831303", "titulo": "Livro", "autor": "", "categorias": []}

    def isbnsearch(_isbn):
        calls.append("isbnsearch")
        return {"isbn": "9788576831303", "titulo": "", "autor": "Autora", "categorias": []}

    def openlibrary(_isbn):
        calls.append("openlibrary")
        return {"isbn": "9788576831303", "titulo": "Livro", "autor": "", "categorias": ["History"]}

    monkeypatch.setattr(books, "_google_books_lookup", google)
    monkeypatch.setattr(books, "_isbnsearch_lookup", isbnsearch)
    monkeypatch.setattr(books, "_openlibrary_lookup", openlibrary)
    monkeypatch.setattr(books, "_match_genre", lambda categories: ("genre-id", "História"))

    result = books._lookup_isbn("978-85-7683-130-3")

    assert calls == ["google", "isbnsearch", "openlibrary"]
    assert result["titulo"] == "Livro"
    assert result["autor"] == "Autora"
    assert result["categorias"] == ["History"]
    assert result["genero_id"] == "genre-id"
    assert "9788576831303" in books._ISBN_CACHE


def test_complete_result_avoids_later_provider(monkeypatch):
    calls = []

    def provider(_isbn):
        calls.append("google")
        return {"isbn": "9788576831303", "titulo": "Livro", "autor": "Autora", "categorias": ["History"]}

    monkeypatch.setattr(books, "_google_books_lookup", provider)
    monkeypatch.setattr(books, "_isbnsearch_lookup", lambda _isbn: calls.append("isbnsearch"))
    monkeypatch.setattr(books, "_openlibrary_lookup", lambda _isbn: calls.append("openlibrary"))
    monkeypatch.setattr(books, "_match_genre", lambda categories: ("", ""))

    books._lookup_isbn("9788576831303")

    assert calls == ["google"]


def test_temporary_provider_failure_is_retried_and_falls_back(monkeypatch):
    calls = []

    def failing_google(_isbn):
        calls.append("google")
        raise books._ProviderError("Google Books", "temporariamente indisponível")

    def isbnsearch(_isbn):
        calls.append("isbnsearch")
        return {"isbn": "9788576831303", "titulo": "Livro", "autor": "Autora", "categorias": ["History"]}

    monkeypatch.setattr(books, "_google_books_lookup", failing_google)
    monkeypatch.setattr(books, "_isbnsearch_lookup", isbnsearch)
    monkeypatch.setattr(books, "_openlibrary_lookup", lambda _isbn: calls.append("openlibrary"))
    monkeypatch.setattr(books.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(books, "_match_genre", lambda categories: ("", ""))

    result = books._lookup_isbn("9788576831303")

    assert result["autor"] == "Autora"
    assert calls == ["google", "isbnsearch"]


def test_all_not_found_providers_return_lookup_error(monkeypatch):
    not_found = lambda _isbn: (_ for _ in ()).throw(books.LookupError("não encontrado"))
    monkeypatch.setattr(books, "_google_books_lookup", not_found)
    monkeypatch.setattr(books, "_isbnsearch_lookup", not_found)
    monkeypatch.setattr(books, "_openlibrary_lookup", not_found)

    with pytest.raises(LookupError):
        books._lookup_isbn("9788576831303")


def test_route_distinguishes_invalid_and_not_found(monkeypatch):
    from app import app

    app.config.update(TESTING=True)
    monkeypatch.setattr(books, "_lookup_isbn", lambda _isbn: (_ for _ in ()).throw(LookupError("Livro não encontrado")))
    with app.test_client() as client:
        not_found = client.get("/api/books/isbn-lookup?isbn=9788576831303")
        invalid = client.get("/api/books/isbn-lookup?isbn=9788576831302")

    assert not_found.status_code == 404
    assert invalid.status_code == 400