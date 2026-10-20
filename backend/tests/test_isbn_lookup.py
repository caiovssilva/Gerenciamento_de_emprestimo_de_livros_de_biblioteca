import base64
import io
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import api.books as books

openlibrary_search_lookup = books._openlibrary_search_lookup
isbndb_lookup = books._isbndb_lookup


def _isbn13_for_sequence(sequence):
    body = f"978{sequence:09d}"
    weighted_sum = sum(int(digit) * (1 if index % 2 == 0 else 3) for index, digit in enumerate(body))
    return body + str((10 - weighted_sum % 10) % 10)


@pytest.fixture(autouse=True)
def clear_isbn_cache(monkeypatch):
    books._ISBN_CACHE.clear()
    books._ISBN_CACHE_TIMESTAMPS.clear()
    not_found = lambda _isbn: (_ for _ in ()).throw(LookupError("não encontrado"))
    monkeypatch.setattr(books, "_openlibrary_search_lookup", not_found)
    monkeypatch.setattr(books, "_isbndb_lookup", not_found)
    monkeypatch.delenv("ISBNDB_API_KEY", raising=False)
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


@pytest.mark.parametrize("sequence", range(100))
def test_lookup_pipeline_handles_100_varied_valid_isbns(monkeypatch, sequence):
    isbn = _isbn13_for_sequence(sequence)
    normalized = books._normalize_isbn(isbn)
    result = {
        "isbn": normalized,
        "titulo": f"Livro de teste {sequence}",
        "autor": f"Autor {sequence}",
        "categorias": ["Testes"],
    }
    for provider in ("_google_books_lookup", "_isbnsearch_lookup", "_openlibrary_lookup"):
        monkeypatch.setattr(books, provider, lambda _isbn, value=result: value)
    monkeypatch.setattr(books, "_match_genre", lambda _categories: ("", ""))

    formatted_isbn = f"{isbn[:3]}-{isbn[3:6]}-{isbn[6:10]}-{isbn[10:]}"
    lookup = books._lookup_isbn(formatted_isbn)

    assert lookup["isbn"] == normalized
    assert lookup["titulo"] == f"Livro de teste {sequence}"
    assert lookup["autor"] == f"Autor {sequence}"


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
    monkeypatch.setattr(books, "_groq_lookup", lambda _isbn: (_ for _ in ()).throw(LookupError()))
    monkeypatch.setattr(books, "_match_genre", lambda categories: ("genre-id", "História"))

    result = books._lookup_isbn("978-85-7683-130-3")

    assert sorted(calls) == ["google", "isbnsearch", "openlibrary"]
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
    monkeypatch.setattr(books, "_groq_lookup", lambda _isbn: (_ for _ in ()).throw(LookupError()))
    monkeypatch.setattr(books, "_match_genre", lambda categories: ("", ""))

    books._lookup_isbn("9788576831303")

    assert sorted(calls) == ["google", "isbnsearch", "openlibrary"]


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
    assert sorted(calls) == ["google", "isbnsearch", "openlibrary"]


def test_manual_lookup_does_not_call_groq(monkeypatch):
    monkeypatch.setattr(books, "_groq_lookup", lambda _isbn: pytest.fail("Groq não deve ser usado no modo manual"))
    monkeypatch.setattr(books, "_google_books_lookup", lambda _isbn: {
        "isbn": "9788576831303", "titulo": "Livro", "autor": "Autora", "categorias": ["History"]
    })
    monkeypatch.setattr(books, "_isbnsearch_lookup", lambda _isbn: {
        "isbn": "9788576831303", "titulo": "", "autor": "", "categorias": []
    })
    monkeypatch.setattr(books, "_openlibrary_lookup", lambda _isbn: {
        "isbn": "9788576831303", "titulo": "", "autor": "", "categorias": []
    })
    monkeypatch.setattr(books, "_match_genre", lambda categories: ("", ""))

    result = books._lookup_isbn("9788576831303")

    assert result["titulo"] == "Livro"


def test_groq_conflict_is_replaced_by_bibliographic_consensus(monkeypatch):
    monkeypatch.setattr(books, "_groq_lookup", lambda _isbn: {
        "isbn": "9788532511010", "titulo": "Araucária", "autor": "Autor Groq", "categorias": ["Groq"]
    })
    bibliographic = {
        "isbn": "9788532511010",
        "titulo": "Harry Potter e a Pedra Filosofal",
        "autor": "J. K. Rowling",
        "categorias": ["Fantasy"],
    }
    for provider in ("_google_books_lookup", "_isbnsearch_lookup", "_openlibrary_lookup"):
        monkeypatch.setattr(books, provider, lambda _isbn, value=bibliographic: value)
    monkeypatch.setattr(books, "_match_genre", lambda categories: ("", ""))

    result = books._lookup_isbn("978-8532511010", use_groq=True)

    assert result["titulo"] == "Harry Potter e a Pedra Filosofal"
    assert result["autor"] == "J. K. Rowling"


