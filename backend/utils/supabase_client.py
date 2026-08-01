"""
utils/supabase_client.py
Conexão ao Supabase. Se falhar, entra em modo offline — dados dos JSONs locais.
"""
import os
import time

_URL  = os.getenv("SUPABASE_URL", "")
_KEY  = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY") or ""

_client      = None
_offline     = False
_last_attempt = 0
_retry_after_seconds = 60

_NETWORK_ERROR_TOKENS = (
    "name or service not known",
    "gaierror",
    "connection refused",
    "connection reset",
    "timed out",
    "timeout",
    "temporary failure",
    "network is unreachable",
    "offline mode",
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


class _OfflineQuery:
    """Stub que imita a interface do supabase-py mas sempre levanta exceção controlada."""
    def select(self, *a, **kw): return self
    def order(self, *a, **kw):  return self
    def limit(self, *a, **kw):  return self
    def eq(self, *a, **kw):     return self
    def is_(self, *a, **kw):    return self
    def insert(self, *a, **kw): return self
    def update(self, *a, **kw): return self
    def delete(self, *a, **kw): return self
    def upsert(self, *a, **kw): return self
    def execute(self):
        raise Exception("could not find the table — offline mode")

class _OfflineClient:
    def table(self, _): return _OfflineQuery()


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
                raise Exception("could not find the table — offline mode") from exc
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


def _now_seconds():
    return int(time.time())


def reset_client_state():
    global _client, _offline, _last_attempt
    _client = None
    _offline = False
    _last_attempt = 0


def get_client():
    global _client, _offline, _last_attempt

    if _client is not None and not _offline:
        return _client

    if _offline:
        now = _now_seconds()
        if now - _last_attempt < _retry_after_seconds:
            return _OfflineClient()

    _last_attempt = _now_seconds()
    try:
        url, key = _get_env_config()
        if not url or not key:
            raise ValueError("SUPABASE_URL / SUPABASE_KEY não configurados")
        _client = SupabaseClient(url, key)
        _offline = False
        print("[supabase] ✅ Conectado com sucesso.")
    except Exception as e:
        print(f"[supabase] ⚠️  Falha: {e} — usando dados locais (JSON).")
        _offline = True
        _client = None
        return _OfflineClient()

    return _client


def sb_exec(query):
    r = query.execute()
    if hasattr(r, "error") and r.error:
        raise Exception(r.error.message or str(r.error))
    if isinstance(r, dict) and r.get("error"):
        raise Exception(r["error"])
    return getattr(r, "data", r.get("data") if isinstance(r, dict) else r) or []