"""
scanner/routes.py
QR Code: geração, decodificação e geração de cartão imprimível (PDF-like PNG).
- /api/qr/decode      → decodifica imagem base64 e resolve o ID contra o banco
- /api/qr/generate    → gera QR Code PNG em base64
- /api/qr/card/book/<id>    → retorna imagem PNG do cartão do livro + QR
- /api/qr/card/student/<id> → retorna imagem PNG do cartão do aluno + QR
"""

import base64
import threading
import time
from io import BytesIO

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
        import cv2, numpy as np
        from PIL import Image
        from pyzbar import pyzbar
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
        frame   = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        decoded = pyzbar.decode(frame)

        if not decoded:
            return jsonify({"codes": [], "primary": None, "type": "unknown"})

        primary = decoded[0].data.decode("utf-8", errors="replace")

        # Resolve contra o banco
        resolved = _resolve_qr(primary)
        return jsonify({
            "codes":   [d.data.decode("utf-8", errors="replace") for d in decoded],
            "primary": primary,
            **resolved,
        })

    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


def _resolve_qr(code: str) -> dict:
    """Tenta encontrar o código como ID de livro ou aluno."""
    try:
        from utils import get_client, sb_exec
        sb = get_client()

        # Tenta como livro
        books = sb_exec(sb.table("livros").select("*").eq("id", code))
        if not books:
            books = sb_exec(sb.table("livros").select("*").eq("isbn", code))
        if books:
            return {"type": "book", "data": books[0]}

        # Tenta como aluno
        students = sb_exec(sb.table("alunos").select("*").eq("id", code))
        if not students:
            students = sb_exec(sb.table("alunos").select("*").eq("carteirinha", code))
        if students:
            return {"type": "student", "data": students[0]}

        return {"type": "unknown", "data": None}
    except Exception:
        return {"type": "unknown", "data": None}


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
        from utils import get_client, sb_exec
        import qrcode as qr_lib
        from PIL import Image, ImageDraw, ImageFont
        import textwrap

        sb    = get_client()
        books = sb_exec(sb.table("livros").select("*").eq("id", book_id))
        if not books:
            return jsonify({"error": "Livro não encontrado"}), 404
        book = books[0]

        img_b64 = _build_card(
            entity_type = "livro",
            title       = book.get("titulo", ""),
            subtitle    = book.get("autor", ""),
            field1      = f"Área: {book.get('area', '')}",
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
        from utils import get_client, sb_exec

        sb       = get_client()
        students = sb_exec(sb.table("alunos").select("*").eq("id", student_id))
        if not students:
            return jsonify({"error": "Aluno não encontrado"}), 404
        student = students[0]

        # Busca sala
        sala_nome = ""
        if student.get("sala_id"):
            salas = sb_exec(sb.table("salas").select("nome").eq("id", student["sala_id"]))
            if salas:
                sala_nome = salas[0]["nome"]

        img_b64 = _build_card(
            entity_type = "aluno",
            title       = student.get("nome", ""),
            subtitle    = f"Turma: {student.get('turma', '')}",
            field1      = f"Sala: {sala_nome or 'Não atribuída'}",
            field2      = f"Carteirinha: {student.get('carteirinha', '') or 'N/A'}",
            field3      = f"ID: {student['id'][:8].upper()}",
            qr_data     = student["id"],
            badge       = student.get("turma", ""),
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
    Constrói um cartão PNG 600x220px profissional com QR Code embutido.
    Retorna string base64 "data:image/png;base64,..."
    """
    import qrcode as qr_lib
    from PIL import Image, ImageDraw, ImageFont
    import textwrap

    W, H = 600, 220
    MARGIN = 16

    # Cores
    bg_color     = (255, 255, 255)
    header_color = tuple(int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
    text_dark    = (15, 23, 42)
    text_muted   = (100, 116, 139)
    border_color = (226, 232, 240)

    img  = Image.new("RGB", (W, H), bg_color)
    draw = ImageDraw.Draw(img)

    # Borda
    draw.rectangle([0, 0, W-1, H-1], outline=border_color, width=2)

    # Faixa lateral colorida
    draw.rectangle([0, 0, 8, H], fill=header_color)

    # Header colorido topo
    draw.rectangle([0, 0, W, 48], fill=header_color)

    # Texto do tipo no header
    type_label = "📚 BIBLIOTECA IFES" if entity_type == "livro" else "🎓 BIBLIOTECA IFES"
    try:
        font_header = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 13)
        font_title  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        font_sub    = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        font_field  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
        font_small  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 9)
    except Exception:
        font_header = ImageFont.load_default()
        font_title  = font_header
        font_sub    = font_header
        font_field  = font_header
        font_small  = font_header

    draw.text((20, 14), type_label, fill=(255, 255, 255), font=font_header)

    # Tipo do cartão (direita do header)
    card_label = "FICHA DO LIVRO" if entity_type == "livro" else "CARTEIRINHA DO ALUNO"
    draw.text((W - 160, 14), card_label, fill=(255, 255, 255, 180), font=font_small)

    # Gera QR Code
    qr     = qr_lib.QRCode(version=1, box_size=5, border=1)
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color=color, back_color="white").convert("RGB")
    qr_size = 140
    qr_img  = qr_img.resize((qr_size, qr_size), Image.LANCZOS)

    # Posição QR (direita, centralizado verticalmente na área de conteúdo)
    qr_x = W - qr_size - MARGIN - 8
    qr_y = 48 + (H - 48 - qr_size) // 2
    img.paste(qr_img, (qr_x, qr_y))

    # Borda ao redor do QR
    draw.rectangle(
        [qr_x - 2, qr_y - 2, qr_x + qr_size + 2, qr_y + qr_size + 2],
        outline=border_color, width=1
    )

    # Texto "Escaneie" abaixo do QR
    draw.text((qr_x + 18, qr_y + qr_size + 4), "Escaneie o QR Code", fill=text_muted, font=font_small)

    # Conteúdo textual (esquerda)
    cx = 20
    cy = 58

    # Título (nome do livro / aluno)
    title_wrapped = textwrap.wrap(title, width=32)
    for line in title_wrapped[:2]:
        draw.text((cx, cy), line, fill=text_dark, font=font_title)
        cy += 22

    cy += 2

    # Subtítulo
    draw.text((cx, cy), subtitle, fill=text_muted, font=font_sub)
    cy += 18

    # Linha divisória
    draw.line([(cx, cy), (qr_x - 16, cy)], fill=border_color, width=1)
    cy += 10

    # Campos
    for field in [field1, field2, field3]:
        if field and field.split(": ")[1] if ": " in field else field:
            label, _, value = field.partition(": ")
            draw.text((cx, cy), f"{label}:", fill=text_muted, font=font_small)
            draw.text((cx + 80, cy), value, fill=text_dark, font=font_field)
            cy += 16

    # Badge / turma
    if badge:
        badge_x, badge_y = cx, H - 28
        badge_w = len(badge) * 7 + 16
        draw.rounded_rectangle(
            [badge_x, badge_y, badge_x + badge_w, badge_y + 18],
            radius=4, fill=header_color
        )
        draw.text((badge_x + 8, badge_y + 3), badge, fill=(255, 255, 255), font=font_small)

    # ID no rodapé
    id_short = qr_data[:8].upper() if len(qr_data) >= 8 else qr_data
    draw.text((cx, H - 14), f"ID: {id_short}", fill=text_muted, font=font_small)

    # Linha de corte pontilhada no rodapé
    for x in range(0, W, 8):
        draw.point((x, H - 1), fill=border_color)

    # Converte para base64
    buf = BytesIO()
    img.save(buf, format="PNG", dpi=(300, 300))
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"