def test_groq_is_fallback_when_bibliographic_sources_find_nothing(monkeypatch):
    groq_result = {"isbn": "9788532511010", "titulo": "Livro X", "autor": "Autor X", "categorias": []}
    monkeypatch.setattr(books, "_groq_lookup", lambda _isbn: groq_result)
    not_found = lambda _isbn: (_ for _ in ()).throw(LookupError("não encontrado"))
    monkeypatch.setattr(books, "_google_books_lookup", not_found)
    monkeypatch.setattr(books, "_isbnsearch_lookup", not_found)
    monkeypatch.setattr(books, "_openlibrary_lookup", not_found)
    monkeypatch.setattr(books, "_match_genre", lambda categories: ("", ""))

    result = books._lookup_isbn("9788532511010", use_groq=True)

    assert result["titulo"] == "Livro X"
    assert result["autor"] == "Autor X"


def test_bibliographic_sources_complete_fields_from_each_other(monkeypatch):
    monkeypatch.setattr(books, "_groq_lookup", lambda _isbn: {
        "isbn": "9788532511010", "titulo": "", "autor": "", "categorias": []
    })
    monkeypatch.setattr(books, "_google_books_lookup", lambda _isbn: {
        "isbn": "9788532511010", "titulo": "Livro X", "autor": "", "categorias": []
    })
    monkeypatch.setattr(books, "_isbnsearch_lookup", lambda _isbn: {
        "isbn": "9788532511010", "titulo": "", "autor": "Autor X", "categorias": []
    })
    monkeypatch.setattr(books, "_openlibrary_lookup", lambda _isbn: {
        "isbn": "9788532511010", "titulo": "", "autor": "", "categorias": []
    })
    monkeypatch.setattr(books, "_match_genre", lambda categories: ("", ""))

    result = books._lookup_isbn("9788532511010", use_groq=True)

    assert result["titulo"] == "Livro X"
    assert result["autor"] == "Autor X"


def test_route_manual_does_not_call_groq(monkeypatch):
    from app import app

    monkeypatch.setattr(books, "_groq_lookup", lambda _isbn: pytest.fail("Groq não deve ser chamado no modo manual"))
    complete = {"isbn": "9788532511010", "titulo": "Livro", "autor": "Autor", "categorias": ["History"]}
    monkeypatch.setattr(books, "_google_books_lookup", lambda _isbn: complete)
    monkeypatch.setattr(books, "_isbnsearch_lookup", lambda _isbn: complete)
    monkeypatch.setattr(books, "_openlibrary_lookup", lambda _isbn: complete)
    monkeypatch.setattr(books, "_match_genre", lambda categories: ("", ""))

    with app.test_client() as client:
        response = client.get("/api/books/isbn-lookup?isbn=9788532511010&source=manual")

    assert response.status_code == 200


def test_route_scanner_uses_groq(monkeypatch):
    from app import app
    calls = []

    def groq(_isbn):
        calls.append(_isbn)
        return {"isbn": _isbn, "titulo": "Livro Groq", "autor": "Autor Groq", "categorias": []}

    monkeypatch.setattr(books, "_groq_lookup", groq)
    not_found = lambda _isbn: (_ for _ in ()).throw(LookupError("não encontrado"))
    monkeypatch.setattr(books, "_google_books_lookup", not_found)
    monkeypatch.setattr(books, "_isbnsearch_lookup", not_found)
    monkeypatch.setattr(books, "_openlibrary_lookup", not_found)
    monkeypatch.setattr(books, "_match_genre", lambda categories: ("", ""))

    with app.test_client() as client:
        response = client.get("/api/books/isbn-lookup?isbn=978-8532511010&source=scanner")

    assert response.status_code == 200
    assert calls == ["9788532511010"]


def test_all_sources_receive_the_same_normalized_isbn(monkeypatch):
    received = []
    result = {"isbn": "9788532511010", "titulo": "Livro", "autor": "Autor", "categorias": ["History"]}
    for provider in ("_groq_lookup", "_google_books_lookup", "_isbnsearch_lookup", "_openlibrary_lookup"):
        monkeypatch.setattr(books, provider, lambda isbn, value=result: (received.append(isbn) or value))
    monkeypatch.setattr(books, "_match_genre", lambda categories: ("", ""))

    books._lookup_isbn("978-8532511010", use_groq=True)

    assert received == ["9788532511010"] * 4


