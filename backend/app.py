"""
app.py — Biblioteca IFES Campus Aracruz (v3)
Servidor Flask que serve o backend (API) e o frontend (SPA) juntos.
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.exceptions import HTTPException
load_dotenv()

from api.books    import books_bp
from api.students import students_bp
from api.loans    import loans_bp
from api.reports  import reports_bp
from api.rooms    import rooms_bp
from api.genres   import genres_bp
from scanner.routes import qr_bp

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "ifes-biblioteca-2024")
CORS(app, resources={r"/api/*": {"origins": "*"}})

app.register_blueprint(books_bp,    url_prefix="/api/books")
app.register_blueprint(students_bp, url_prefix="/api/students")
app.register_blueprint(loans_bp,    url_prefix="/api/loans")
app.register_blueprint(reports_bp,  url_prefix="/api/reports")
app.register_blueprint(rooms_bp,    url_prefix="/api/rooms")
app.register_blueprint(genres_bp,   url_prefix="/api/genres")
app.register_blueprint(qr_bp,       url_prefix="/api/qr")

# ── Tratamento de erros ───────────────────────────────────────────────
@app.errorhandler(HTTPException)
def handle_http(err):
    return jsonify({"error": err.description}), err.code

@app.errorhandler(Exception)
def handle_generic(err):
    return jsonify({"error": str(err)}), 500

# ── Health check ──────────────────────────────────────────────────────
@app.route("/api/health")
def health():
    from utils import get_client
    try:
        get_client().table("livros").select("id").limit(1).execute()
        return jsonify({"status": "ok", "service": "Biblioteca IFES v3", "database": "conectado"})
    except Exception as e:
        return jsonify({"status": "offline", "service": "Biblioteca IFES v3", "database": f"offline — {e}"}), 200

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
    port  = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_ENV", "development") == "development"
    print(f"\n🚀 Biblioteca IFES v3 — http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=debug)