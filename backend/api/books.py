"""api/books.py — CRUD de livros com fallback JSON local."""
import json
import os
import re
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import Blueprint, request, jsonify
from pathlib import Path
from utils import get_client, sb_exec, new_id, today_str
from api._helpers import read_json, write_json, table_ok, has_deleted_at, is_offline_error

books_bp   = Blueprint("books", __name__)
DATA_DIR   = Path(__file__).resolve().parent.parent / "data"
BOOKS_FILE = DATA_DIR / "livros.json"
GENR_FILE  = DATA_DIR / "generos.json"
LOAN_FILE  = DATA_DIR / "emprestimos.json"
_ISBN_CACHE: dict[str, dict] = {}


def _normalize_isbn(value: str) -> str:
    return re.sub(r"[^0-9Xx]", "", str(value or "")).upper()


def _google_books_lookup(isbn: str) -> dict:
    normalized = _normalize_isbn(isbn)
    if len(normalized) not in (10, 13):
        raise ValueError("Informe um ISBN válido de 10 ou 13 dígitos.")

    api_key = os.getenv("KEY=AIzaSyAEFXrb_Ces2HQsEjOhoyi2jOyBbk-WXCQ", "").strip()
    url = "https://www.googleapis.com/books/v1/volumes?q=isbn:" + normalized
    if api_key:
        url += "&key=" + api_key
    try:
        request_obj = Request(url, headers={"Accept": "application/json"})
        with urlopen(request_obj, timeout=6) as response:
            data = json.load(response)
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError("Não foi possível consultar a Google Books agora.") from exc

    item = (data.get("items") or [None])[0]
    if not item:
        raise LookupError("Livro não encontrado para este ISBN.")

    info = item.get("volumeInfo") or {}
    identifiers = info.get("industryIdentifiers") or []
    found_isbn = normalized
    for identifier in identifiers:
        if identifier.get("type") == "ISBN_13":
            found_isbn = _normalize_isbn(identifier.get("identifier"))
            break
    else:
        for identifier in identifiers:
            if identifier.get("type") == "ISBN_10":
                found_isbn = _normalize_isbn(identifier.get("identifier"))
                break

    return {
        "isbn": found_isbn,
        "titulo": str(info.get("title") or "").strip(),
        "autor": ", ".join(str(author).strip() for author in (info.get("authors") or []) if str(author).strip()),
        "categorias": [str(category).strip() for category in (info.get("categories") or []) if str(category).strip()],
    }


class _IsbnSearchParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.authors = ""
        self._in_title = False
        self._in_authors = False
        self._capture_authors = False

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self._in_title = True
        if tag == "p":
            self._capture_authors = False

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag == "p":
            self._in_authors = False
            self._capture_authors = False

    def handle_data(self, data):
        text = " ".join(data.split())
        if self._in_title:
            self.title += text
        if self._capture_authors:
            self.authors += text
        if text.lower().startswith("authors:"):
            self._capture_authors = True
            self._in_authors = True
            self.authors += text.split(":", 1)[1].strip()


def _isbnsearch_lookup(isbn: str) -> dict:
    normalized = _normalize_isbn(isbn)
    url = "https://isbnsearch.org/isbn/" + normalized
    request_obj = Request(url, headers={"Accept": "text/html", "User-Agent": "Mozilla/5.0"})
    try:
        with urlopen(request_obj, timeout=6) as response:
            parser = _IsbnSearchParser()
            parser.feed(response.read().decode("utf-8", errors="replace"))
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError("Não foi possível consultar fontes de ISBN agora.") from exc

    title = re.sub(r"^ISBN\s+\S+\s*-\s*", "", parser.title, flags=re.IGNORECASE).strip()
    authors = re.sub(r"\s*[-|].*$", "", parser.authors).strip()
    if not title or title.upper().startswith("ISBN "):
        raise LookupError("Livro não encontrado para este ISBN.")

    return {"isbn": normalized, "titulo": title, "autor": authors, "categorias": []}


