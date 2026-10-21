"""
app.py — Biblioteca narceu de paiva filho Campus Aracruz (v3)
Servidor Flask que serve o backend (API) e o frontend (SPA) juntos.
"""
import os, sys
from pathlib import Path
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, jsonify, send_from_directory, request, session
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.exceptions import HTTPException
import logging

BACKEND_DIR = Path(__file__).resolve().parent


def load_environment():
    dotenv_path = BACKEND_DIR / ".env"
    load_dotenv(dotenv_path=dotenv_path, override=False)
    return dotenv_path


load_environment()

FRONTEND_DIR = os.path.abspath(os.path.join(BACKEND_DIR, "..", "frontend"))

from api.books    import books_bp
from api.students import students_bp
from api.loans    import loans_bp
from api.reports  import reports_bp
from api.rooms    import rooms_bp
from api.genres   import genres_bp
from api.auth     import auth_bp
from api.controle import controle_bp, librarian_operation_allowed
from scanner.routes import qr_bp

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
app.secret_key = os.getenv("SECRET_KEY", "narceu-biblioteca-2026-dev-only")

# ── Configuração de logging ──────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ── CORS configuration ───────────────────────────────────────────────
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ── Registrar blueprints ─────────────────────────────────────────────
app.register_blueprint(auth_bp,     url_prefix="/api/auth")
app.register_blueprint(controle_bp, url_prefix="/api/controle")
app.register_blueprint(books_bp,    url_prefix="/api/books")
app.register_blueprint(students_bp, url_prefix="/api/students")
app.register_blueprint(loans_bp,    url_prefix="/api/loans")
app.register_blueprint(reports_bp,  url_prefix="/api/reports")
app.register_blueprint(rooms_bp,    url_prefix="/api/rooms")
app.register_blueprint(genres_bp,   url_prefix="/api/genres")
app.register_blueprint(qr_bp,       url_prefix="/api/qr")


@app.route("/api/config/supabase", methods=["GET"])
@app.route("/api/supabase-config", methods=["GET"])
def legacy_supabase_config():
    from api.auth import get_supabase_config
    return get_supabase_config()


@app.after_request
def apply_security_headers(response):
    # CSP compatível com frontend atual, incluindo execução por CDN, câmera,
    # WebSocket/Supabase e handlers legados inline.
    csp = (
        "default-src 'self'; "
        "script-src 'self' https: blob: 'unsafe-inline'; "
        "style-src 'self' https: 'unsafe-inline'; "
        "font-src 'self' https: data:; "
        "img-src 'self' data: blob: https:; "
        "connect-src 'self' https: wss:; "
        "media-src 'self' blob:; "
        "worker-src 'self' blob:; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "frame-ancestors 'self'"
    )
    response.headers["Content-Security-Policy"] = csp
    return response


@app.before_request
def restrict_self_service_api():
    """Limita a sessão do aluno ao próprio histórico e à saída."""
    if not request.path.startswith("/api/"):
        return None

    scope = session.get("access_scope")
    if scope == "staff_librarian":
        permission = None
        if request.method == "POST" and request.path == "/api/loans/":
            permission = "allow_borrow"
        elif request.method == "POST" and request.path.startswith("/api/loans/") and request.path.endswith("/return"):
            permission = "allow_return"
        elif request.method == "POST" and request.path.startswith("/api/loans/") and request.path.endswith("/renew"):
            permission = "allow_renew"
        if permission and not librarian_operation_allowed(permission):
            return jsonify({"error": "Esta operação está desativada pelo administrador."}), 403
        return None

    if scope != "self_service":
        return None
    if request.path == "/api/auth/login" and request.method == "POST":
        return None
    if request.path == "/api/auth/self-service/logout" and request.method == "POST":
        return None
    if request.path in {"/api/health", "/api/ready"} and request.method == "GET":
        return None
    if request.method == "GET" and request.path in {
        "/api/controle/autoatendimento",
        "/api/auth/config/supabase",
        "/api/config/supabase",
        "/api/auth/supabase-config",
        "/api/supabase-config",
    }:
        return None
    from api.controle import self_service_operation_allowed
    if not self_service_operation_allowed():
        return jsonify({"error": "O Autoatendimento está desativado pelo administrador."}), 403
    if request.path == "/api/auth/self-service/history" and request.method == "GET":
        return None
    if request.path == "/api/auth/self-service/books" and request.method == "GET":
        if not self_service_operation_allowed("allow_borrow"):
            return jsonify({"error": "Empréstimos pelo Autoatendimento estão desativados pelo administrador."}), 403
        return None
    if request.path == "/api/auth/self-service/loans" and request.method == "POST":
        if not self_service_operation_allowed("allow_borrow"):
            return jsonify({"error": "Empréstimos pelo Autoatendimento estão desativados pelo administrador."}), 403
        return None
    if request.path == "/api/qr/decode" and request.method == "POST":
        if any(self_service_operation_allowed(setting) for setting in ("allow_borrow", "allow_return", "allow_renew")):
            return None
        return jsonify({"error": "Leitura de QR Code desativada pelo administrador."}), 403
    if request.path.startswith("/api/auth/self-service/loans/") and request.method == "POST":
        return None
    return jsonify({"error": "A sessão de autoatendimento permite apenas operar os empréstimos da carteirinha lida."}), 403

