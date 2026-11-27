"""Configurações administrativas de permissões do Autoatendimento."""
from pathlib import Path

from flask import Blueprint, jsonify, request, session

from api._helpers import read_json, write_json

controle_bp = Blueprint("controle", __name__)
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SELF_SERVICE_SETTINGS_FILE = DATA_DIR / "self_service_settings.json"
DEFAULT_RENEWAL_DAYS = 7
PERMISSION_KEYS = ("enabled", "allow_borrow", "allow_return", "allow_renew")
DEFAULT_SETTINGS = {
    "enabled": False,
    "allow_borrow": False,
    "allow_return": False,
    "allow_renew": False,
    "renewal_days": DEFAULT_RENEWAL_DAYS,
}


def get_self_service_settings():
    stored = read_json(SELF_SERVICE_SETTINGS_FILE)
    if not isinstance(stored, dict):
        stored = {}
    settings = {
        key: stored.get(key, DEFAULT_SETTINGS[key]) is True
        for key in PERMISSION_KEYS
    }
    try:
        renewal_days = int(stored.get("renewal_days", DEFAULT_RENEWAL_DAYS))
    except (TypeError, ValueError):
        renewal_days = DEFAULT_RENEWAL_DAYS
    settings["renewal_days"] = min(365, max(1, renewal_days))
    return settings


def self_service_operation_allowed(setting=None):
    settings = get_self_service_settings()
    return settings["enabled"] and (setting is None or settings[setting])


def librarian_operation_allowed(setting):
    return get_self_service_settings()[setting]


@controle_bp.route("/autoatendimento", methods=["GET", "PUT"])
def autoatendimento_settings():
    if request.method == "GET":
        return jsonify(get_self_service_settings()), 200

    if session.get("access_scope") != "staff_admin":
        return jsonify({"error": "Somente um administrador autenticado pode alterar essas configurações."}), 403

    body = request.get_json(force=True) or {}
    if any(key not in body or type(body[key]) is not bool for key in PERMISSION_KEYS):
        return jsonify({"error": "Envie valores booleanos para todas as permissões do Autoatendimento."}), 400

    renewal_days = body.get("renewal_days")
    if type(renewal_days) is not int or not 1 <= renewal_days <= 365:
        return jsonify({"error": "Informe um prazo padrão de renovação entre 1 e 365 dias."}), 400

    settings = {key: body[key] for key in PERMISSION_KEYS}
    settings["renewal_days"] = renewal_days
    if not write_json(SELF_SERVICE_SETTINGS_FILE, settings):
        return jsonify({"error": "Não foi possível salvar as configurações do Autoatendimento."}), 500
    return jsonify(settings), 200