def _openlibrary_lookup(isbn: str) -> dict:
    normalized = _normalize_isbn(isbn)
    url = "https://openlibrary.org/api/books?bibkeys=ISBN:" + normalized + "&jscmd=data&format=json"
    request_obj = Request(url, headers={"Accept": "application/json", "User-Agent": "Biblioteca/1.0"})
    try:
        with urlopen(request_obj, timeout=6) as response:
            data = json.load(response)
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError("Não foi possível consultar fontes de ISBN agora.") from exc

    book = data.get("ISBN:" + normalized) or {}
    authors = []
    for author in book.get("authors") or []:
        name = author.get("name") if isinstance(author, dict) else author
        if str(name or "").strip():
            authors.append(str(name).strip())

    categories = []
    for subject in book.get("subjects") or []:
        name = subject.get("name") if isinstance(subject, dict) else subject
        if str(name or "").strip():
            categories.append(str(name).strip())

    author_text = ", ".join(authors)
    title = str(book.get("title") or "").strip()
    if not title and not author_text and not categories:
        raise LookupError("Livro não encontrado para este ISBN.")
    return {"isbn": normalized, "titulo": title, "autor": author_text, "categorias": categories}


def _lookup_isbn(isbn: str) -> dict:
    normalized = _normalize_isbn(isbn)
    if len(normalized) not in (10, 13):
        raise ValueError("Informe um ISBN válido de 10 ou 13 dígitos.")
    if normalized in _ISBN_CACHE:
        return _ISBN_CACHE[normalized].copy()

    errors = []
    result = None
    for provider in (_google_books_lookup, _isbnsearch_lookup, _openlibrary_lookup):
        try:
            found = provider(normalized)
            if result is None:
                result = found
            else:
                result["titulo"] = result.get("titulo") or found.get("titulo", "")
                result["autor"] = result.get("autor") or found.get("autor", "")
                categories = result.get("categorias") or []
                for category in found.get("categorias") or []:
                    if category not in categories:
                        categories.append(category)
                result["categorias"] = categories
            if result.get("titulo") and result.get("autor") and result.get("categorias"):
                break
        except (HTTPError, URLError, TimeoutError, LookupError, RuntimeError) as exc:
            errors.append(exc)

    if result is not None:
        _ISBN_CACHE[normalized] = result
        return result.copy()
    raise RuntimeError("Não foi possível consultar fontes de ISBN agora.") from errors[-1]


def _build_exemplar_meta(book_id: str, total: int) -> list[dict]:
    copies = []
    for idx in range(max(1, int(total))):
        code = str(idx + 1).zfill(3)
        exemplar_id = f"{book_id}-EX-{code}-{new_id()}"
        copies.append({
            "id": exemplar_id,
            "code": code,
            "qr_data": f"EXEMPLAR-{exemplar_id}",
        })
    return copies


@books_bp.route("/", methods=["GET"])
def list_books():
    q     = request.args.get("q", "").strip().lower()
    genre = request.args.get("genre", "").strip()

    try:
        sb = get_client()
        if table_ok(sb, "livros"):
            try:
                books = sb_exec(sb.table("livros").select("*, generos(nome,cor,icone)").order("titulo"))
            except Exception:
                books = sb_exec(sb.table("livros").select("*").order("titulo"))
        else:
            books = read_json(BOOKS_FILE)
    except Exception:
        books = read_json(BOOKS_FILE)

    if q:
        books = [b for b in books if q in (b.get("titulo","")).lower() or
                 q in (b.get("autor","")).lower() or q in (b.get("isbn","")).lower()]
    if genre:
        books = [b for b in books if b.get("genero_id") == genre]

    gmap = {g["id"]: g for g in read_json(GENR_FILE)}
    for b in books:
        g = b.pop("generos", None) or gmap.get(b.get("genero_id"), {})
        b["genero_nome"] = g.get("nome",""); b["genero_cor"] = g.get("cor",""); b["genero_icone"] = g.get("icone","")
    return jsonify(books)


@books_bp.route("/isbn-lookup", methods=["GET"])
def lookup_isbn():
    isbn = request.args.get("isbn", "")
    try:
        return jsonify(_lookup_isbn(isbn))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except LookupError as exc:
        return jsonify({"error": str(exc)}), 404
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 502


@books_bp.route("/<book_id>", methods=["GET"])
def get_book(book_id):
    sb = get_client()
    try:
        rows = sb_exec(sb.table("livros").select("*, generos(nome,cor,icone)").eq("id", book_id))
        if not rows: rows = sb_exec(sb.table("livros").select("*, generos(nome,cor,icone)").eq("isbn", book_id))
        if not rows: rows = sb_exec(sb.table("livros").select("*, generos(nome,cor,icone)").contains("exemplares_ids", [book_id]))
    except:
        all_b = read_json(BOOKS_FILE)
        rows  = [b for b in all_b if b.get("id")==book_id or b.get("isbn")==book_id or book_id in (b.get("exemplares_ids") or [])]
    if not rows: return jsonify({"error": "Livro não encontrado"}), 404
    b = rows[0]; g = b.pop("generos", None) or {}
    b["genero_nome"] = g.get("nome",""); b["genero_cor"] = g.get("cor",""); b["genero_icone"] = g.get("icone","")
    return jsonify(b)


