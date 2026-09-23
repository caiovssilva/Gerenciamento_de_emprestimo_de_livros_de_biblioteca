import importlib
import os
import sys
from pathlib import Path


def test_load_environment_reads_backend_dotenv_from_any_cwd(monkeypatch, tmp_path):
    backend_dir = Path(__file__).resolve().parents[1]
    dotenv_path = backend_dir / ".env"

    if not dotenv_path.exists():
        raise AssertionError("backend/.env not found")

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_KEY", raising=False)

    sys.path.insert(0, str(backend_dir))
    sys.modules.pop("app", None)

    import app as backend_app
    importlib.reload(backend_app)

    assert hasattr(backend_app, "load_environment")
    backend_app.load_environment()
    assert os.getenv("SUPABASE_URL", "").startswith("https://")
