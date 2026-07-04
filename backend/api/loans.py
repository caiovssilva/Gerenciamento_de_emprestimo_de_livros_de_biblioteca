"""api/loans.py — Empréstimos e devoluções com fallback JSON local."""
from flask import Blueprint, request, jsonify
from pathlib import Path
from utils import get_client, sb_exec, new_id, today_str, add_days, loan_status
from api._helpers import read_json, write_json, table_ok, is_offline_error

loans_bp    = Blueprint("loans", __name__)
DATA_DIR    = Path(__file__).resolve().parent.parent / "data"
LOANS_FILE  = DATA_DIR / "emprestimos.json"
BOOKS_FILE  = DATA_DIR / "livros.json"
ALUNOS_FILE = DATA_DIR / "alunos.json"


def _available_copies(sb, book_id, total, exemplar_ids=None):
    try:
        rows = sb_exec(sb.table("emprestimos").select("exemplar","exemplar_id").eq("livro_id",book_id).is_("devolvido_em","null"))
    except:
        rows = [l for l in read_json(LOANS_FILE) if l.get("livro_id")==book_id and not l.get("devolvido_em")]

    usados_codigos = {str(r.get("exemplar", "")).strip() for r in rows if str(r.get("exemplar", "")).strip()}
    usados_ids = {str(r.get("exemplar_id", "")).strip() for r in rows if str(r.get("exemplar_id", "")).strip()}

    if exemplar_ids:
        return [
            {"code": str(idx + 1).zfill(3), "id": exemplar_id}
            for idx, exemplar_id in enumerate(exemplar_ids)
            if str(exemplar_id) not in usados_ids and str(idx + 1).zfill(3) not in usados_codigos
        ]

    return [
        {"code": str(i + 1).zfill(3), "id": f"{book_id}-{str(i + 1).zfill(3)}"}
        for i in range(max(1, int(total)))
        if str(i + 1).zfill(3) not in usados_codigos
    ]


def _find_student_by_ref(sb, student_ref):
    if not student_ref:
        return None
    student_ref = str(student_ref).strip()
    if not student_ref:
        return None

    try:
        rows = sb_exec(sb.table("alunos").select("id,carteirinha,qr_id").eq("id", student_ref))
        if rows:
            return rows[0]
    except Exception:
        rows = []

    try:
        rows = sb_exec(sb.table("alunos").select("id,carteirinha,qr_id").eq("carteirinha", student_ref))
        if rows:
            return rows[0]
    except Exception:
        rows = []

    try:
        rows = sb_exec(sb.table("alunos").select("id,carteirinha,qr_id").eq("qr_id", student_ref))
        if rows:
            return rows[0]
    except Exception:
        rows = []

    local_students = [s for s in read_json(ALUNOS_FILE) if str(s.get("id", "")) == student_ref or str(s.get("carteirinha", "")) == student_ref or str(s.get("qr_id", "")) == student_ref]
    return local_students[0] if local_students else None


@loans_bp.route("/", methods=["GET"])
def list_loans():
    sb     = get_client()
    status = request.args.get("status","")
    try:    loans = sb_exec(sb.table("emprestimos").select("*").order("data_emprestimo",desc=True))
    except: loans = sorted(read_json(LOANS_FILE), key=lambda l: l.get("data_emprestimo",""), reverse=True)
    if status in ("active","overdue","returned"):
        loans = [l for l in loans if loan_status(l)==status]
    return jsonify(loans)


@loans_bp.route("/<loan_id>", methods=["GET"])
def get_loan(loan_id):
    sb = get_client()
    try:    rows = sb_exec(sb.table("emprestimos").select("*").eq("id",loan_id))
    except: rows = [l for l in read_json(LOANS_FILE) if l.get("id")==loan_id]
    if not rows: return jsonify({"error":"Empréstimo não encontrado"}),404
    return jsonify(rows[0])


