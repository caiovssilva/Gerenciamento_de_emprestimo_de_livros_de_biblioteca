"""
api/genres.py
CRUD de Gêneros/Tipos de livro (ex: Comédia, Ficção, Técnico...).
Livros têm campo genero_id.
"""

from flask import Blueprint, request, jsonify
from utils import get_client, sb_exec, new_id

genres_bp = Blueprint("genres", __name__)


@genres_bp.route("/", methods=["GET"])
def list_genres():
    sb     = get_client()
    genres = sb_exec(sb.table("generos").select("*").order("nome"))
    for g in genres:
        livros = sb_exec(sb.table("livros").select("id").eq("genero_id", g["id"]))
        g["total_livros"] = len(livros)
    return jsonify(genres)


@genres_bp.route("/", methods=["POST"])
def create_genre():
    body = request.get_json(force=True) or {}
    if not body.get("nome"):
        return jsonify({"error": "nome é obrigatório"}), 400

    sb      = get_client()
    payload = {
        "id":    new_id(),
        "nome":  body["nome"].strip(),
        "icone": body.get("icone", "ti-book").strip(),
        "cor":   body.get("cor", "#6366f1").strip(),
    }
    rows = sb_exec(sb.table("generos").insert(payload))
    return jsonify(rows[0] if rows else payload), 201


@genres_bp.route("/<genre_id>", methods=["PUT"])
def update_genre(genre_id):
    body = request.get_json(force=True) or {}
    body.pop("id", None); body.pop("criado_em", None)
    sb   = get_client()
    rows = sb_exec(sb.table("generos").update(body).eq("id", genre_id))
    if not rows:
        return jsonify({"error": "Gênero não encontrado"}), 404
    return jsonify(rows[0])


@genres_bp.route("/<genre_id>", methods=["DELETE"])
def delete_genre(genre_id):
    sb = get_client()
    # Remove vínculo dos livros
    sb_exec(sb.table("livros").update({"genero_id": None}).eq("genero_id", genre_id))
    sb_exec(sb.table("generos").delete().eq("id", genre_id))
    return jsonify({"success": True})
