import os
import sys
from pathlib import Path


def test_load_environment_reads_backend_dotenv_from_any_cwd(monkeypatch, tmp_path):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import app as backend_app

    backend_dir = tmp_path / "backend"
    backend_dir.mkdir()
    dotenv_path = backend_dir / ".env"
    dotenv_path.write_text(
        "SUPABASE_URL=https://dotenv.example.supabase.co\n"
        "SUPABASE_KEY=dotenv-key\n"
        "TEST_DOTENV_FALLBACK=dotenv-value\n"
    )
    monkeypatch.setattr(backend_app, "BACKEND_DIR", backend_dir)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SUPABASE_URL", "https://codespaces.example.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "codespaces-key")
    monkeypatch.setenv("GROQ_API_KEY", "codespaces-groq-secret")
    monkeypatch.delenv("TEST_DOTENV_FALLBACK", raising=False)

    assert hasattr(backend_app, "load_environment")
    assert backend_app.load_environment() == dotenv_path
    assert os.getenv("SUPABASE_URL") == "https://codespaces.example.supabase.co"
    assert os.getenv("SUPABASE_KEY") == "codespaces-key"
    assert os.getenv("GROQ_API_KEY") == "codespaces-groq-secret"
    assert os.getenv("TEST_DOTENV_FALLBACK") == "dotenv-value"