def test_bibliographic_consensus_beats_google_priority(monkeypatch):
    monkeypatch.setattr(books, "_google_books_lookup", lambda _isbn: {
        "isbn": "9788532511010", "titulo": "Livro A", "autor": "Autor", "categorias": []
    })
    monkeypatch.setattr(books, "_isbnsearch_lookup", lambda _isbn: {
        "isbn": "9788532511010", "titulo": "Livro B", "autor": "Autor", "categorias": []
    })
    monkeypatch.setattr(books, "_openlibrary_lookup", lambda _isbn: {
        "isbn": "9788532511010", "titulo": "Livro B", "autor": "Autor", "categorias": []
    })
    monkeypatch.setattr(books, "_match_genre", lambda categories: ("", ""))

    result = books._lookup_isbn("9788532511010")

    assert result["titulo"] == "Livro B"


def test_google_priority_wins_without_bibliographic_consensus(monkeypatch):
    monkeypatch.setattr(books, "_google_books_lookup", lambda _isbn: {
        "isbn": "9788532511010", "titulo": "Livro A", "autor": "Autor", "categorias": []
    })
    monkeypatch.setattr(books, "_isbnsearch_lookup", lambda _isbn: {
        "isbn": "9788532511010", "titulo": "Livro B", "autor": "Autor", "categorias": []
    })
    monkeypatch.setattr(books, "_openlibrary_lookup", lambda _isbn: {
        "isbn": "9788532511010", "titulo": "", "autor": "Autor", "categorias": []
    })
    monkeypatch.setattr(books, "_match_genre", lambda categories: ("", ""))

    result = books._lookup_isbn("9788532511010")

    assert result["titulo"] == "Livro A"


def _vision_frame():
    return "data:image/jpeg;base64," + base64.b64encode(b"temporary-frame").decode()


def _mock_groq_vision(monkeypatch, content, calls=None):
    class Completion:
        def create(self, **payload):
            if calls is not None:
                calls.append(payload)
            return type("Response", (), {
                "choices": [type("Choice", (), {
                    "message": type("Message", (), {"content": content})()
                })()]
            })()

    client = type("Client", (), {"chat": type("Chat", (), {"completions": Completion()})()})
    monkeypatch.setattr(books, "OpenAI", lambda **kwargs: client())


def test_groq_vision_extracts_and_normalizes_isbn(monkeypatch):
    calls = []
    _mock_groq_vision(monkeypatch, '{"encontrado": true, "isbn": "978-85-3251-101-0"}', calls)

    result = books._groq_isbn_from_image(_vision_frame())

    assert result == {"encontrado": True, "isbn": "9788532511010"}
    assert calls[0]["messages"][0]["content"][1]["image_url"]["url"].startswith("data:image/jpeg")


def test_groq_vision_returns_empty_when_image_has_no_isbn(monkeypatch):
    _mock_groq_vision(monkeypatch, '{"encontrado": false, "isbn": ""}')

    assert books._groq_isbn_from_image(_vision_frame()) == {"encontrado": False, "isbn": ""}


def test_groq_vision_reports_auth_error(monkeypatch):
    class AuthError(books.OpenAIError):
        def __init__(self, message="Unauthorized", status_code=401):
            self.status_code = status_code
            super().__init__(message)

    class Completion:
        def create(self, **payload):
            raise AuthError("401 Unauthorized")

    client = type("Client", (), {"chat": type("Chat", (), {"completions": Completion()})()})
    monkeypatch.setattr(books, "OpenAI", lambda **kwargs: client())

    with pytest.raises(books._ProviderError, match="GROQ_API_KEY|autoriz"):
        books._groq_isbn_from_image(_vision_frame())


def test_groq_vision_rejects_invalid_isbn(monkeypatch):
    _mock_groq_vision(monkeypatch, '{"encontrado": true, "isbn": "978853251101X"}')

    assert books._groq_isbn_from_image(_vision_frame()) == {"encontrado": False, "isbn": ""}