@books_bp.route("/", methods=["POST"])
def create_book():
    body = request.get_json(force=True) or {}
    if not body.get("titulo") or not body.get("autor"):
        return jsonify({"error": "titulo e autor são obrigatórios"}), 400
    sb = get_client()
    try: copies = max(1, int(body.get("exemplares", 1)))
    except: copies = 1
    book_id = new_id()
    payload = {"id": book_id, "isbn": body.get("isbn",""), "titulo": body["titulo"].strip(),
               "autor": body["autor"].strip(), "area": body.get("area","Geral"), "exemplares": copies}
    exemplar_meta = _build_exemplar_meta(book_id, copies)
    payload["exemplares_ids"] = [item["id"] for item in exemplar_meta]
    payload["exemplares_meta"] = exemplar_meta
    gid = body.get("genero_id") or None
    if gid:
        try:
            if sb_exec(sb.table("generos").select("id").eq("id", gid)): payload["genero_id"] = gid
        except:
            if any(g.get("id")==gid for g in read_json(GENR_FILE)): payload["genero_id"] = gid

    if table_ok(sb, "livros"):
        try: rows = sb_exec(sb.table("livros").insert(payload))
        except Exception as e:
            if "genero_id" in str(e): payload.pop("genero_id",None); rows = sb_exec(sb.table("livros").insert(payload))
            elif is_offline_error(e): books=read_json(BOOKS_FILE); books.append(payload); write_json(BOOKS_FILE,books); rows=[payload]
            else: raise
    else:
        books=read_json(BOOKS_FILE); books.append(payload); write_json(BOOKS_FILE,books); rows=[payload]

    result = rows[0] if rows else payload
    try:
        import qrcode as ql, base64; from io import BytesIO
        qr = ql.QRCode(version=1, box_size=6, border=2)
        qr.add_data(payload["id"]); qr.make(fit=True)
        img = qr.make_image(fill_color="#1a4f8a", back_color="white")
        buf = BytesIO(); img.save(buf, format="PNG")
        result["qr_code"] = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    except: result["qr_code"] = None
    return jsonify(result), 201


@books_bp.route("/<book_id>", methods=["PUT"])
def update_book(book_id):
    body = request.get_json(force=True) or {}
    for k in ["id","criado_em","generos","genero_nome","genero_cor","genero_icone"]: body.pop(k,None)
    sb = get_client()
    if table_ok(sb, "livros"):
        try: rows = sb_exec(sb.table("livros").update(body).eq("id", book_id))
        except Exception as e:
            if "genero_id" in str(e): body.pop("genero_id",None); rows = sb_exec(sb.table("livros").update(body).eq("id", book_id))
            elif is_offline_error(e):
                books=read_json(BOOKS_FILE); rows=[]
                for b in books:
                    if b.get("id")==book_id: b.update(body); rows=[b]; break
                write_json(BOOKS_FILE,books)
            else: raise
        if not rows: return jsonify({"error": "Livro não encontrado"}), 404
        return jsonify(rows[0])
    books=read_json(BOOKS_FILE)
    for b in books:
        if b.get("id")==book_id: b.update(body); write_json(BOOKS_FILE,books); return jsonify(b)
    return jsonify({"error": "Livro não encontrado"}), 404


@books_bp.route("/<book_id>", methods=["DELETE"])
def delete_book(book_id):
    sb = get_client()
    try: ativos = sb_exec(sb.table("emprestimos").select("id").eq("livro_id",book_id).is_("devolvido_em","null"))
    except: ativos = [l for l in read_json(LOAN_FILE) if l.get("livro_id")==book_id and not l.get("devolvido_em")]
    if ativos: return jsonify({"error": "Livro possui empréstimos ativos."}), 409
    if table_ok(sb, "livros"):
        try:
            if has_deleted_at(sb, "livros"): sb_exec(sb.table("livros").update({"deleted_at":today_str()}).eq("id",book_id))
            else: sb_exec(sb.table("livros").delete().eq("id",book_id))
            return jsonify({"success": True})
        except: pass
    books=read_json(BOOKS_FILE); write_json(BOOKS_FILE,[b for b in books if b.get("id")!=book_id])
    return jsonify({"success": True})