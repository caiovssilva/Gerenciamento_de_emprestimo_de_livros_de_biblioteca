"""api/genres.py — CRUD de gêneros com fallback JSON local."""
from flask import Blueprint, request, jsonify
from pathlib import Path
from utils import get_client, sb_exec, new_id
from api._helpers import read_json, write_json, table_ok, is_offline_error

genres_bp  = Blueprint("genres", __name__)
DATA_DIR   = Path(__file__).resolve().parent.parent / "data"
GENR_FILE  = DATA_DIR / "generos.json"
BOOKS_FILE = DATA_DIR / "livros.json"


@genres_bp.route("/", methods=["GET"])
def list_genres():
    sb = get_client()
    if table_ok(sb,"generos"):
        try: genres = sb_exec(sb.table("generos").select("*").order("nome"))
        except: genres = read_json(GENR_FILE)
    else: genres = read_json(GENR_FILE)
    books = read_json(BOOKS_FILE)
    for g in genres:
        try: count = len(sb_exec(sb.table("livros").select("id").eq("genero_id",g["id"])))
        except: count = sum(1 for b in books if b.get("genero_id")==g["id"])
        g["total_livros"] = count
    return jsonify(genres)


@genres_bp.route("/", methods=["POST"])
def create_genre():
    body = request.get_json(force=True) or {}
    if not body.get("nome"): return jsonify({"error":"nome é obrigatório"}),400
    payload = {"id":new_id(),"nome":body["nome"].strip(),"icone":body.get("icone","ti-book"),"cor":body.get("cor","#6366f1")}
    sb = get_client()
    if table_ok(sb,"generos"):
        try: rows=sb_exec(sb.table("generos").insert(payload)); return jsonify(rows[0] if rows else payload),201
        except Exception as e:
            if not is_offline_error(e): raise
    gs=read_json(GENR_FILE); gs.append(payload); write_json(GENR_FILE,gs)
    return jsonify(payload),201


@genres_bp.route("/<genre_id>", methods=["PUT"])
def update_genre(genre_id):
    body = request.get_json(force=True) or {}
    body.pop("id",None); body.pop("criado_em",None)
    sb = get_client()
    if table_ok(sb,"generos"):
        try:
            rows=sb_exec(sb.table("generos").update(body).eq("id",genre_id))
            if not rows: return jsonify({"error":"Gênero não encontrado"}),404
            return jsonify(rows[0])
        except Exception as e:
            if not is_offline_error(e): raise
    gs=read_json(GENR_FILE)
    for g in gs:
        if g.get("id")==genre_id: g.update(body); write_json(GENR_FILE,gs); return jsonify(g)
    return jsonify({"error":"Gênero não encontrado"}),404


@genres_bp.route("/<genre_id>", methods=["DELETE"])
def delete_genre(genre_id):
    sb = get_client()
    try: sb_exec(sb.table("livros").update({"genero_id":None}).eq("genero_id",genre_id))
    except:
        books=read_json(BOOKS_FILE)
        for b in books:
            if b.get("genero_id")==genre_id: b["genero_id"]=None
        write_json(BOOKS_FILE,books)
    if table_ok(sb,"generos"):
        try: sb_exec(sb.table("generos").delete().eq("id",genre_id)); return jsonify({"success":True})
        except: pass
    gs=read_json(GENR_FILE); write_json(GENR_FILE,[g for g in gs if g.get("id")!=genre_id])
    return jsonify({"success":True})