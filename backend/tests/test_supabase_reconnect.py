import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import backend.utils.supabase_client as sb


def test_get_client_retries_after_60_seconds(monkeypatch):
    monkeypatch.setattr(sb, "_URL", "https://example.supabase.co")
    monkeypatch.setattr(sb, "_KEY", "example-key")
    monkeypatch.setattr(sb, "_client", None)
    monkeypatch.setattr(sb, "_offline", True)
    monkeypatch.setattr(sb, "_last_attempt", 0)

    class FailingClient:
        def __init__(self, url, key):
            raise ConnectionError("simulated startup failure")

    class SuccessfulClient:
        def __init__(self, url, key):
            self.url = url
            self.key = key
        def table(self, name):
            return sb._OfflineQuery()

    monkeypatch.setattr(sb, "SupabaseClient", FailingClient)
    client = sb.get_client()
    assert isinstance(client, sb._OfflineClient)

    # Subsequent calls before 60s should not retry
    last_attempt = sb._last_attempt
    client2 = sb.get_client()
    assert isinstance(client2, sb._OfflineClient)
    assert sb._last_attempt == last_attempt

    # After 60 seconds, should try to reconnect again
    monkeypatch.setattr(sb, "_last_attempt", last_attempt - 61)
    monkeypatch.setattr(sb, "SupabaseClient", SuccessfulClient)
    client3 = sb.get_client()
    assert isinstance(client3, SuccessfulClient)
    assert sb._offline is False


def test_get_client_returns_cached_connection_when_online(monkeypatch):
    monkeypatch.setattr(sb, "_URL", "https://example.supabase.co")
    monkeypatch.setattr(sb, "_KEY", "example-key")
    monkeypatch.setattr(sb, "_client", None)
    monkeypatch.setattr(sb, "_offline", False)
    monkeypatch.setattr(sb, "_last_attempt", 0)

    class SuccessfulClient:
        def __init__(self, url, key):
            self.url = url
            self.key = key
        def table(self, name):
            return sb._OfflineQuery()

    monkeypatch.setattr(sb, "SupabaseClient", SuccessfulClient)
    client = sb.get_client()
    client2 = sb.get_client()

    assert client is client2
    assert isinstance(client, SuccessfulClient)
