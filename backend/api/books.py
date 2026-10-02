"""api/books.py — CRUD de livros com fallback JSON local."""
import json
import logging
import os
import re
import time
import unicodedata
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from openai import OpenAI, OpenAIError
from flask import Blueprint, request, jsonify
from pathlib import Path
from utils import get_client, sb_exec, new_id, today_str
from api._helpers import read_json, write_json, table_ok, has_deleted_at, is_offline_error

books_bp   = Blueprint("books", __name__)
logger = logging.getLogger(__name__)
DATA_DIR   = Path(__file__).resolve().parent.parent / "data"
BOOKS_FILE = DATA_DIR / "livros.json"
GENR_FILE  = DATA_DIR / "generos.json"
LOAN_FILE  = DATA_DIR / "emprestimos.json"
_ISBN_CACHE: OrderedDict[str, dict] = OrderedDict()
_ISBN_CACHE_TIMESTAMPS: dict[str, float] = {}
_ISBN_CACHE_TTL_SECONDS = 15 * 60
_ISBN_CACHE_MAX_SIZE = 128
_PROVIDER_TIMEOUT_SECONDS = 6
_PROVIDER_ATTEMPTS = 2
_PROVIDER_RETRY_DELAY_SECONDS = 0.2
_GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
_GROQ_BASE_URL = "https://api.groq.com/openai/v1"
_GROQ_DEFAULT_MODEL = "allam-2-7b"


def _normalize_isbn(value: str) -> str:
    return re.sub(r"[^0-9Xx]", "", str(value or "")).upper()


def _validate_isbn(normalized: str) -> None:
    if len(normalized) == 10:
        if not re.fullmatch(r"[0-9]{9}[0-9X]", normalized):
            raise ValueError("Informe um ISBN-10 válido.")
        total = sum((10 - index) * (10 if digit == "X" else int(digit))
                    for index, digit in enumerate(normalized))
        if total % 11 != 0:
            raise ValueError("Informe um ISBN-10 válido.")
        return

    if len(normalized) == 13 and normalized.isdigit():
        total = sum(int(digit) * (1 if index % 2 == 0 else 3)
                    for index, digit in enumerate(normalized))
        if total % 10 == 0:
            return

    raise ValueError("Informe um ISBN-10 ou ISBN-13 válido.")


class _ProviderError(RuntimeError):
    def __init__(self, source: str, message: str):
        super().__init__(message)
        self.source = source


def _open_provider(request_obj: Request, source: str):
    for attempt in range(_PROVIDER_ATTEMPTS):
        try:
            return urlopen(request_obj, timeout=_PROVIDER_TIMEOUT_SECONDS)
        except HTTPError as exc:
            retryable = exc.code in {408, 429, 500, 502, 503, 504}
            if retryable and attempt + 1 < _PROVIDER_ATTEMPTS:
                time.sleep(_PROVIDER_RETRY_DELAY_SECONDS)
                continue
            if exc.code == 404:
                raise LookupError("Livro não encontrado para este ISBN.") from exc
            raise _ProviderError(source, f"A fonte {source} respondeu HTTP {exc.code}.") from exc
        except (URLError, TimeoutError) as exc:
            if attempt + 1 < _PROVIDER_ATTEMPTS:
                time.sleep(_PROVIDER_RETRY_DELAY_SECONDS)
                continue
            raise _ProviderError(source, f"Não foi possível consultar {source} agora.") from exc


def _google_books_lookup(isbn: str) -> dict:
    normalized = _normalize_isbn(isbn)
    _validate_isbn(normalized)

    api_key = os.getenv("GOOGLE_BOOKS_API_KEY", "").strip()
    url = "https://www.googleapis.com/books/v1/volumes?q=isbn:" + normalized
    if api_key:
        url += "&key=" + api_key
    request_obj = Request(url, headers={"Accept": "application/json"})
    try:
        with _open_provider(request_obj, "Google Books") as response:
            data = json.load(response)
    except (ValueError, TypeError) as exc:
        raise _ProviderError("Google Books", "A Google Books retornou uma resposta inválida.") from exc

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

    result = {
        "isbn": found_isbn,
        "titulo": str(info.get("title") or "").strip(),
        "autor": ", ".join(str(author).strip() for author in (info.get("authors") or []) if str(author).strip()),
        "categorias": [str(category).strip() for category in (info.get("categories") or []) if str(category).strip()],
    }
    if not any((result["titulo"], result["autor"], result["categorias"])):
        raise LookupError("Livro não encontrado para este ISBN.")
    return result


