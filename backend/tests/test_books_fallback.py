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
