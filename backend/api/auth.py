"""api/auth.py — Autenticação segura com hash de senhas."""
from flask import Blueprint, request, jsonify, current_app
import os
import hashlib
import secrets
from functools import wraps

auth_bp = Blueprint("auth", __name__)


# ── Configuração de usuários com hash (bcrypt não disponível, usando SHA-256 + salt) ──
def hash_password(password: str, salt: str = None) -> tuple:
    """
    Hash seguro de senha usando SHA-256 com salt.
    Retorna (hashed_password, salt)
    """
    if salt is None:
        salt = secrets.token_hex(16)  # 32 caracteres aleatórios
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return hashed, salt


def verify_password(password: str, hashed: str, salt: str) -> bool:
    """Verifica se a senha corresponde ao hash armazenado."""
    computed_hash, _ = hash_password(password, salt)
    return computed_hash == hashed


# ── Credenciais padrão (devem ser substituídas via .env em produção) ──
def get_default_users():
    """
    Retorna lista de usuários com credenciais hash.
    Em produção, isso deve vir de um banco de dados seguro.
    """
    # Hashes pré-computados de "ifes2024"
    # Para regenerar: hash_password("ifes2024")
    admin_hash = "6a7a47a7cb82a78947fc8917f982f076433f26d2399524df5455b7804142364f"
    admin_salt = "100c3c34b730606bd01adf1960aa9ffe"
    
    return [
        {
            "id": "usr_admin",
            "login": "admin",
            "name": "Administrador",
            "password_hash": admin_hash,
            "salt": admin_salt,
        },
        {
            "id": "usr_biblioteca",
            "login": "biblioteca",
            "name": "Bibliotecária",
            "password_hash": admin_hash,
            "salt": admin_salt,
        }
    ]


# ── Endpoint: Login ──────────────────────────────────────────────────
@auth_bp.route("/login", methods=["POST"])
def login():
    """
    POST /api/auth/login
    Body: { "login": "admin", "password": "ifes2024" }
    
    Response:
    {
      "access": "admin",
      "login": "admin",
      "name": "Administrador",
      "id": "usr_admin"
    }
    """
    body = request.get_json(force=True) or {}
    login_str = (body.get("login") or "").strip()
    password = body.get("password") or ""
    
    if not login_str or not password:
        return jsonify({"error": "Login e senha são obrigatórios"}), 400
    
    try:
        users = get_default_users()
        user = next((u for u in users if u["login"] == login_str), None)
        
        if not user or not verify_password(password, user["password_hash"], user["salt"]):
            return jsonify({"error": "Credenciais inválidas"}), 401
        
        return jsonify({
            "access": "admin",
            "id": user["id"],
            "login": user["login"],
            "name": user["name"]
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
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_KEY", "")
        
        if not url or not key:
            current_app.logger.warning("Credenciais Supabase não configuradas")
            return jsonify({"error": "Configuração Supabase não disponível"}), 503
        
        return jsonify({"url": url, "key": key}), 200
    
    except Exception as e:
        current_app.logger.error(f"Erro ao carregar config Supabase: {e}")
        return jsonify({"error": "Erro ao carregar configuração"}), 500


@auth_bp.route("/supabase-config", methods=["GET"])
def get_supabase_config_compat():
    """Compatibilidade com frontends antigos que chamam /api/config/supabase."""
    return get_supabase_config()
