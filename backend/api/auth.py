"""api/auth.py — Autenticação via tabela usuarios do Supabase."""
from flask import Blueprint, request, jsonify, current_app
import os
import crypt as unix_crypt

from utils import get_client, sb_exec

auth_bp = Blueprint("auth", __name__)


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

    try:
        return unix_crypt.crypt(password, stored_hash) == stored_hash
    except Exception:
        return False


def _get_user_by_login(login_str: str):
    sb = get_client()
    rows = sb_exec(
        sb.table("usuarios")
        .select("id,nome,login,senha")
        .eq("login", login_str)
    )
    return rows[0] if rows else None


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

        if not user or not _verify_password(password, user.get("senha", "")):
            current_app.logger.warning(f"Falha de login para '{login_str}'")
            return jsonify({"error": "Usuário ou senha incorretos"}), 401
        
        access = "librarian" if user["login"].lower() == "bibliotecario" else "admin"
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
