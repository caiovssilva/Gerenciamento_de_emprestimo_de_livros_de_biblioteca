"""api/auth.py — Autenticação via tabela usuarios do Supabase."""
from flask import Blueprint, request, jsonify, current_app, session
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
import os
from pathlib import Path
import unicodedata

# Prefer passlib for portable password verification.
# Add explicit bcrypt support in case the system lacks passlib backends.
try:
    from passlib.context import CryptContext
    _pwd_ctx = CryptContext(
        schemes=["bcrypt", "pbkdf2_sha256", "sha512_crypt", "sha256_crypt", "des_crypt"],
        deprecated="auto"
    )
except Exception:
    _pwd_ctx = None

try:
    import bcrypt
except Exception:
    bcrypt = None

try:
    import crypt as unix_crypt  # type: ignore
except Exception:
    unix_crypt = None

from utils import get_client, sb_exec
from api._helpers import read_json
from api.controle import self_service_operation_allowed

auth_bp = Blueprint("auth", __name__)
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SELF_SERVICE_TOKEN_MAX_AGE = 30 * 60
DEFAULT_DEV_SECRET = "narceu-biblioteca-2026-dev-only"

LOGIN_ALIASES = {
    "bibliotecario": "biblioteca",
    "bibliotecaria": "biblioteca",
}

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
    # If passlib is available and the scheme is not bcrypt/2y/2b,
    # let it identify and verify the scheme.
    try:
        if _pwd_ctx is not None and not (isinstance(stored_hash, str) and stored_hash.startswith("$2")):
            return _pwd_ctx.verify(password, stored_hash)
    except Exception:
        # Verification via passlib failed; fall back to bcrypt/unix crypt if available
        pass

    # If the stored value doesn't look like a hashed string, treat it
    # as a legacy plain-text password (created by earlier DB seeds).
    # Accept equality and let the caller re-hash the password for safety.
    try:
        if isinstance(stored_hash, str) and "$" not in stored_hash:
            return password == stored_hash
    except Exception:
        pass

    if 'unix_crypt' in globals() and unix_crypt is not None:
        try:
            return unix_crypt.crypt(password, stored_hash) == stored_hash
        except Exception:
            return False

    if bcrypt is not None and isinstance(stored_hash, str) and stored_hash.startswith('$2'):
        try:
            return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
        except Exception:
            return False

    return False


def _get_user_by_login(login_str: str):
    sb = get_client()
    requested_login = (login_str or "").strip().lower()
    canonical_login = LOGIN_ALIASES.get(requested_login, requested_login)
    login_candidates = [canonical_login]
    if requested_login not in login_candidates:
        login_candidates.append(requested_login)
    # Try exact match first (fast). If no result, fallback to reading
    # all users and matching case-insensitively to tolerate different
    # capitalization in the stored `login` values.
    try:
        rows = sb_exec(
            sb.table("usuarios")
            .select("id,nome,login,senha")
            .in_("login", login_candidates)
        )
    except Exception:
        rows = []

    if rows:
        return rows[0]

    # Fallback: try case-insensitive match by fetching all users (small table).
    try:
        all_rows = sb_exec(sb.table("usuarios").select("id,nome,login,senha"))
        if all_rows:
            for r in all_rows:
                if (r.get("login") or "").strip().lower() in login_candidates:
                    return r
    except Exception:
        pass

    return None


def _self_service_serializer():
    session_secret = current_app.config.get("SECRET_KEY")
    if not session_secret or session_secret == DEFAULT_DEV_SECRET:
        return None
    secret = os.getenv("SELF_SERVICE_SECRET_KEY") or session_secret
    if not secret:
        return None
    return URLSafeTimedSerializer(secret, salt="biblioteca-self-service-v1")


def _normalize_card_code(value) -> str:
    normalized = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return "".join(character for character in normalized if character.isalnum())


