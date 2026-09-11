"""Cliente central do Supabase; o sistema exige conexão real com o banco."""
import os

_URL  = os.getenv("SUPABASE_URL", "")
_KEY  = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY") or ""

_client = None

_NETWORK_ERROR_TOKENS = (
    "name or service not known",
    "gaierror",
    "connection refused",
    "connection reset",
    "timed out",
    "timeout",
    "temporary failure",
    "network is unreachable",
    "certificate verify failed",
)


def _looks_like_offline_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return any(token in message for token in _NETWORK_ERROR_TOKENS) or isinstance(exc, (ConnectionError, TimeoutError, OSError))


def _normalize_supabase_url(url: str) -> str:
    normalized = (url or "").strip()
    if normalized.endswith("/rest/v1/"):
        normalized = normalized[:-len("/rest/v1/")]
    elif normalized.endswith("/rest/v1"):
        normalized = normalized[:-len("/rest/v1")]
    return normalized.rstrip("/")


def _get_env_config():
    global _URL, _KEY
    _URL = os.getenv("SUPABASE_URL", _URL)
    _KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY") or _KEY
    return _normalize_supabase_url(_URL), _KEY


class SupabaseTable:
    def __init__(self, client, name):
        self.q = client.table(name)
    def select(self, c="*"):          self.q = self.q.select(c);                      return self
    def order(self, f, desc=False):   self.q = self.q.order(f, desc=desc);            return self
    def limit(self, n):               self.q = self.q.limit(n);                       return self
    def eq(self, f, v):               self.q = self.q.eq(f, v);                       return self
    def is_(self, f, v):              self.q = self.q.is_(f, None if v=="null" else v); return self
    def insert(self, p):              self.q = self.q.insert(p);                      return self
    def update(self, p):              self.q = self.q.update(p);                      return self
    def delete(self):                 self.q = self.q.delete();                       return self
    def upsert(self, p, on_conflict=None): self.q = self.q.upsert(p, on_conflict=on_conflict); return self
    def execute(self):
        try:
            r = self.q.execute()
        except Exception as exc:
            if _looks_like_offline_error(exc):
                raise Exception("Supabase indisponível") from exc
            raise
        if hasattr(r, "error") and r.error:
            raise Exception(r.error.message or str(r.error))
        if isinstance(r, dict) and r.get("error"):
            raise Exception(r["error"])
        return getattr(r, "data", r.get("data") if isinstance(r, dict) else r) or []

class SupabaseClient:
    def __init__(self, url, key):
        from supabase import create_client
        self._c = create_client(url, key)
    def table(self, name):
        return SupabaseTable(self._c, name)


def reset_client_state():
    global _client
    _client = None


def get_client():
    global _client

    if _client is not None:
        return _client

    try:
        url, key = _get_env_config()
        if not url or not key:
            raise ValueError("SUPABASE_URL / SUPABASE_KEY não configurados")
        _client = SupabaseClient(url, key)
        print("[supabase] ✅ Conectado com sucesso.")
    except Exception as e:
        print(f"[supabase] ⚠️  Falha: {e} — aguardando conexão real.")
        _client = None
        raise ConnectionError(f"Supabase indisponível: {e}") from e

    return _client


def sb_exec(query):
    r = query.execute()
    if hasattr(r, "error") and r.error:
        raise Exception(r.error.message or str(r.error))
    if isinstance(r, dict) and r.get("error"):
        raise Exception(r["error"])
    return getattr(r, "data", r.get("data") if isinstance(r, dict) else r) or []