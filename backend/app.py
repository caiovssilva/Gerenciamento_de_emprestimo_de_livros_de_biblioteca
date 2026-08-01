"""
app.py — Biblioteca narceu de paiva filho Campus Aracruz (v3)
Servidor Flask que serve o backend (API) e o frontend (SPA) juntos.
"""
import os, sys
from pathlib import Path
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, jsonify, send_from_directory
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
    from utils import get_client
    try:
        get_client().table("livros").select("id").limit(1).execute()
        logger.info("Health check OK - Database connected")
        return jsonify({"status": "ok", "service": "Biblioteca narceu de paiva filho v3", "database": "conectado"}), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({"status": "offline", "service": "Biblioteca narceu de paiva filho v3", "database": f"offline — {e}", "hint": "defina SUPABASE_URL e SUPABASE_KEY reais no backend/.env"}), 200

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

if __name__ == "__main__":
    port  = int(os.getenv("PORT", os.getenv("FLASK_PORT", 5000)))
    debug = os.getenv("FLASK_ENV", "development") == "development"
    print(f"\n🚀 Biblioteca narceu de paiva filho v3 — http://localhost:{port}\n")
    print(f"📝 DEBUG mode: {debug}")
    print(f"🔐 Secret key set: {'Yes' if os.getenv('SECRET_KEY') else 'No (using default)'}\n")
    app.run(host="0.0.0.0", port=port, debug=debug)