def test_openai_vision_uses_configured_model_and_normalizes_isbn(monkeypatch):
    calls = []
    client_options = []
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_VISION_MODEL", "test-vision-model")

    class Completion:
        def create(self, **payload):
            calls.append(payload)
            return type("Response", (), {
                "choices": [type("Choice", (), {
                    "message": type("Message", (), {"content": '{"encontrado": true, "isbn": "978-85-3251-101-0"}'})()
                })()]
            })()

    def create_client(**kwargs):
        client_options.append(kwargs)
        return type("Client", (), {"chat": type("Chat", (), {"completions": Completion()})()})()

    monkeypatch.setattr(books, "OpenAI", create_client)

    result = books._openai_isbn_from_image(_vision_frame())

    assert result == {"encontrado": True, "isbn": "9788532511010"}
    assert client_options[0]["api_key"] == "test-key"
    assert "base_url" not in client_options[0]
    assert calls[0]["model"] == "test-vision-model"


def test_vision_endpoint_dispatches_to_selected_provider(monkeypatch):
    calls = []
    monkeypatch.setattr(books, "_openai_isbn_from_image", lambda image: calls.append(image) or {"encontrado": True, "isbn": "9788532511010"})
    monkeypatch.setattr(books, "_lookup_isbn", lambda isbn, use_groq=False: {
        "isbn": isbn, "titulo": "Livro", "autor": "Autora", "categorias": []
    })
    from app import app

    with app.test_client() as client:
        response = client.post("/api/books/isbn-vision", json={"image": _vision_frame(), "provider": "openai"})

    assert response.status_code == 200
    assert calls == [_vision_frame()]
    assert response.get_json()["titulo"] == "Livro"


def test_vision_endpoint_rejects_unknown_provider():
    from app import app

    with app.test_client() as client:
        response = client.post("/api/books/isbn-vision", json={"image": _vision_frame(), "provider": "unknown"})

    assert response.status_code == 400


def test_vision_endpoint_uses_normalized_isbn_without_metadata_groq(monkeypatch):
    calls = []
    monkeypatch.setattr(books, "_groq_isbn_from_image", lambda image: {"encontrado": True, "isbn": "9788532511010"})

    def lookup(isbn, use_groq=False):
        calls.append((isbn, use_groq))
        return {"isbn": isbn, "titulo": "Harry Potter e a Pedra Filosofal", "autor": "J. K. Rowling", "categorias": []}

    monkeypatch.setattr(books, "_lookup_isbn", lookup)
    from app import app

    with app.test_client() as client:
        response = client.post("/api/books/isbn-vision", json={"image": _vision_frame()})

    assert response.status_code == 200
    assert calls == [("9788532511010", False)]
    assert response.get_json()["titulo"] == "Harry Potter e a Pedra Filosofal"


def test_manual_route_does_not_call_groq_vision(monkeypatch):
    from app import app
    monkeypatch.setattr(books, "_groq_isbn_from_image", lambda image: pytest.fail("Vision não deve ser usado no modo manual"))
    complete = {"isbn": "9788532511010", "titulo": "Livro", "autor": "Autor", "categorias": ["History"]}
    monkeypatch.setattr(books, "_google_books_lookup", lambda _isbn: complete)
    monkeypatch.setattr(books, "_isbnsearch_lookup", lambda _isbn: complete)
    monkeypatch.setattr(books, "_openlibrary_lookup", lambda _isbn: complete)
    monkeypatch.setattr(books, "_match_genre", lambda categories: ("", ""))

    with app.test_client() as client:
        response = client.get("/api/books/isbn-lookup?isbn=9788532511010&source=manual")

    assert response.status_code == 200


def test_groq_data_is_preserved_when_verification_sources_find_nothing(monkeypatch):
    groq_result = {
        "isbn": "9788576831303",
        "titulo": "Livro sugerido",
        "autor": "Autora sugerida",
        "categorias": [],
    }
    monkeypatch.setattr(books, "_groq_lookup", lambda _isbn: groq_result)
    not_found = lambda _isbn: (_ for _ in ()).throw(LookupError("não encontrado"))
    monkeypatch.setattr(books, "_google_books_lookup", not_found)
    monkeypatch.setattr(books, "_isbnsearch_lookup", not_found)
    monkeypatch.setattr(books, "_openlibrary_lookup", not_found)
    monkeypatch.setattr(books, "_match_genre", lambda categories: ("", ""))

    result = books._lookup_isbn("9788576831303", use_groq=True)

    assert result["titulo"] == "Livro sugerido"
    assert result["autor"] == "Autora sugerida"
    assert result["categorias"] == []


def test_all_not_found_providers_return_lookup_error(monkeypatch):
    not_found = lambda _isbn: (_ for _ in ()).throw(LookupError("não encontrado"))
    monkeypatch.setattr(books, "_google_books_lookup", not_found)
    monkeypatch.setattr(books, "_isbnsearch_lookup", not_found)
    monkeypatch.setattr(books, "_openlibrary_lookup", not_found)

    with pytest.raises(LookupError):
        books._lookup_isbn("9788576831303")


