"""
api/students.py
CRUD de alunos com sala_id + geração de QR automático no cadastro.
"""

from flask import Blueprint, request, jsonify
from utils import get_client, sb_exec, new_id
import csv, io

students_bp = Blueprint("students", __name__)


@students_bp.route("/", methods=["GET"])
def list_students():
    sb    = get_client()
    q     = request.args.get("q", "").strip().lower()
    cls   = request.args.get("class", "").strip()
    sala  = request.args.get("sala_id", "").strip()

    students = sb_exec(sb.table("alunos").select("*, salas(nome, codigo)").order("nome"))

    if q:
        students = [s for s in students
            if q in (s.get("nome") or "").lower()
            or q in (s.get("turma") or "").lower()
            or q in (s.get("carteirinha") or "").lower()
            or q in (s.get("id") or "").lower()
        ]
    if cls:
        students = [s for s in students if s.get("turma") == cls]
    if sala:
        students = [s for s in students if s.get("sala_id") == sala]

    # Flatten sala
    for s in students:
        sala_data = s.pop("salas", None) or {}
        s["sala_nome"]   = sala_data.get("nome", "")
        s["sala_codigo"] = sala_data.get("codigo", "")

    return jsonify(students)


@students_bp.route("/<student_id>", methods=["GET"])
def get_student(student_id):
    sb   = get_client()
    rows = sb_exec(sb.table("alunos").select("*, salas(nome, codigo)").eq("id", student_id))
    if not rows:
        rows = sb_exec(sb.table("alunos").select("*, salas(nome, codigo)").eq("carteirinha", student_id))
    if not rows:
        all_s = sb_exec(sb.table("alunos").select("*, salas(nome, codigo)"))
        rows  = [s for s in all_s if student_id.lower() in (s.get("nome") or "").lower()]
    if not rows:
        return jsonify({"error": "Aluno não encontrado"}), 404

    s         = rows[0]
    sala_data = s.pop("salas", None) or {}
    s["sala_nome"]   = sala_data.get("nome", "")
    s["sala_codigo"] = sala_data.get("codigo", "")
    return jsonify(s)


@students_bp.route("/", methods=["POST"])
def create_student():
    body = request.get_json(force=True) or {}
    if not body.get("nome") or not body.get("turma"):
        return jsonify({"error": "nome e turma são obrigatórios"}), 400

    sb         = get_client()
    student_id = new_id()
    payload    = {
        "id":          student_id,
        "nome":        body["nome"].strip(),
        "turma":       body["turma"].strip().upper(),
        "carteirinha": body.get("carteirinha", "") or "",
        "sala_id":     body.get("sala_id") or None,
    }

    rows   = sb_exec(sb.table("alunos").insert(payload))
    result = rows[0] if rows else payload

    # Gera QR Code automaticamente
    try:
        import qrcode as qr_lib, base64
        from io import BytesIO
        qr = qr_lib.QRCode(version=1, box_size=6, border=2)
        qr.add_data(student_id)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#166534", back_color="white")
        buf = BytesIO()
        img.save(buf, format="PNG")
        result["qr_code"] = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception:
        result["qr_code"] = None

    return jsonify(result), 201


@students_bp.route("/<student_id>", methods=["PUT"])
def update_student(student_id):
    body = request.get_json(force=True) or {}
    body.pop("id", None); body.pop("criado_em", None)
    body.pop("salas", None); body.pop("sala_nome", None); body.pop("sala_codigo", None)
    if body.get("turma"):
        body["turma"] = body["turma"].upper()

    sb   = get_client()
    rows = sb_exec(sb.table("alunos").update(body).eq("id", student_id))
    if not rows:
        return jsonify({"error": "Aluno não encontrado"}), 404
    return jsonify(rows[0])


@students_bp.route("/<student_id>", methods=["DELETE"])
def delete_student(student_id):
    sb     = get_client()
    ativos = sb_exec(sb.table("emprestimos").select("id").eq("aluno_id", student_id).is_("devolvido_em", "null"))
    if ativos:
        return jsonify({"error": "Aluno possui empréstimos ativos"}), 409
    sb_exec(sb.table("alunos").delete().eq("id", student_id))
    return jsonify({"success": True})


@students_bp.route("/import/csv", methods=["POST"])
def import_csv():
    sb = get_client()
    if "file" in request.files:
        raw = request.files["file"].read().decode("utf-8", errors="replace")
    else:
        raw = request.get_data(as_text=True)
    if not raw.strip():
        return jsonify({"error": "Arquivo vazio"}), 400

    sep    = ";" if ";" in raw.split("\n")[0] else ","
    reader = csv.DictReader(io.StringIO(raw), delimiter=sep)

    existing = {s.get("carteirinha", "") for s in sb_exec(sb.table("alunos").select("carteirinha")) if s.get("carteirinha")}
    added, skipped = 0, 0
    batch = []

    for row in reader:
        nome  = (row.get("nome") or row.get("Nome") or "").strip()
        turma = (row.get("turma") or row.get("Turma") or "").strip().upper()
        card  = (row.get("carteirinha") or row.get("matricula") or row.get("matrícula") or "").strip()
        sala  = (row.get("sala_id") or "").strip() or None

        if not nome or not turma: skipped += 1; continue
        if card and card in existing: skipped += 1; continue

        batch.append({"id": new_id(), "nome": nome, "turma": turma, "carteirinha": card, "sala_id": sala})
        if card: existing.add(card)
        added += 1

    if batch:
        try:
            sb_exec(sb.table("alunos").insert(batch))
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return jsonify({"added": added, "skipped": skipped})
