"""
api/books.py
CRUD de livros com suporte a genero_id e geração de QR automático.
"""

from flask import Blueprint, request, jsonify
from utils import get_client, sb_exec, new_id

books_bp = Blueprint("books", __name__)


@books_bp.route("/", methods=["GET"])
def list_books():
    sb     = get_client()
    q      = request.args.get("q", "").strip().lower()
    genre  = request.args.get("genre", "").strip()

    books = sb_exec(sb.table("livros").select("*, generos(nome, cor, icone)").order("titulo"))

    if q:
        books = [
            b for b in books
            if q in (b.get("titulo") or "").lower()
            or q in (b.get("autor") or "").lower()
            or q in (b.get("isbn") or "").lower()
            or q in (b.get("id") or "").lower()
        ]
    if genre:
        books = [b for b in books if b.get("genero_id") == genre]

    # Flatten genero info
    for b in books:
        gen = b.pop("generos", None) or {}
        b["genero_nome"] = gen.get("nome", "")
        b["genero_cor"]  = gen.get("cor", "")
        b["genero_icone"]= gen.get("icone", "")

    return jsonify(books)


@books_bp.route("/<book_id>", methods=["GET"])
def get_book(book_id):
    sb   = get_client()
    rows = sb_exec(sb.table("livros").select("*, generos(nome, cor, icone)").eq("id", book_id))
    if not rows:
        rows = sb_exec(sb.table("livros").select("*, generos(nome, cor, icone)").eq("isbn", book_id))
    if not rows:
        return jsonify({"error": "Livro não encontrado"}), 404
    b   = rows[0]
    gen = b.pop("generos", None) or {}
    b["genero_nome"] = gen.get("nome", "")
    b["genero_cor"]  = gen.get("cor", "")
    b["genero_icone"]= gen.get("icone", "")
    return jsonify(b)


@books_bp.route("/", methods=["POST"])
def create_book():
    body = request.get_json(force=True) or {}
    if not body.get("titulo") or not body.get("autor"):
        return jsonify({"error": "titulo e autor são obrigatórios"}), 400

    sb      = get_client()
    book_id = new_id()
    payload = {
        "id":         book_id,
        "isbn":       body.get("isbn", "") or "",
        "titulo":     body["titulo"].strip(),
        "autor":      body["autor"].strip(),
        "area":       body.get("area", "Geral"),
        "genero_id":  body.get("genero_id") or None,
        "exemplares": max(1, int(body.get("exemplares", 1))),
    }

    rows = sb_exec(sb.table("livros").insert(payload))
    result = rows[0] if rows else payload

    # Gera QR Code e retorna junto
    try:
        import qrcode as qr_lib
        import base64
        from io import BytesIO
        qr = qr_lib.QRCode(version=1, box_size=6, border=2)
        qr.add_data(book_id)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#1a4f8a", back_color="white")
        buf = BytesIO()
        img.save(buf, format="PNG")
        result["qr_code"] = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception:
        result["qr_code"] = None

    return jsonify(result), 201


@books_bp.route("/<book_id>", methods=["PUT"])
def update_book(book_id):
    body = request.get_json(force=True) or {}
    body.pop("id", None); body.pop("criado_em", None)
    body.pop("generos", None); body.pop("genero_nome", None)
    body.pop("genero_cor", None); body.pop("genero_icone", None)

    sb   = get_client()
    rows = sb_exec(sb.table("livros").update(body).eq("id", book_id))
    if not rows:
        return jsonify({"error": "Livro não encontrado"}), 404
    return jsonify(rows[0])


@books_bp.route("/<book_id>", methods=["DELETE"])
def delete_book(book_id):
    sb     = get_client()
    ativos = sb_exec(
        sb.table("emprestimos").select("id")
          .eq("livro_id", book_id)
          .is_("devolvido_em", "null")
    )
    if ativos:
        return jsonify({"error": "Livro possui empréstimos ativos."}), 409
    sb_exec(sb.table("livros").delete().eq("id", book_id))
    return jsonify({"success": True})
