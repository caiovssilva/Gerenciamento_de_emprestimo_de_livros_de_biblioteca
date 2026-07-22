"""
scanner/routes.py
QR Code: geração, decodificação e geração de cartão imprimível (PDF-like PNG).
- /api/qr/decode      → decodifica imagem base64 e resolve o ID contra o banco
- /api/qr/generate    → gera QR Code PNG em base64
- /api/qr/card/book/<id>    → retorna imagem PNG do cartão do livro + QR
- /api/qr/card/student/<id> → retorna imagem PNG do cartão do aluno + QR
"""

import base64
import re
import threading
import time
from io import BytesIO

try:
    import cv2
    import numpy as np
    from pyzbar import pyzbar
except Exception:  # pragma: no cover - optional in some environments
    cv2 = None
    np = None
    pyzbar = None

from flask import Blueprint, jsonify, request, send_file

qr_bp = Blueprint("qr", __name__)

# ── Estado câmera servidor ────────────────────────────────────────────
_lock          = threading.Lock()
_camera_active = False
_last_result   = None
_camera_thread = None


def _scan_loop(camera_index: int = 0):
    global _camera_active, _last_result
    try:
        import cv2
        from pyzbar import pyzbar
    except ImportError:
        _camera_active = False
        return

    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        _camera_active = False
        return

    while _camera_active:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.1)
            continue
        decoded = pyzbar.decode(frame)
        if decoded:
            data = decoded[0].data.decode("utf-8", errors="replace")
            with _lock:
                _last_result   = data
                _camera_active = False
            break
        time.sleep(0.05)
    cap.release()


# ── Endpoints câmera servidor ─────────────────────────────────────────
@qr_bp.route("/start", methods=["POST"])
def start_scan():
    global _camera_active, _camera_thread, _last_result
    with _lock:
        if _camera_active:
            return jsonify({"status": "already_running"})
        _camera_active = True
        _last_result   = None
    idx = int((request.get_json(force=True) or {}).get("camera", 0))
    _camera_thread = threading.Thread(target=_scan_loop, args=(idx,), daemon=True)
    _camera_thread.start()
    return jsonify({"status": "started"})


@qr_bp.route("/stop", methods=["POST"])
def stop_scan():
    global _camera_active
    with _lock:
        _camera_active = False
    return jsonify({"status": "stopped"})


@qr_bp.route("/result", methods=["GET"])
def get_result():
    with _lock:
        return jsonify({"result": _last_result, "scanning": _camera_active})


@qr_bp.route("/status", methods=["GET"])
def camera_status():
    with _lock:
        return jsonify({"scanning": _camera_active, "last_result": _last_result})


# ── Decode: decodifica imagem e resolve ID no banco ───────────────────
@qr_bp.route("/decode", methods=["POST"])
def decode_image():
    """
    Decodifica QR/barcode da imagem base64.
    Depois tenta resolver o código decodificado contra livros e alunos no banco.
    Retorna: { primary, type: 'book'|'student'|'unknown', data: {...} }
    """
    try:
        from PIL import Image
    except ImportError as e:
        return jsonify({"error": f"Dependência faltando: {e}"}), 500

    try:
        if "file" in request.files:
            img_bytes = request.files["file"].read()
        else:
            body     = request.get_json(force=True) or {}
            b64_data = body.get("image", "")
            if "," in b64_data:
                b64_data = b64_data.split(",", 1)[1]
            img_bytes = base64.b64decode(b64_data)

        pil_img = Image.open(BytesIO(img_bytes)).convert("RGB")

        decoded = []
        try:
            if cv2 is not None and np is not None and pyzbar is not None:
                frame = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                decoded = pyzbar.decode(frame)
        except Exception:
            decoded = []

        if not decoded:
            try:
                import cv2
                import numpy as np
                frame = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                detector = cv2.QRCodeDetector()
                value, _, _ = detector.detectAndDecode(frame)
                if value:
                    decoded = [type("Decoded", (), {"data": value.encode("utf-8")})()]
            except Exception:
                decoded = []

        if not decoded:
            return jsonify({"codes": [], "primary": None, "type": "unknown"})

        primary = decoded[0].data.decode("utf-8", errors="replace")

        resolved = _resolve_qr(primary)
        return jsonify({
            "codes":   [d.data.decode("utf-8", errors="replace") for d in decoded],
            "primary": primary,
            **resolved,
        })

    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