@app.before_request
def require_database_for_api():
    """Impede que qualquer API de negócio sirva ou grave dados locais."""
    if not request.path.startswith("/api/") or request.path in {
        "/api/health",
        "/api/ready",
        "/api/auth/config/supabase",
        "/api/config/supabase",
        "/api/auth/supabase-config",
        "/api/supabase-config",
        "/api/books/isbn-lookup",
        "/api/books/isbn-vision",
    }:
        return None
    try:
        from utils import get_client, sb_exec
        sb_exec(get_client().table("livros").select("id").limit(1))
    except Exception as exc:
        logger.warning("API bloqueada: Supabase indisponível: %s", exc)
        return jsonify({
            "error": "Banco de dados indisponível. A aplicação está aguardando a conexão.",
            "code": "DATABASE_UNAVAILABLE",
            "retry_after": 3,
        }), 503
    return None

# ── Tratamento de erros ───────────────────────────────────────────────
@app.errorhandler(HTTPException)
def handle_http(err):
    logger.warning(f"HTTP Error {err.code}: {err.description}")
    return jsonify({"error": err.description}), err.code

@app.errorhandler(Exception)
def handle_generic(err):
    logger.error(f"Erro não tratado: {err}", exc_info=True)
    return jsonify({"error": "Erro interno do servidor. Contacte o administrador."}), 500

# ── Health check ──────────────────────────────────────────────────────
@app.route("/api/health")
def health():
    """Liveness probe: confirma que o processo Flask está respondendo."""
    return jsonify({"status": "ok", "service": "Biblioteca narceu de paiva filho v3"}), 200


@app.route("/api/ready")
def readiness():
    """Readiness probe: confirma que a aplicação consegue consultar o Supabase."""
    from utils import get_client
    try:
        get_client().table("livros").select("id").limit(1).execute()
        logger.info("Readiness check OK - Database connected")
        return jsonify({"status": "ready", "service": "Biblioteca narceu de paiva filho v3", "database": "conectado"}), 200
    except Exception as e:
        logger.error("Readiness check failed: %s", e)
        return jsonify({"status": "waiting", "service": "Biblioteca narceu de paiva filho v3", "database": "indisponível", "retry_after": 3}), 503

# ── Serve o frontend ──────────────────────────────────────────────────
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    if path.startswith("api/"):
        return jsonify({"error": "Not found"}), 404
    if path and os.path.exists(os.path.join(FRONTEND_DIR, path)):
        return send_from_directory(FRONTEND_DIR, path)
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route('/favicon.ico')
def favicon():
    # Serve a favicon if present, otherwise return empty 204 to avoid 404 noise.
    fav_path = os.path.join(FRONTEND_DIR, 'favicon.ico')
    if os.path.exists(fav_path):
        return send_from_directory(FRONTEND_DIR, 'favicon.ico')
    return ('', 204)

if __name__ == "__main__":
    port  = int(os.getenv("PORT", os.getenv("FLASK_PORT", 5000)))
    debug = os.getenv("FLASK_ENV", "development") == "development"
    print(f"\n🚀 Biblioteca narceu de paiva filho v3 — http://localhost:{port}\n")
    print(f"📝 DEBUG mode: {debug}")
    print(f"🔐 Secret key set: {'Yes' if os.getenv('SECRET_KEY') else 'No (using default)'}\n")
    app.run(host="0.0.0.0", port=port, debug=debug)