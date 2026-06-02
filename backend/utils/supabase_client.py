"""
utils/supabase_client.py
Cliente Supabase — supabase-py v2.
Credenciais lidas do .env com fallback hardcoded.
"""

import os
from supabase import create_client, Client

# Credenciais do projeto IFES Aracruz
_SUPABASE_URL = "https://jwncagbmqipbzoeldlet.supabase.co"
_SUPABASE_KEY = "sb_publishable_erfwnkHOevFoIX1pHN-9-g_i8xcqPkX"

_client: Client | None = None


def get_client() -> Client:
    """Retorna o singleton do cliente Supabase."""
    global _client
    if _client is None:
        url = os.getenv("SUPABASE_URL", _SUPABASE_URL)
        key = os.getenv("SUPABASE_KEY", _SUPABASE_KEY)
        _client = create_client(url, key)
    return _client


def sb_exec(query):
    """
    Executa uma query Supabase e retorna a lista de resultados.
    Compatível com supabase-py v2 (response.data).
    """
    try:
        response = query.execute()
        return response.data or []
    except Exception as e:
        print(f"[Supabase] Erro na query: {e}")
        return []
