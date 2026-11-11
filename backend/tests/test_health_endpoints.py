import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import utils
from app import app


def test_health_stays_available_when_database_is_offline(monkeypatch):
    def unavailable_client():
        raise ConnectionError("Supabase indisponível")

    monkeypatch.setattr(utils, "get_client", unavailable_client)

    with app.test_client() as client:
        health = client.get("/api/health")
        readiness = client.get("/api/ready")

    assert health.status_code == 200
    assert health.get_json()["status"] == "ok"
    assert readiness.status_code == 503
    assert readiness.get_json()["database"] == "indisponível"


def test_readiness_returns_success_when_database_is_available(monkeypatch):
    class Query:
        def select(self, *_columns):
            return self

        def limit(self, _count):
            return self

        def execute(self):
            return []

    class Client:
        def table(self, _name):
            return Query()

    monkeypatch.setattr(utils, "get_client", Client)

    with app.test_client() as client:
        readiness = client.get("/api/ready")

    assert readiness.status_code == 200
    assert readiness.get_json()["status"] == "ready"
    assert readiness.get_json()["database"] == "conectado"
