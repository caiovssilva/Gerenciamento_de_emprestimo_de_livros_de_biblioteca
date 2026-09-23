"""api/rooms.py — CRUD de salas com fallback JSON local."""
from flask import Blueprint, request, jsonify
from pathlib import Path
from utils import get_client, sb_exec, new_id
from api._helpers import read_json, write_json, table_ok, is_offline_error

rooms_bp    = Blueprint("rooms", __name__)
DATA_DIR    = Path(__file__).resolve().parent.parent / "data"
ROOMS_FILE  = DATA_DIR / "salas.json"
ALUNOS_FILE = DATA_DIR / "alunos.json"


@rooms_bp.route("/", methods=["GET"])
def list_rooms():
    sb = get_client()
    if table_ok(sb,"salas"):
        try: rooms = sb_exec(sb.table("salas").select("*").order("nome"))
        except: rooms = read_json(ROOMS_FILE)
    else: rooms = read_json(ROOMS_FILE)
    alunos = read_json(ALUNOS_FILE)
    for r in rooms:
        try: count = len(sb_exec(sb.table("alunos").select("id").eq("sala_id",r["id"])))
        except: count = sum(1 for a in alunos if a.get("sala_id")==r["id"])
        r["total_alunos"] = count
    return jsonify(rooms)


@rooms_bp.route("/<room_id>", methods=["GET"])
def get_room(room_id):
    sb = get_client()
    try:    rows = sb_exec(sb.table("salas").select("*").eq("id",room_id))
    except: rows = [r for r in read_json(ROOMS_FILE) if r.get("id")==room_id]
    if not rows: return jsonify({"error":"Sala não encontrada"}),404
    room = rows[0]
    try:    room["alunos"] = sb_exec(sb.table("alunos").select("*").eq("sala_id",room_id).order("nome"))
    except: room["alunos"] = [a for a in read_json(ALUNOS_FILE) if a.get("sala_id")==room_id]
    return jsonify(room)


@rooms_bp.route("/", methods=["POST"])
def create_room():
    body = request.get_json(force=True) or {}
    if not body.get("nome"): return jsonify({"error":"nome é obrigatório"}),400
    try: cap = int(body.get("capacidade",40))
    except: cap = 40
    payload = {"id":new_id(),"nome":body["nome"].strip(),"codigo":body.get("codigo","").strip().upper(),
               "descricao":body.get("descricao","").strip(),"capacidade":cap}
    sb = get_client()
    if table_ok(sb,"salas"):
        try: rows=sb_exec(sb.table("salas").insert(payload)); return jsonify(rows[0] if rows else payload),201
        except Exception as e:
            if not is_offline_error(e): raise
    rs=read_json(ROOMS_FILE); rs.append(payload); write_json(ROOMS_FILE,rs)
    return jsonify(payload),201


@rooms_bp.route("/<room_id>", methods=["PUT"])
def update_room(room_id):
    body = request.get_json(force=True) or {}
    body.pop("id",None); body.pop("criado_em",None)
    sb = get_client()
    if table_ok(sb,"salas"):
        try:
            rows=sb_exec(sb.table("salas").update(body).eq("id",room_id))
            if not rows: return jsonify({"error":"Sala não encontrada"}),404
            return jsonify(rows[0])
        except Exception as e:
            if not is_offline_error(e): raise
    rs=read_json(ROOMS_FILE)
    for r in rs:
        if r.get("id")==room_id: r.update(body); write_json(ROOMS_FILE,rs); return jsonify(r)
    return jsonify({"error":"Sala não encontrada"}),404


@rooms_bp.route("/<room_id>", methods=["DELETE"])
def delete_room(room_id):
    sb = get_client()
    try: sb_exec(sb.table("alunos").update({"sala_id":None}).eq("sala_id",room_id))
    except:
        alunos=read_json(ALUNOS_FILE)
        for a in alunos:
            if a.get("sala_id")==room_id: a["sala_id"]=None
        write_json(ALUNOS_FILE,alunos)
    if table_ok(sb,"salas"):
        try: sb_exec(sb.table("salas").delete().eq("id",room_id)); return jsonify({"success":True})
        except: pass
    rs=read_json(ROOMS_FILE); write_json(ROOMS_FILE,[r for r in rs if r.get("id")!=room_id])
    return jsonify({"success":True})