ADMIN_CARD_PREFIX = "ADMIN-"
ADMIN_LOGIN_DEFAULT = "admin"


def _resolve_qr(code: str) -> dict:
    """Tenta encontrar o código como ID/ISBN de livro, carteirinha de aluno, QR único por exemplar ou cartão de admin."""
    from pathlib import Path
    from api._helpers import read_json
    DATA_DIR    = Path(__file__).resolve().parent.parent / "data"
    BOOKS_FILE  = DATA_DIR / "livros.json"
    ALUNOS_FILE = DATA_DIR / "alunos.json"

    code = (code or "").strip()

    if code.startswith(ADMIN_CARD_PREFIX):
        login = code[len(ADMIN_CARD_PREFIX):] or ADMIN_LOGIN_DEFAULT
        return {"type": "admin", "data": {"login": login}}

    book_ref = code
    exemplar_code = None
    exemplar_id = None
    match = re.match(r"^EXEMPLAR-(.+)-(.+)-(.+)$", code)
    if match:
        book_ref = match[1]
        exemplar_code = match[2]
        exemplar_id = match[3]

    try:
        from utils import get_client, sb_exec
        sb = get_client()

        try:
            books = sb_exec(sb.table("livros").select("*").eq("id", book_ref))
        except Exception:
            books = []
        if not books:
            try:
                books = sb_exec(sb.table("livros").select("*").eq("isbn", book_ref))
            except Exception:
                books = []
        if books:
            data = dict(books[0])
            if exemplar_code or exemplar_id:
                data["exemplar_code"] = exemplar_code
                data["exemplar_id"] = exemplar_id
            return {"type": "book", "data": data}

        try:
            students = sb_exec(sb.table("alunos").select("*").eq("id", code))
        except Exception:
            students = []
        if not students:
            try:
                students = sb_exec(sb.table("alunos").select("*").eq("carteirinha", code))
            except Exception:
                students = []
        if students:
            students[0]["is_librarian"] = bool(students[0].get("is_librarian", False))
            return {"type": "student", "data": students[0]}
    except Exception:
        pass

    try:
        books = [b for b in read_json(BOOKS_FILE) if b.get("id") == book_ref or b.get("isbn") == book_ref]
        if books:
            data = dict(books[0])
            if exemplar_code or exemplar_id:
                data["exemplar_code"] = exemplar_code
                data["exemplar_id"] = exemplar_id
            return {"type": "book", "data": data}
        students = [s for s in read_json(ALUNOS_FILE) if s.get("id") == code or s.get("carteirinha") == code]
        if students:
            students[0]["is_librarian"] = bool(students[0].get("is_librarian", False))
            return {"type": "student", "data": students[0]}
    except Exception:
        pass

    return {"type": "unknown", "data": None}


def _read_local_record(file_path, record_id, alt_field=None):
    from api._helpers import read_json

    rows = read_json(file_path)
    if alt_field:
        matches = [row for row in rows if row.get("id") == record_id or row.get(alt_field) == record_id]
    else:
        matches = [row for row in rows if row.get("id") == record_id]
    return matches[0] if matches else None