def _groq_lookup(isbn: str) -> dict:
    """Obtém uma sugestão inicial do Groq; as outras fontes fazem a confirmação."""
    normalized = _normalize_isbn(isbn)
    _validate_isbn(normalized)
    api_key = (
        os.getenv("GROQ_API_KEY")
        or os.getenv("API_GROQ")
        or os.getenv("GROQ_API")
        or ""
    ).strip()
    if not api_key:
        raise LookupError("Groq não configurado.")

    model = os.getenv("GROQ_MODEL", _GROQ_DEFAULT_MODEL).strip() or _GROQ_DEFAULT_MODEL
    payload = {
        "model": model,
        "temperature": 0,
        "max_tokens": 300,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Você é um extrator de metadados bibliográficos. Responda somente JSON com "
                    "isbn, titulo, autor e categorias. Não invente dados: use string vazia ou "
                    "lista vazia quando não souber. O ISBN informado é a única identidade aceita."
                ),
            },
            {
                "role": "user",
                "content": f"ISBN: {normalized}. Retorne os metadados conhecidos deste livro.",
            },
        ],
    }
    try:
        client = OpenAI(
            api_key=api_key,
            base_url=_GROQ_BASE_URL,
            timeout=_PROVIDER_TIMEOUT_SECONDS,
            max_retries=0,
        )
        response = client.chat.completions.create(**payload)
        content = response.choices[0].message.content
    except (OpenAIError, OSError) as exc:
        raise _ProviderError("Groq", "Não foi possível consultar o Groq agora.") from exc
    try:
        result = json.loads(content)
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise _ProviderError("Groq", "O Groq retornou uma resposta inválida.") from exc

    result = {
        "isbn": normalized,
        "titulo": str(result.get("titulo") or "").strip(),
        "autor": str(result.get("autor") or "").strip(),
        "categorias": [str(item).strip() for item in (result.get("categorias") or []) if str(item).strip()],
    }
    if not any((result["titulo"], result["autor"], result["categorias"])):
        raise LookupError("Groq não encontrou dados para este ISBN.")
    return result


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
        label = text.split(":", 1)[0].strip().lower()
        if label in {"author", "authors"}:
            self._capture_authors = True
            self._in_authors = True
            self.authors += text.split(":", 1)[1].strip()


def _isbnsearch_lookup(isbn: str) -> dict:
    normalized = _normalize_isbn(isbn)
    _validate_isbn(normalized)
    url = "https://isbnsearch.org/isbn/" + normalized
    request_obj = Request(url, headers={"Accept": "text/html", "User-Agent": "Mozilla/5.0"})
    try:
        with _open_provider(request_obj, "ISBNsearch") as response:
            parser = _IsbnSearchParser()
            parser.feed(response.read().decode("utf-8", errors="replace"))
    except UnicodeError as exc:
        raise _ProviderError("ISBNsearch", "O ISBNsearch retornou uma resposta inválida.") from exc

    title = re.sub(r"^ISBN\s+\S+\s*-\s*", "", parser.title, flags=re.IGNORECASE).strip()
    authors = re.sub(r"\s*[-|].*$", "", parser.authors).strip()
    if not title or title.upper().startswith("ISBN "):
        raise LookupError("Livro não encontrado para este ISBN.")

    return {"isbn": normalized, "titulo": title, "autor": authors, "categorias": []}


def _openlibrary_lookup(isbn: str) -> dict:
    normalized = _normalize_isbn(isbn)
    _validate_isbn(normalized)
    url = "https://openlibrary.org/api/books?bibkeys=ISBN:" + normalized + "&jscmd=data&format=json"
    request_obj = Request(url, headers={"Accept": "application/json", "User-Agent": "Biblioteca/1.0"})
    try:
        with _open_provider(request_obj, "Open Library") as response:
            data = json.load(response)
    except (ValueError, TypeError) as exc:
        raise _ProviderError("Open Library", "A Open Library retornou uma resposta inválida.") from exc

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


def _match_genre(categories: list[str]) -> tuple[str, str]:
    """Relaciona categorias externas a um gênero cadastrado no sistema."""
    def normalize(value):
        without_accents = unicodedata.normalize("NFKD", str(value or ""))
        without_accents = "".join(char for char in without_accents if not unicodedata.combining(char))
        return re.sub(r"[^a-z0-9]+", " ", without_accents.lower()).strip()
    aliases = {
        "ficcao cientifica": ["science fiction", "sci fi", "scifi"],
        "historia": ["history", "historical"],
        "biografia": ["biography", "autobiography", "memoir"],
        "romance": ["romance", "love story", "romantic fiction"],
        "aventura": ["adventure"],
        "comedia": ["comedy", "humor"],
        "terror suspense": ["horror", "thriller", "suspense"],
        "autoajuda": ["self help", "self improvement"],
        "tecnico didatico": ["textbook", "technical", "educational"],
    }
    genres = read_json(GENR_FILE)
    if not genres:
        try:
            sb = get_client()
            genres = sb_exec(sb.table("generos").select("id,nome").order("nome"))
        except Exception:
            genres = []

    normalized_categories = [normalize(category) for category in categories or []]
    for genre in genres:
        genre_name = str(genre.get("nome") or "").strip()
        normalized_name = normalize(genre_name)
        terms = [normalized_name, *aliases.get(normalized_name, [])]
        if any(category and (term in category or category in term)
               for category in normalized_categories for term in terms):
            return str(genre.get("id") or ""), genre_name
    return "", ""