def test_openlibrary_search_is_used_when_primary_sources_find_nothing(monkeypatch):
    not_found = lambda _isbn: (_ for _ in ()).throw(LookupError("não encontrado"))
    monkeypatch.setattr(books, "_google_books_lookup", not_found)
    monkeypatch.setattr(books, "_isbnsearch_lookup", not_found)
    monkeypatch.setattr(books, "_openlibrary_lookup", not_found)
    monkeypatch.setattr(books, "_openlibrary_search_lookup", lambda _isbn: {
        "isbn": "9788576831303", "titulo": "Diário de um banana", "autor": "Jeff Kinney", "categorias": ["Fiction"]
    })
    monkeypatch.setattr(books, "_match_genre", lambda categories: ("", ""))

    result = books._lookup_isbn("9788576831303")

    assert result["titulo"] == "Diário de um banana"
    assert result["autor"] == "Jeff Kinney"


def test_openlibrary_search_requires_exact_isbn_match(monkeypatch):
    response = io.BytesIO(json.dumps({"docs": [{
        "isbn": ["9780000000002"], "title": "Outro livro", "author_name": ["Outro autor"]
    }]}).encode())
    monkeypatch.setattr(books, "_open_provider", lambda _request, _source: response)

    with pytest.raises(LookupError):
        openlibrary_search_lookup("9788576831303")


def test_openlibrary_search_maps_metadata_for_exact_isbn(monkeypatch):
    response = io.BytesIO(json.dumps({"docs": [{
        "isbn": ["978-85-7683-130-3"], "title": "Diário de um banana",
        "author_name": ["Jeff Kinney"], "subject": ["Fiction"]
    }]}).encode())
    monkeypatch.setattr(books, "_open_provider", lambda _request, _source: response)

    result = openlibrary_search_lookup("9788576831303")

    assert result == {
        "isbn": "9788576831303", "titulo": "Diário de um banana",
        "autor": "Jeff Kinney", "categorias": ["Fiction"]
    }


def test_isbndb_is_used_as_fallback_when_configured(monkeypatch):
    monkeypatch.setenv("ISBNDB_API_KEY", "test-key")
    not_found = lambda _isbn: (_ for _ in ()).throw(LookupError("não encontrado"))
    monkeypatch.setattr(books, "_google_books_lookup", not_found)
    monkeypatch.setattr(books, "_isbnsearch_lookup", not_found)
    monkeypatch.setattr(books, "_openlibrary_lookup", not_found)
    monkeypatch.setattr(books, "_openlibrary_search_lookup", not_found)
    monkeypatch.setattr(books, "_isbndb_lookup", lambda _isbn: {
        "isbn": "9788576831303", "titulo": "Diário de um banana", "autor": "Jeff Kinney", "categorias": []
    })
    monkeypatch.setattr(books, "_match_genre", lambda categories: ("", ""))

    result = books._lookup_isbn("9788576831303")

    assert result["titulo"] == "Diário de um banana"
    assert result["autor"] == "Jeff Kinney"


def test_isbndb_lookup_uses_optional_api_key(monkeypatch):
    monkeypatch.setenv("ISBNDB_API_KEY", "test-key")
    response = io.BytesIO(json.dumps({"book": {
        "title": "Diário de um banana", "authors": ["Jeff Kinney"], "subjects": ["Fiction"]
    }}).encode())
    requests = []

    def open_provider(request, source):
        requests.append((request, source))
        return response

    monkeypatch.setattr(books, "_open_provider", open_provider)

    result = isbndb_lookup("9788576831303")

    assert result["titulo"] == "Diário de um banana"
    assert result["autor"] == "Jeff Kinney"
    assert requests[0][0].get_header("Authorization") == "test-key"
    assert requests[0][1] == "ISBNdb"


def test_route_distinguishes_invalid_and_not_found(monkeypatch):
    from app import app

    app.config.update(TESTING=True)
    def not_found(isbn, use_groq=False):
        books._validate_isbn(books._normalize_isbn(isbn))
        raise LookupError("Livro não encontrado")

    monkeypatch.setattr(books, "_lookup_isbn", not_found)
    with app.test_client() as client:
        not_found = client.get("/api/books/isbn-lookup?isbn=9788576831303")
        invalid = client.get("/api/books/isbn-lookup?isbn=9788576831302")

    assert not_found.status_code == 404
    assert invalid.status_code == 400