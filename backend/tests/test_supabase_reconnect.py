import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import utils.supabase_client as sb


def test_get_client_retries_after_connection_failure(monkeypatch):
    monkeypatch.setattr(sb, "_URL", "https://example.supabase.co")
    monkeypatch.setattr(sb, "_KEY", "example-key")
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "example-key")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "example-service-key")
    monkeypatch.setattr(sb, "_client", None)

    class FailingClient:
        def __init__(self, _url, _key):
            raise ConnectionError("simulated startup failure")

    class SuccessfulClient:
        def __init__(self, url, key):
            self.url = url
            self.key = key

    monkeypatch.setattr(sb, "SupabaseClient", FailingClient)
    with pytest.raises(ConnectionError, match="Supabase indisponível"):
        sb.get_client()
    assert sb._client is None

    monkeypatch.setattr(sb, "SupabaseClient", SuccessfulClient)
    client = sb.get_client()
    assert isinstance(client, SuccessfulClient)
    assert client.url == "https://example.supabase.co"
    assert client.key == "example-service-key"


def test_get_client_returns_cached_connection_when_online(monkeypatch):
    monkeypatch.setattr(sb, "_URL", "https://example.supabase.co")
    monkeypatch.setattr(sb, "_KEY", "example-key")
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "example-key")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "example-service-key")
    monkeypatch.setattr(sb, "_client", None)

    class SuccessfulClient:
        def __init__(self, url, key):
            self.url = url
            self.key = key

    monkeypatch.setattr(sb, "SupabaseClient", SuccessfulClient)
    client = sb.get_client()
    client2 = sb.get_client()

    assert client is client2
    assert isinstance(client, SuccessfulClient)


@pytest.mark.parametrize("method", ["GET", "HEAD"])
def test_table_retries_transient_read_disconnections(monkeypatch, method):
    class Request:
        http_method = method

    class Response:
        data = [{"id": "book-1"}]

    class Query:
        request = Request()

        def __init__(self):
            self.attempts = 0

        def execute(self):
            self.attempts += 1
            if self.attempts == 1:
                raise ConnectionError("Server disconnected")
            return Response()

    class Client:
        def __init__(self):
            self.query = Query()

        def table(self, _name):
            return self.query

    monkeypatch.setattr(sb.time, "sleep", lambda _delay: None)
    client = Client()
    result = sb.SupabaseTable(client, "livros").execute()

    assert result == [{"id": "book-1"}]
    assert client.query.attempts == 2


def test_table_does_not_retry_transient_write_disconnections(monkeypatch):
    class Request:
        http_method = "POST"

    class Query:
        request = Request()

        def __init__(self):
            self.attempts = 0

        def execute(self):
            self.attempts += 1
            raise ConnectionError("Server disconnected")

    class Client:
        def __init__(self):
            self.query = Query()

        def table(self, _name):
            return self.query

    client = Client()
    with pytest.raises(Exception, match="Supabase indisponível"):
        sb.SupabaseTable(client, "emprestimos").execute()

    assert client.query.attempts == 1