# ── Login por QR (carteirinha de admin ou bibliotecário) ──────────────
@qr_bp.route("/login", methods=["POST"])
def qr_login():
    """
    Recebe o código lido pela câmera (carteirinha) e resolve o tipo de acesso:
    - admin: cartão administrativo, login direto.
    - librarian: aluno com is_librarian=True, entra como Bibliotecário.
    - student: aluno comum, sem acesso ao painel (apenas informativo).
    - unknown: código não reconhecido.
    """
    body = request.get_json(force=True) or {}
    code = (body.get("code") or "").strip()
    if not code:
        return jsonify({"error": "Código vazio"}), 400

    resolved = _resolve_qr(code)

    if resolved["type"] == "admin":
        return jsonify({"access": "admin", **resolved})

    if resolved["type"] == "student":
        student = resolved["data"]
        if student.get("is_librarian"):
            return jsonify({"access": "librarian", "type": "student", "data": student})
        return jsonify({"access": "denied", "type": "student", "data": student,
                         "message": "Este aluno não possui acesso ao painel. Solicite ao administrador para 'Permitir acesso'."})

    return jsonify({"access": "denied", "type": resolved["type"], "data": resolved["data"],
                     "message": "Código não reconhecido."})


# ── Cartão imprimível: Administrador ──────────────────────────────────
@qr_bp.route("/card/admin/<login>", methods=["GET"])
def admin_card(login):
    """Gera a 'carteirinha' do administrador/bibliotecária, com QR Code de login."""
    try:
        users = {
            "admin":      {"name": "Administrador", "role": "Sistema"},
            "biblioteca": {"name": "Bibliotecária",  "role": "Sistema"},
        }
        info = users.get(login, {"name": login.capitalize(), "role": "Usuário"})
        qr_data = f"{ADMIN_CARD_PREFIX}{login}"

        img_b64 = _build_card(
            entity_type = "aluno",
            title       = info["name"],
            subtitle    = "Acesso administrativo",
            field1      = f"Usuário: {login}",
            field2      = f"Perfil: {info['role']}",
            field3      = "Acesso: Total ao sistema",
            qr_data     = qr_data,
            badge       = "ADMIN",
            color       = "#1a4f8a",
        )
        return jsonify({"image": img_b64, "filename": f"carteirinha-admin-{login}.png"})
    except ImportError as e:
        return jsonify({"error": f"Pillow não instalado: {e}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Geração de QR Code simples ────────────────────────────────────────
@qr_bp.route("/generate", methods=["POST"])
def generate_qr():
    import qrcode as qr_lib

    body = request.get_json(force=True) or {}
    data = body.get("data", "").strip()
    if not data:
        return jsonify({"error": "Campo 'data' obrigatório"}), 400

    color = body.get("color", "#1a4f8a")

    qr = qr_lib.QRCode(version=1, box_size=8, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color=color, back_color="white")

    buf = BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return jsonify({"image": f"data:image/png;base64,{b64}"})


# ── Cartão imprimível: Livro ──────────────────────────────────────────
@qr_bp.route("/card/book/<book_id>", methods=["GET"])
def book_card(book_id):
    """
    Gera imagem PNG do cartão do livro com QR Code para impressão.
    """
    try:
        from pathlib import Path
        from api._helpers import read_json
        from utils import get_client, sb_exec

        data_dir = Path(__file__).resolve().parent.parent / "data"
        books_file = data_dir / "livros.json"
        genres_file = data_dir / "generos.json"

        sb    = get_client()
        book = None
        try:
            books = sb_exec(sb.table("livros").select("*").eq("id", book_id))
        except Exception:
            books = []
        if books:
            book = books[0]
        if not book:
            rows = [b for b in read_json(books_file) if b.get("id") == book_id or b.get("isbn") == book_id]
            if rows:
                book = rows[0]
        if not book:
            return jsonify({"error": "Livro não encontrado"}), 404

        genres = {g.get("id"): g for g in read_json(genres_file)}
        genero = genres.get(book.get("genero_id"), {})
        book["genero_nome"] = book.get("genero_nome") or genero.get("nome", "")

        img_b64 = _build_card(
            entity_type = "livro",
            title       = book.get("titulo", ""),
            subtitle    = f"Autor: {book.get('autor', '')}",
            field1      = f"Gênero: {book.get('genero_nome', '') or 'N/A'}",
            field2      = f"ISBN: {book.get('isbn', '') or 'N/A'}",
            field3      = f"Exemplares: {book.get('exemplares', 1)}",
            qr_data     = book["id"],
            badge       = book.get("genero_nome", ""),
            color       = "#1a4f8a",
        )

        return jsonify({"image": img_b64, "filename": f"cartao-livro-{book_id[:8]}.png"})
    except ImportError as e:
        return jsonify({"error": f"Pillow não instalado: {e}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Cartão imprimível: Aluno ──────────────────────────────────────────
@qr_bp.route("/card/student/<student_id>", methods=["GET"])
def student_card(student_id):
    """
    Gera imagem PNG da carteirinha do aluno com QR Code para impressão.
    """
    try:
        from pathlib import Path
        from api._helpers import read_json
        from utils import get_client, sb_exec

        data_dir = Path(__file__).resolve().parent.parent / "data"
        students_file = data_dir / "alunos.json"
        rooms_file = data_dir / "salas.json"

        sb       = get_client()
        student = None
        try:
            students = sb_exec(sb.table("alunos").select("*").eq("id", student_id))
        except Exception:
            students = []
        if students:
            student = students[0]
        if not student:
            rows = [s for s in read_json(students_file) if s.get("id") == student_id or s.get("carteirinha") == student_id]
            if rows:
                student = rows[0]
        if not student:
            return jsonify({"error": "Aluno não encontrado"}), 404

        rooms = {r.get("id"): r for r in read_json(rooms_file)}
        sala_data = rooms.get(student.get("sala_id"), {})
        sala_nome = sala_data.get("nome", "") or "Não atribuída"

        img_b64 = _build_card(
            entity_type = "aluno",
            title       = student.get("nome", ""),
            subtitle    = f"Turma: {student.get('turma', '')}",
            field1      = f"Sala: {sala_nome}",
            field2      = f"Carteirinha: {student.get('carteirinha', '') or 'N/A'}",
            field3      = f"ID: {student['id'][:8].upper()}",
            qr_data     = student["id"],
            badge       = "BIBLIOTECÁRIO" if student.get("is_librarian") else student.get("turma", ""),
            color       = "#166534",
        )

        return jsonify({"image": img_b64, "filename": f"carteirinha-{student_id[:8]}.png"})
    except ImportError as e:
        return jsonify({"error": f"Pillow não instalado: {e}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Builder do cartão PNG ─────────────────────────────────────────────
def _build_card(entity_type, title, subtitle, field1, field2, field3,
                qr_data, badge="", color="#1a4f8a"):
    """
    Constrói um cartão PNG 600x260px com visual de carteirinha.
    Retorna string base64 "data:image/png;base64,..."
    """
    import qrcode as qr_lib
    from PIL import Image, ImageDraw, ImageFont
    import textwrap

    W, H = 600, 260
    MARGIN = 18

    bg_color     = (245, 247, 250)
    card_color   = (255, 255, 255)
    header_color = tuple(int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
    text_dark    = (17, 24, 39)
    text_muted   = (80, 92, 123)
    border_color = (216, 226, 241)

    img  = Image.new("RGB", (W, H), bg_color)
    draw = ImageDraw.Draw(img)

    # Card principal
    draw.rounded_rectangle([8, 8, W-8, H-8], radius=22, fill=card_color, outline=border_color, width=2)

    # Header
    draw.rounded_rectangle([14, 14, W-14, 72], radius=16, fill=header_color)
    draw.text((28, 24), "BIBLIOTECA NARCEU DE PAIVA FILHO", fill=(255, 255, 255), font=_load_font(18, bold=True))
    header_label = "CARTEIRINHA" if entity_type == "aluno" else "CARTÃO DE LIVRO"
    draw.text((28, 46), header_label, fill=(255, 255, 255), font=_load_font(12, bold=True))
    draw.rectangle([14, 72, W-14, 76], fill=(255, 255, 255))

    # QR Code
    chip_text = "narceu"
    chip_w    = draw.textlength(chip_text, font=_load_font(11, bold=True)) + 20
    chip_x    = W - chip_w - 24
    chip_y    = 24
    draw.rounded_rectangle([chip_x, chip_y, chip_x + chip_w, chip_y + 28], radius=14, fill=(255, 255, 255), outline=(255, 255, 255), width=0)
    draw.text((chip_x + 10, chip_y + 6), chip_text, fill=header_color, font=_load_font(11, bold=True))

    qr = qr_lib.QRCode(version=1, box_size=5, border=1)
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color=header_color, back_color="white").convert("RGB")
    qr_size = 146
    qr_img  = qr_img.resize((qr_size, qr_size), Image.LANCZOS)
    qr_x = W - qr_size - MARGIN - 4
    qr_y = 88
    img.paste(qr_img, (qr_x, qr_y))
    draw.rectangle([qr_x-3, qr_y-3, qr_x+qr_size+3, qr_y+qr_size+3], outline=border_color, width=2)
    qr_label = "ESCANEAR QR"
    label_w  = draw.textlength(qr_label, font=_load_font(11))
    draw.text((qr_x + (qr_size - label_w) / 2, qr_y + qr_size + 8), qr_label, fill=text_muted, font=_load_font(11))

    # Texto principal
    cx = 34
    cy = 90
    title_wrapped = textwrap.wrap(title, width=22)
    for line in title_wrapped[:3]:
        draw.text((cx, cy), line, fill=text_dark, font=_load_font(24, bold=True))
        cy += 34
    cy += 4
    draw.text((cx, cy), subtitle, fill=text_dark, font=_load_font(14, bold=False))
    cy += 28

    # Bloco de detalhes com fundo suave
    details_x = cx
    details_y = cy
    details_w = qr_x - details_x - 12

    info_blocks = []
    for field in [field1, field2, field3]:
        if field and ("".join(field.split(": ")[1:]).strip() if ": " in field else field).strip():
            label, _, value = field.partition(": ")
            wrapped = textwrap.wrap(value, width=28) or [""]
            info_blocks.append((label, wrapped))

    block_top_padding = 18
    block_spacing = 16
    line_height = 22
    details_h = max(118, block_top_padding + sum(line_height * (1 + len(wrapped)) + block_spacing for _, wrapped in info_blocks))

    draw.rounded_rectangle([details_x, details_y, details_x + details_w, details_y + details_h], radius=20, fill=(249, 250, 252), outline=border_color, width=1)

    # Badge / turma ou gênero
    if badge:
        badge_text = badge.upper()
        badge_w = draw.textlength(badge_text, font=_load_font(12, bold=True)) + 26
        badge_x = details_x + details_w - badge_w - 18
        badge_y = details_y + 18
        draw.rounded_rectangle([badge_x, badge_y, badge_x + badge_w, badge_y + 28], radius=14, fill=header_color)
        draw.text((badge_x + 13, badge_y + 6), badge_text, fill=(255, 255, 255), font=_load_font(12, bold=True))

    info_x = details_x + 18
    info_y = details_y + block_top_padding
    for label, wrapped_value in info_blocks:
        draw.text((info_x, info_y), label, fill=text_muted, font=_load_font(10, bold=True))
        info_y += line_height
        for line in wrapped_value:
            draw.text((info_x, info_y), line, fill=text_dark, font=_load_font(16, bold=False))
            info_y += line_height
        info_y += block_spacing

    footer_y = details_y + details_h + 18
    id_short = qr_data[:8].upper() if len(qr_data) >= 8 else qr_data
    draw.text((34, footer_y), f"ID: {id_short}", fill=text_muted, font=_load_font(11))
    draw.text((34, footer_y + 21), "Biblioteca Narceu de Paiva Filho — Carteirinha", fill=text_muted, font=_load_font(10))

    # Barra inferior contrastante
    draw.rectangle([0, H - 10, W, H], fill=header_color)

    buf = BytesIO()
    img.save(buf, format="PNG", dpi=(300, 300))
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


def _load_font(size, bold=False):
    from PIL import ImageFont
    try:
        if bold:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except Exception:
        return ImageFont.load_default()