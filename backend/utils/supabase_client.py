"""
utils/supabase_client.py
Conexão ao Supabase. Se falhar, entra em modo offline — dados dos JSONs locais.
"""
import os

_URL  = os.getenv("SUPABASE_URL", "")
_KEY  = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY") or ""

_client  = None
_offline = False


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
        r = self.q.execute()
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


def get_client():
    global _client, _offline
    if _offline:
        return _OfflineClient()
    if _client is None:
        try:
            if not _URL or not _KEY:
                raise ValueError("SUPABASE_URL / SUPABASE_KEY não configurados")
            _client = SupabaseClient(_URL, _KEY)
            print("[supabase] ✅ Conectado com sucesso.")
        except Exception as e:
            print(f"[supabase] ⚠️  Falha: {e} — usando dados locais (JSON).")
            _offline = True
            return _OfflineClient()
    return _client


def sb_exec(query):
    r = query.execute()
    if hasattr(r, "error") and r.error:
        raise Exception(r.error.message or str(r.error))
    if isinstance(r, dict) and r.get("error"):
        raise Exception(r["error"])
    return getattr(r, "data", r.get("data") if isinstance(r, dict) else r) or []