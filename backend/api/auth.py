"""api/auth.py — Autenticação via tabela usuarios do Supabase."""
from flask import Blueprint, request, jsonify, current_app
import os

# Prefer passlib for portable password verification. Fallback to the system
# `crypt` module if passlib is not available or cannot verify the stored hash.
try:
    from passlib.context import CryptContext
    _pwd_ctx = CryptContext(
        schemes=["bcrypt", "pbkdf2_sha256", "sha512_crypt", "sha256_crypt", "des_crypt"],
        deprecated="auto"
    )
except Exception:
    _pwd_ctx = None

try:
    import crypt as unix_crypt  # type: ignore
except Exception:
    unix_crypt = None

from utils import get_client, sb_exec

auth_bp = Blueprint("auth", __name__)

LOGIN_ALIASES = {
    "bibliotecario": "biblioteca",
    "bibliotecaria": "biblioteca",
}


def _normalize_supabase_url(url: str) -> str:
    normalized = (url or "").strip()
    if normalized.endswith("/rest/v1/"):
        normalized = normalized[:-len("/rest/v1/")]
    elif normalized.endswith("/rest/v1"):
        normalized = normalized[:-len("/rest/v1")]
    return normalized.rstrip("/")
def _verify_password(password: str, stored_hash: str) -> bool:
    """Compara a senha informada com o hash bcrypt/pgcrypto armazenado no banco."""
    if not password or not stored_hash:
        return False
    # If passlib is available, let it identify and verify the scheme.
    try:
        if _pwd_ctx is not None:
            return _pwd_ctx.verify(password, stored_hash)
    except Exception:
        # Verification via passlib failed; fall back to unix crypt if available
        pass

    # If the stored value doesn't look like a hashed string, treat it
    # as a legacy plain-text password (created by earlier DB seeds).
    # Accept equality and let the caller re-hash the password for safety.
    try:
        if isinstance(stored_hash, str) and "$" not in stored_hash:
            return password == stored_hash
    except Exception:
        pass

    if 'unix_crypt' in globals() and unix_crypt is not None:
        try:
            return unix_crypt.crypt(password, stored_hash) == stored_hash
        except Exception:
            return False

    return False


def _get_user_by_login(login_str: str):
    sb = get_client()
    canonical_login = LOGIN_ALIASES.get((login_str or "").strip().lower(), login_str)
    # Try exact match first (fast). If no result, fallback to reading
    # all users and matching case-insensitively to tolerate different
    # capitalization in the stored `login` values.
    try:
        rows = sb_exec(
            sb.table("usuarios")
            .select("id,nome,login,senha")
            .eq("login", canonical_login)
        )
    except Exception:
        rows = []

    if rows:
        return rows[0]

    # Fallback: try case-insensitive match by fetching all users (small table).
    try:
        all_rows = sb_exec(sb.table("usuarios").select("id,nome,login,senha"))
        if all_rows:
            for r in all_rows:
                if (r.get("login") or "").strip().lower() == (canonical_login or "").strip().lower():
                    return r
    except Exception:
        pass

    return None


# ── Endpoint: Login ──────────────────────────────────────────────────
@auth_bp.route("/login", methods=["POST"])
def login():
    """
    POST /api/auth/login
    Body: { "login": "admin", "password": "narceu2026" }
    
    Response:
    {
      "access": "admin",
      "login": "admin",
      "name": "Administrador",
      "id": "usr_admin"
    }
    """
    body = request.get_json(force=True) or {}
    login_str = (body.get("login") or "").strip().lower()
    password = (body.get("password") or "").strip()
    
    if not login_str or not password:
        return jsonify({"error": "Login e senha são obrigatórios"}), 400
    
    try:
        user = _get_user_by_login(login_str)

        auth_debug = os.getenv("AUTH_DEBUG", "").lower() in ("1","true","yes")

        if not user:
            if auth_debug:
                current_app.logger.info(f"Login falhou: usuário '{login_str}' não encontrado")
            else:
                current_app.logger.warning(f"Falha de login para '{login_str}'")
            return jsonify({"error": "Usuário ou senha incorretos"}), 401

        if not _verify_password(password, user.get("senha", "")):
            if auth_debug:
                current_app.logger.info(f"Login falhou para '{login_str}': senha inválida. Stored hash startswith: '{(user.get('senha') or '')[:10]}'")
            else:
                current_app.logger.warning(f"Falha de login para '{login_str}'")
            return jsonify({"error": "Usuário ou senha incorretos"}), 401
        # If login succeeded but the stored senha looks like plain-text,
        # re-hash it using passlib and update the Supabase record to a
        # secure scheme. This makes future verifications reliable.
        stored = user.get("senha") or ""
        try:
            looks_hashed = isinstance(stored, str) and "$" in stored
            if _pwd_ctx is not None and not looks_hashed:
                try:
                    new_hash = _pwd_ctx.hash(password)
                    sb = get_client()
                    # update the user's senha in the DB; ignore errors
                    try:
                        sb_exec(sb.table("usuarios").update({"senha": new_hash}).eq("id", user["id"]))
                        if auth_debug:
                            current_app.logger.info(f"Rehashed senha para usuário '{login_str}' (id={user.get('id')})")
                    except Exception:
                        if auth_debug:
                            current_app.logger.warning(f"Falha ao atualizar hash da senha para '{login_str}'")
                except Exception:
                    # If hashing fails, continue without blocking login.
                    if auth_debug:
                        current_app.logger.info(f"Não foi possível re-hash da senha para '{login_str}'")
        except Exception:
            pass

        normalized_login = (user["login"] or "").strip().lower()
        access = "librarian" if normalized_login in ("bibliotecario", "biblioteca") else "admin"
        return jsonify({
            "access": access,
            "id": user["id"],
            "login": user["login"],
            "name": user.get("nome") or user.get("name")
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Erro ao fazer login: {e}")
        return jsonify({"error": "Erro ao processar login"}), 500


# ── Endpoint: Configuração Supabase Segura ──────────────────────────
@auth_bp.route("/config/supabase", methods=["GET"])
def get_supabase_config():
    """
    GET /api/auth/config/supabase
    
    Retorna as credenciais do Supabase de forma segura.
    Isso é melhor que hardcoded no frontend porque:
    1. Credenciais não ficam expostas no código cliente
    2. Podem ser rotacionadas sem deploiar frontend
    3. Podem ser diferentes por ambiente
    """
    try:
        url = _normalize_supabase_url(os.getenv("SUPABASE_URL", ""))
        key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_KEY") or ""
        
        if not url or not key:
            current_app.logger.info("Supabase não configurado: usando fallback local")
            return jsonify({"url": "", "key": ""}), 200
        
        return jsonify({"url": url, "key": key}), 200
    
    except Exception as e:
        current_app.logger.error(f"Erro ao carregar config Supabase: {e}")
        return jsonify({"error": "Erro ao carregar configuração", "url": "", "key": ""}), 200


@auth_bp.route("/supabase-config", methods=["GET"])
def get_supabase_config_compat():
    """Compatibilidade com frontends antigos.

    Suporta:
      /api/auth/config/supabase
      /api/config/supabase
      /api/auth/supabase-config
      /api/supabase-config
    """
    return get_supabase_config()