def _normalize_metadata_text(value: str) -> str:
    without_accents = unicodedata.normalize("NFKD", str(value or ""))
    without_accents = "".join(char for char in without_accents if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", without_accents).strip().casefold()


def _select_metadata_field(results: list[dict], field: str, groq_result: dict | None = None) -> str:
    candidates = []
    for provider_name, result in results:
        value = str(result.get(field) or "").strip()
        if value:
            candidates.append((provider_name, value, _normalize_metadata_text(value)))

    if candidates:
        counts = {}
        for _, _, normalized in candidates:
            counts[normalized] = counts.get(normalized, 0) + 1
        consensus = max(counts.values())
        if consensus >= 2:
            for provider_name, value, normalized in candidates:
                if counts[normalized] == consensus:
                    return value
        return candidates[0][1]

    return str((groq_result or {}).get(field) or "").strip()


def _combine_metadata_categories(results: list[dict], groq_result: dict | None = None) -> list[str]:
    categories = []
    for _, result in results:
        for category in result.get("categorias") or []:
            value = str(category).strip()
            if value and not any(_normalize_metadata_text(value) == _normalize_metadata_text(existing)
                                 for existing in categories):
                categories.append(value)
    if categories:
        return categories
    return [str(category).strip() for category in (groq_result or {}).get("categorias") or [] if str(category).strip()]


def _lookup_isbn(isbn: str, use_groq: bool = False) -> dict:
    normalized = _normalize_isbn(isbn)
    _validate_isbn(normalized)
    cached = _ISBN_CACHE.get(normalized)
    cached_at = _ISBN_CACHE_TIMESTAMPS.get(normalized, 0)
    if cached and time.monotonic() - cached_at < _ISBN_CACHE_TTL_SECONDS:
        _ISBN_CACHE.move_to_end(normalized)
        return deepcopy(cached)
    if cached:
        _ISBN_CACHE.pop(normalized, None)
        _ISBN_CACHE_TIMESTAMPS.pop(normalized, None)

    providers = (
        ("Google Books", _google_books_lookup),
        ("ISBNsearch", _isbnsearch_lookup),
        ("Open Library", _openlibrary_lookup),
    )
    providers_to_call = (("Groq", _groq_lookup), *providers) if use_groq else providers
    errors = []
    groq_result = None
    unavailable_provider = False

    def call_provider(item):
        provider_name, provider = item
        try:
            return provider_name, provider(normalized), None
        except (LookupError, _ProviderError) as exc:
            return provider_name, None, exc

    # As fontes de confirmação são independentes; consultá-las juntas reduz a latência.
    with ThreadPoolExecutor(max_workers=len(providers_to_call)) as executor:
        responses = list(executor.map(call_provider, providers_to_call))

    bibliographic_results = []
    for provider_name, found, error in responses:
        if error:
            errors.append(error)
            if isinstance(error, _ProviderError):
                unavailable_provider = True
                logger.warning("Consulta de ISBN falhou no provedor %s: %s", error.source, error)
            continue
        try:
            if isinstance(found, dict):
                if provider_name == "Groq":
                    groq_result = deepcopy(found)
                else:
                    bibliographic_results.append((provider_name, found))
        except (AttributeError, TypeError) as exc:
            errors.append(_ProviderError(provider_name, "A fonte retornou dados inválidos."))
            logger.warning("Consulta de ISBN falhou no provedor %s: %s", provider_name, exc)

    result = None
    if bibliographic_results or groq_result is not None:
        result = {
            "isbn": normalized,
            "titulo": _select_metadata_field(bibliographic_results, "titulo", groq_result),
            "autor": _select_metadata_field(bibliographic_results, "autor", groq_result),
            "categorias": _combine_metadata_categories(bibliographic_results, groq_result),
        }

    if result is not None:
        result["area"] = "Geral"
        result["genero_id"], result["genero_nome"] = _match_genre(result.get("categorias", []))
        if result.get("titulo") and result.get("autor") and result.get("categorias"):
            _ISBN_CACHE[normalized] = deepcopy(result)
            _ISBN_CACHE_TIMESTAMPS[normalized] = time.monotonic()
            _ISBN_CACHE.move_to_end(normalized)
            while len(_ISBN_CACHE) > _ISBN_CACHE_MAX_SIZE:
                expired_isbn, _ = _ISBN_CACHE.popitem(last=False)
                _ISBN_CACHE_TIMESTAMPS.pop(expired_isbn, None)
        return deepcopy(result)
    if unavailable_provider and errors:
        raise RuntimeError("Não foi possível consultar fontes de ISBN agora.") from errors[-1]
    raise LookupError("Livro não encontrado para este ISBN.")


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
    source = request.args.get("source", "manual").strip().lower()
    try:
        return jsonify(_lookup_isbn(isbn, use_groq=source == "scanner"))
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