def _get_student_by_card(code: str):
    sb = get_client()
    normalized_code = str(code or "").strip()
    if not normalized_code:
        return None
    for field in ("id", "carteirinha"):
        try:
            rows = sb_exec(sb.table("alunos").select("*").eq(field, normalized_code))
            if rows:
                student = rows[0]
                if not student.get("deleted_at"):
                    return student
        except Exception:
            pass

    try:
        students = sb_exec(sb.table("alunos").select("*"))
    except Exception:
        students = read_json(DATA_DIR / "alunos.json")
    normalized_code = _normalize_card_code(normalized_code)
    if not normalized_code:
        return None
    matches = [
        student for student in students
        if not student.get("deleted_at")
        and normalized_code in {
            _normalize_card_code(student.get(field))
            for field in ("id", "carteirinha", "card", "matricula")
        }
    ]
    unique_students = {str(student.get("id") or student.get("carteirinha") or id(student)): student for student in matches}
    return next(iter(unique_students.values())) if len(unique_students) == 1 else None


def _self_service_student_from_request():
    serializer = _self_service_serializer()
    if serializer is None:
        return None, (jsonify({"error": "Autoatendimento indisponível: configure uma chave secreta segura."}), 503)

    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None, (jsonify({"error": "Sessão de autoatendimento inválida ou expirada."}), 401)

    try:
        payload = serializer.loads(token, max_age=SELF_SERVICE_TOKEN_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None, (jsonify({"error": "Sessão de autoatendimento inválida ou expirada."}), 401)

    if payload.get("scope") != "student_history" or not payload.get("student_id"):
        return None, (jsonify({"error": "Sessão de autoatendimento inválida ou expirada."}), 401)
    student_id = str(payload["student_id"])
    if session.get("access_scope") != "self_service" or str(session.get("student_id", "")) != student_id:
        return None, (jsonify({"error": "Sessão de autoatendimento inválida ou expirada."}), 401)
    return student_id, None


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

        auth_debug = os.getenv("AUTH_DEBUG", "").lower() in ("1","true","yes")

        if not user:
            if auth_debug:
                current_app.logger.info(f"Login falhou: usuário '{login_str}' não encontrado")
            else:
                current_app.logger.warning(f"Falha de login para '{login_str}'")
            return jsonify({"error": "Usuário ou senha incorretos"}), 401

        if not _verify_password(password, user.get("senha", "")):
            if auth_debug:
                current_app.logger.info(f"Login falhou para '{login_str}': senha inválida. Stored hash startswith: '{(user.get('senha') or '')[:10]}'")
            else:
                current_app.logger.warning(f"Falha de login para '{login_str}'")
            return jsonify({"error": "Usuário ou senha incorretos"}), 401
        # If login succeeded but the stored senha looks like plain-text,
        # re-hash it using passlib and update the Supabase record to a
        # secure scheme. This makes future verifications reliable.
        stored = user.get("senha") or ""
        try:
            looks_hashed = isinstance(stored, str) and "$" in stored
            if _pwd_ctx is not None and not looks_hashed:
                try:
                    new_hash = _pwd_ctx.hash(password)
                    sb = get_client()
                    # update the user's senha in the DB; ignore errors
                    try:
                        sb_exec(sb.table("usuarios").update({"senha": new_hash}).eq("id", user["id"]))
                        if auth_debug:
                            current_app.logger.info(f"Rehashed senha para usuário '{login_str}' (id={user.get('id')})")
                    except Exception:
                        if auth_debug:
                            current_app.logger.warning(f"Falha ao atualizar hash da senha para '{login_str}'")
                except Exception:
                    # If hashing fails, continue without blocking login.
                    if auth_debug:
                        current_app.logger.info(f"Não foi possível re-hash da senha para '{login_str}'")
        except Exception:
            pass

        normalized_login = (user["login"] or "").strip().lower()
        access = "librarian" if normalized_login in ("bibliotecario", "biblioteca") else "admin"
        session.clear()
        session["access_scope"] = "staff_librarian" if access == "librarian" else "staff_admin"
        return jsonify({
            "access": access,
            "id": user["id"],
            "login": user["login"],
            "name": user.get("nome") or user.get("name")
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Erro ao fazer login: {e}")
        return jsonify({"error": "Erro ao processar login"}), 500


@auth_bp.route("/self-service/login", methods=["POST"])
def self_service_login():
    """Emite uma sessão restrita ao titular de uma carteirinha cadastrada."""
    if not self_service_operation_allowed():
        return jsonify({"error": "O Autoatendimento está desativado pelo administrador."}), 403
    serializer = _self_service_serializer()
    if serializer is None:
        return jsonify({"error": "Autoatendimento indisponível: configure uma chave secreta segura."}), 503

    body = request.get_json(force=True) or {}
    code = str(body.get("code") or "").strip()
    if not code:
        return jsonify({"error": "Leia a carteirinha para continuar."}), 400

    try:
        student = _get_student_by_card(code)
        if not student:
            return jsonify({"error": "Carteirinha não reconhecida para autoatendimento."}), 401

        token = serializer.dumps({"scope": "student_history", "student_id": str(student["id"])})
        session.clear()
        session["access_scope"] = "self_service"
        session["student_id"] = str(student["id"])
        return jsonify({
            "access": "self_service",
            "token": token,
            "name": student.get("nome") or student.get("name") or "Aluno",
        }), 200
    except Exception as error:
        current_app.logger.error("Erro no login de autoatendimento: %s", error)
        return jsonify({"error": "Erro ao validar a carteirinha."}), 500


@auth_bp.route("/self-service/logout", methods=["POST"])
def self_service_logout():
    session.clear()
    return jsonify({"success": True}), 200


@auth_bp.route("/self-service/history", methods=["GET"])
def self_service_history():
    """Retorna somente o histórico pertencente à carteirinha autenticada."""
    if not self_service_operation_allowed():
        return jsonify({"error": "O Autoatendimento está desativado pelo administrador."}), 403
    student_id, error_response = _self_service_student_from_request()
    if error_response:
        return error_response

    try:
        sb = get_client()
        try:
            loans = sb_exec(
                sb.table("emprestimos").select("*").eq("aluno_id", student_id)
            )
        except Exception:
            loans = [
                loan for loan in read_json(DATA_DIR / "emprestimos.json")
                if str(loan.get("aluno_id", "")) == student_id
            ]

        try:
            books = sb_exec(sb.table("livros").select("id,titulo,autor"))
        except Exception:
            books = read_json(DATA_DIR / "livros.json")
        books_by_id = {str(book.get("id")): book for book in books}

        history = []
        for loan in loans:
            book = books_by_id.get(str(loan.get("livro_id", "")), {})
            history.append({
                "loan_id": loan.get("id"),
                "book_id": loan.get("livro_id"),
                "book_title": book.get("titulo") or book.get("title") or "Livro não encontrado",
                "book_author": book.get("autor") or book.get("author") or "",
                "exemplar": loan.get("exemplar"),
                "exemplar_id": loan.get("exemplar_id"),
                "loan_date": loan.get("data_emprestimo"),
                "due_date": loan.get("data_devolucao_prevista"),
                "returned_at": loan.get("devolvido_em"),
            })
        history.sort(key=lambda item: str(item.get("loan_date") or ""), reverse=True)

        students = read_json(DATA_DIR / "alunos.json")
        student = next((row for row in students if str(row.get("id")) == student_id), None)
        if student is None:
            try:
                rows = sb_exec(sb.table("alunos").select("id,nome,turma,carteirinha").eq("id", student_id))
                student = rows[0] if rows else {}
            except Exception:
                student = {}

        return jsonify({
            "student": {
                "name": student.get("nome") or student.get("name") or "Aluno",
                "class": student.get("turma") or student.get("class") or "",
                "card": student.get("carteirinha") or "",
            },
            "history": history,
        }), 200
    except Exception as error:
        current_app.logger.error("Erro ao consultar histórico de autoatendimento: %s", error)
        return jsonify({"error": "Erro ao carregar o histórico."}), 500


@auth_bp.route("/self-service/books", methods=["GET"])
def self_service_books():
    """Lista somente livros com exemplares disponíveis para o aluno autenticado."""
    if not self_service_operation_allowed("allow_borrow"):
        return jsonify({"error": "Empréstimos pelo Autoatendimento estão desativados pelo administrador."}), 403
    student_id, error_response = _self_service_student_from_request()
    if error_response:
        return error_response

    try:
        from api.loans import _available_copies_from_rows

        sb = get_client()
        books = sb_exec(sb.table("livros").select("*").order("titulo"))
        active_loans = sb_exec(
            sb.table("emprestimos").select("livro_id,exemplar,exemplar_id").is_("devolvido_em", "null")
        )
        available_books = []
        for book in books:
            book_loans = [loan for loan in active_loans if str(loan.get("livro_id")) == str(book.get("id"))]
            available = _available_copies_from_rows(
                book.get("id"),
                book.get("exemplares", 1),
                book.get("exemplares_ids"),
                book.get("exemplares_meta"),
                book_loans,
            )
            if not available:
                continue
            available_books.append({
                "id": book.get("id"),
                "titulo": book.get("titulo") or book.get("title") or "Livro sem título",
                "autor": book.get("autor") or book.get("author") or "",
                "isbn": book.get("isbn") or "",
                "available_copies": len(available),
            })
        return jsonify(available_books), 200
    except Exception as error:
        current_app.logger.error("Erro ao consultar acervo do autoatendimento: %s", error)
        return jsonify({"error": "Não foi possível carregar os livros disponíveis."}), 500


@auth_bp.route("/self-service/loans", methods=["POST"])
def self_service_create_loan():
    """Registra empréstimo associado exclusivamente à carteirinha autenticada."""
    if not self_service_operation_allowed("allow_borrow"):
        return jsonify({"error": "Empréstimos pelo Autoatendimento estão desativados pelo administrador."}), 403
    student_id, error_response = _self_service_student_from_request()
    if error_response:
        return error_response

    body = request.get_json(force=True) or {}
    exemplar_qr = str(body.get("exemplar_qr") or "").strip()
    if not exemplar_qr:
        return jsonify({"error": "Leia o QR Code do exemplar para continuar."}), 400

    from scanner.routes import _resolve_qr

    resolved = _resolve_qr(exemplar_qr)
    book = resolved.get("data") or {}
    if resolved.get("type") != "book" or not book.get("exemplar_code"):
        return jsonify({"error": "O QR Code não identifica um exemplar cadastrado."}), 400

    from api.loans import _create_loan_record

    return _create_loan_record(
        {
            "livro_id": book["id"],
            "exemplar": book["exemplar_code"],
            "dias": 7,
            "observacao": "",
        },
        forced_student_id=student_id,
        created_by_override="autoatendimento",
    )


def _self_service_owned_loan(loan_id, required_setting):
    from api.controle import self_service_operation_allowed

    if not self_service_operation_allowed(required_setting):
        return None, jsonify({"error": "Esta operação está desativada pelo administrador."}), 403

    student_id, error_response = _self_service_student_from_request()
    if error_response:
        response, status = error_response
        return None, response, status

    try:
        from utils import sb_exec

        rows = sb_exec(get_client().table("emprestimos").select("*").eq("id", loan_id))
    except Exception:
        rows = [
            loan for loan in read_json(DATA_DIR / "emprestimos.json")
            if str(loan.get("id", "")) == str(loan_id)
        ]
    if not rows:
        return None, jsonify({"error": "Empréstimo não encontrado."}), 404
    if str(rows[0].get("aluno_id", "")) != student_id:
        return None, jsonify({"error": "Este empréstimo não pertence à carteirinha lida."}), 403
    return student_id, None, None


@auth_bp.route("/self-service/loans/<loan_id>/renew", methods=["POST"])
def self_service_renew_loan(loan_id):
    _student_id, response, status = _self_service_owned_loan(loan_id, "allow_renew")
    if response:
        return response, status

    from api.loans import renew_loan

    return renew_loan(loan_id)


@auth_bp.route("/self-service/loans/<loan_id>/return", methods=["POST"])
def self_service_return_loan(loan_id):
    _student_id, response, status = _self_service_owned_loan(loan_id, "allow_return")
    if response:
        return response, status

    from api.loans import return_loan

    return return_loan(loan_id)


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
            current_app.logger.error("Supabase não configurado")
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