@loans_bp.route("/", methods=["POST"])
def create_loan():
    body = request.get_json(force=True) or {}
    book_id = body.get("livro_id"); student_id = body.get("aluno_id")
    try: days = max(1, int(body.get("dias",7)))
    except: days = 7
    if not book_id or not student_id:
        return jsonify({"error":"livro_id e aluno_id são obrigatórios"}),400
    sb = get_client()
    try:    books = sb_exec(sb.table("livros").select("*").eq("id",book_id))
    except: books = [b for b in read_json(BOOKS_FILE) if b.get("id")==book_id]
    if not books: return jsonify({"error":"Livro não encontrado"}),404
    avail = _available_copies(sb, book_id, books[0].get("exemplares", 1), books[0].get("exemplares_ids"))
    if not avail: return jsonify({"error":"Nenhum exemplar disponível no momento"}),409
    try:    aluno = sb_exec(sb.table("alunos").select("id").eq("id",student_id))
    except: aluno = [a for a in read_json(ALUNOS_FILE) if a.get("id")==student_id]
    if not aluno: return jsonify({"error":"Aluno não encontrado"}),404
    dt = body.get("data_emprestimo") or today_str()
    exemplar_info = avail[0]
    payload = {"id":new_id(),"livro_id":book_id,"aluno_id":student_id,"exemplar":exemplar_info["code"],"exemplar_id":exemplar_info["id"],
               "data_emprestimo":dt,"data_devolucao_prevista":add_days(dt,days),
               "devolvido_em":None,"observacao":body.get("observacao",""),"criado_por":body.get("criado_por","system")}
    try:    rows = sb_exec(sb.table("emprestimos").insert(payload))
    except Exception as e:
        m=str(e).lower()
        if is_offline_error(e): ls=read_json(LOANS_FILE); ls.append(payload); write_json(LOANS_FILE,ls); return jsonify(payload),201
        if "criado_por" in m or "observacao" in m:
            payload.pop("criado_por",None); payload.pop("observacao",None)
            rows=sb_exec(sb.table("emprestimos").insert(payload))
        else: raise
    return jsonify(rows[0] if rows else payload), 201


@loans_bp.route("/<loan_id>/renew", methods=["POST"])
def renew_loan(loan_id):
    """Renova um empréstimo ativo, estendendo a data de devolução prevista."""
    body = request.get_json(force=True) or {}
    try: days = max(1, int(body.get("dias", 7)))
    except: days = 7
    sb = get_client()
    try:    loans = sb_exec(sb.table("emprestimos").select("*").eq("id",loan_id))
    except: loans = [l for l in read_json(LOANS_FILE) if l.get("id")==loan_id]
    if not loans: return jsonify({"error":"Empréstimo não encontrado"}),404
    loan = loans[0]
    if loan.get("devolvido_em"): return jsonify({"error":"Empréstimo já foi devolvido — não é possível renovar"}),409

    base = loan.get("data_devolucao_prevista") or today_str()
    nova_data = add_days(base, days)
    renov_anterior = int(loan.get("renovacoes", 0) or 0)
    upd = {"data_devolucao_prevista": nova_data, "renovacoes": renov_anterior + 1}

    try:    rows = sb_exec(sb.table("emprestimos").update(upd).eq("id",loan_id))
    except Exception as e:
        m=str(e).lower()
        if is_offline_error(e):
            ls=read_json(LOANS_FILE); res=None
            for l in ls:
                if l.get("id")==loan_id: l.update(upd); res=l; break
            write_json(LOANS_FILE,ls); return jsonify(res or {**loan, **upd})
        if "renovacoes" in m:
            upd.pop("renovacoes",None); rows=sb_exec(sb.table("emprestimos").update(upd).eq("id",loan_id))
        else: raise
    return jsonify(rows[0] if rows else {**loan, **upd})


@loans_bp.route("/<loan_id>/return", methods=["POST"])
def return_loan(loan_id):
    body = request.get_json(force=True) or {}
    sb   = get_client()
    try:    loans = sb_exec(sb.table("emprestimos").select("*").eq("id",loan_id))
    except: loans = [l for l in read_json(LOANS_FILE) if l.get("id")==loan_id]
    if not loans: return jsonify({"error":"Empréstimo não encontrado"}),404
    if loans[0].get("devolvido_em"): return jsonify({"error":"Empréstimo já foi devolvido"}),409

    student_ref = body.get("student_id") or body.get("student_qr") or body.get("student_card") or body.get("carteirinha")
    if student_ref:
        student = _find_student_by_ref(sb, student_ref)
        if not student:
            return jsonify({"error":"Aluno não encontrado"}),404
        if str(student.get("id", "")) != str(loans[0].get("aluno_id", "")):
            return jsonify({"error":"Este exemplar pertence a outro aluno."}),403

    upd = {"devolvido_em": body.get("devolvido_em") or today_str(), "observacao": body.get("observacao","") or ""}
    try:    rows = sb_exec(sb.table("emprestimos").update(upd).eq("id",loan_id))
    except Exception as e:
        m=str(e).lower()
        if is_offline_error(e):
            ls=read_json(LOANS_FILE); res=None
            for l in ls:
                if l.get("id")==loan_id: l.update(upd); res=l; break
            write_json(LOANS_FILE,ls); return jsonify(res or upd)
        if "observacao" in m: upd.pop("observacao",None); rows=sb_exec(sb.table("emprestimos").update(upd).eq("id",loan_id))
        else: raise
    return jsonify(rows[0] if rows else upd)