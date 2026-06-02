"""
api/rooms.py
CRUD de Salas (turmas organizadas como salas físicas).
Cada sala tem: nome, código, descrição, capacidade.
Alunos são vinculados à sala via campo sala_id em alunos.
"""

from flask import Blueprint, request, jsonify
from utils import get_client, sb_exec, new_id

rooms_bp = Blueprint("rooms", __name__)


@rooms_bp.route("/", methods=["GET"])
def list_rooms():
    sb    = get_client()
    rooms = sb_exec(sb.table("salas").select("*").order("nome"))
    # Enriquece com contagem de alunos
    for r in rooms:
        alunos = sb_exec(sb.table("alunos").select("id").eq("sala_id", r["id"]))
        r["total_alunos"] = len(alunos)
    return jsonify(rooms)


@rooms_bp.route("/<room_id>", methods=["GET"])
def get_room(room_id):
    sb   = get_client()
    rows = sb_exec(sb.table("salas").select("*").eq("id", room_id))
    if not rows:
        return jsonify({"error": "Sala não encontrada"}), 404
    room = rows[0]
    # Alunos da sala
    room["alunos"] = sb_exec(sb.table("alunos").select("*").eq("sala_id", room_id).order("nome"))
    return jsonify(room)


@rooms_bp.route("/", methods=["POST"])
def create_room():
    body = request.get_json(force=True) or {}
    if not body.get("nome"):
        return jsonify({"error": "nome é obrigatório"}), 400

    sb      = get_client()
    payload = {
        "id":         new_id(),
        "nome":       body["nome"].strip(),
        "codigo":     body.get("codigo", "").strip().upper(),
        "descricao":  body.get("descricao", "").strip(),
        "capacidade": int(body.get("capacidade", 40)),
    }
    rows = sb_exec(sb.table("salas").insert(payload))
    return jsonify(rows[0] if rows else payload), 201


@rooms_bp.route("/<room_id>", methods=["PUT"])
def update_room(room_id):
    body = request.get_json(force=True) or {}
    body.pop("id", None); body.pop("criado_em", None)
    sb   = get_client()
    rows = sb_exec(sb.table("salas").update(body).eq("id", room_id))
    if not rows:
        return jsonify({"error": "Sala não encontrada"}), 404
    return jsonify(rows[0])


@rooms_bp.route("/<room_id>", methods=["DELETE"])
def delete_room(room_id):
    sb = get_client()
    # Desvincula alunos antes de excluir
    sb_exec(sb.table("alunos").update({"sala_id": None}).eq("sala_id", room_id))
    sb_exec(sb.table("salas").delete().eq("id", room_id))
    return jsonify({"success": True})
