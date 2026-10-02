"""api/students.py — CRUD de alunos com fallback JSON local."""
from flask import Blueprint, request, jsonify
from pathlib import Path
import csv, io
from utils import get_client, sb_exec, new_id, today_str
from api._helpers import read_json, write_json, table_ok, has_deleted_at, is_offline_error

students_bp = Blueprint("students", __name__)
DATA_DIR   = Path(__file__).resolve().parent.parent / "data"
ALUNOS_FILE = DATA_DIR / "alunos.json"
ROOMS_FILE  = DATA_DIR / "salas.json"
LOANS_FILE  = DATA_DIR / "emprestimos.json"


@students_bp.route("/", methods=["GET"])
def list_students():
    sb   = get_client()
    q    = request.args.get("q","").strip().lower()
    cls  = request.args.get("class","").strip()
    sala = request.args.get("sala_id","").strip()

    if table_ok(sb, "alunos"):
        try:
            query = sb.table("alunos").select("*, salas(nome,codigo)").order("nome")
            if has_deleted_at(sb, "alunos"): query = query.is_("deleted_at","null")
            try:    students = sb_exec(query)
            except: students = sb_exec(sb.table("alunos").select("*").order("nome"))
        except: students = read_json(ALUNOS_FILE)
    else:
        students = [s for s in read_json(ALUNOS_FILE) if not s.get("deleted_at")]

    if q:    students = [s for s in students if q in (s.get("nome","")).lower() or q in (s.get("turma","")).lower() or q in (s.get("carteirinha","")).lower()]
    if cls:  students = [s for s in students if s.get("turma")==cls]
    if sala: students = [s for s in students if s.get("sala_id")==sala]

    rmap = {r["id"]: r for r in read_json(ROOMS_FILE)}
    for s in students:
        sala_data = s.pop("salas", None) or rmap.get(s.get("sala_id"),{})
        s["sala_nome"] = sala_data.get("nome",""); s["sala_codigo"] = sala_data.get("codigo","")
        s["is_librarian"] = bool(s.get("is_librarian", False))
    return jsonify(students)


@students_bp.route("/<student_id>", methods=["GET"])
def get_student(student_id):
    sb = get_client()
    rows = []
    if table_ok(sb, "alunos"):
        try:
            rows = sb_exec(sb.table("alunos").select("*, salas(nome,codigo)").eq("id", student_id))
            if not rows: rows = sb_exec(sb.table("alunos").select("*, salas(nome,codigo)").eq("carteirinha", student_id))
        except:
            rows = sb_exec(sb.table("alunos").select("*").eq("id", student_id))
    if not rows:
        all_s = read_json(ALUNOS_FILE)
        rows  = [s for s in all_s if s.get("id")==student_id or s.get("carteirinha")==student_id]
    if not rows: return jsonify({"error": "Aluno não encontrado"}), 404
    s = rows[0]; sala_data = s.pop("salas",None) or {}
    rmap = {r["id"]:r for r in read_json(ROOMS_FILE)}
    if not sala_data: sala_data = rmap.get(s.get("sala_id"),{})
    s["sala_nome"] = sala_data.get("nome",""); s["sala_codigo"] = sala_data.get("codigo","")
    s["is_librarian"] = bool(s.get("is_librarian", False))
    return jsonify(s)


@students_bp.route("/", methods=["POST"])
def create_student():
    body = request.get_json(force=True) or {}
    if not body.get("nome") or not body.get("turma"):
        return jsonify({"error": "nome e turma são obrigatórios"}), 400
    sb = get_client()
    sid  = new_id()
    sala = body.get("sala_id") or None
    if sala:
        try:
            if not sb_exec(sb.table("salas").select("id").eq("id",sala)): sala=None
        except:
            if not any(r.get("id")==sala for r in read_json(ROOMS_FILE)): sala=None
    card = (body.get("carteirinha") or "").strip() or sid[:8]
    payload = {"id":sid,"nome":body["nome"].strip(),"turma":body["turma"].strip().upper(),"carteirinha":card}
    if sala: payload["sala_id"] = sala

    if table_ok(sb, "alunos"):
        try: rows = sb_exec(sb.table("alunos").insert(payload))
        except Exception as e:
            m = str(e).lower()
            if "sala_id" in m and "could not find" in m:
                payload.pop("sala_id", None)
                rows = sb_exec(sb.table("alunos").insert(payload))
            elif "duplicate key" in m or "unique constraint" in m:
                existing = [s for s in read_json(ALUNOS_FILE) if s.get("carteirinha") == card]
                if existing:
                    rows = [existing[0]]
                else:
                    return jsonify({"error":"Carteirinha já cadastrada."}),409
            elif is_offline_error(e):
                s = read_json(ALUNOS_FILE)
                s.append(payload)
                write_json(ALUNOS_FILE, s)
                rows = [payload]
            else:
                raise
    else:
        all_s = read_json(ALUNOS_FILE)
        existing = [s for s in all_s if s.get("carteirinha") == card]
        if existing:
            rows = [existing[0]]
        else:
            all_s.append(payload)
            write_json(ALUNOS_FILE, all_s)
            rows = [payload]

    result = rows[0] if rows else payload
    try:
        import qrcode as ql, base64; from io import BytesIO
        qr=ql.QRCode(version=1,box_size=6,border=2); qr.add_data(sid); qr.make(fit=True)
        img=qr.make_image(fill_color="#166534",back_color="white")
        buf=BytesIO(); img.save(buf,format="PNG")
        result["qr_code"]="data:image/png;base64,"+base64.b64encode(buf.getvalue()).decode()
    except: result["qr_code"]=None
    return jsonify(result), 201


@students_bp.route("/<student_id>", methods=["PUT"])
def update_student(student_id):
    body = request.get_json(force=True) or {}
    for k in ["id","criado_em","salas","sala_nome","sala_codigo"]: body.pop(k,None)
    if body.get("turma"): body["turma"] = body["turma"].upper()
    sb = get_client()
    if table_ok(sb, "alunos"):
        try: rows = sb_exec(sb.table("alunos").update(body).eq("id",student_id))
        except Exception as e:
            m=str(e).lower()
            if "sala_id" in m and "could not find" in m: body.pop("sala_id",None); rows=sb_exec(sb.table("alunos").update(body).eq("id",student_id))
            elif "duplicate key" in m: return jsonify({"error":"Carteirinha já cadastrada."}),409
            elif is_offline_error(e):
                s=read_json(ALUNOS_FILE); rows=[]
                for st in s:
                    if st.get("id")==student_id: st.update(body); rows=[st]; break
                write_json(ALUNOS_FILE,s)
            else: raise
        if not rows: return jsonify({"error":"Aluno não encontrado"}),404
        return jsonify(rows[0])
    s=read_json(ALUNOS_FILE)
    for st in s:
        if st.get("id")==student_id: st.update(body); write_json(ALUNOS_FILE,s); return jsonify(st)
    return jsonify({"error":"Aluno não encontrado"}),404


@students_bp.route("/<student_id>", methods=["DELETE"])
def delete_student(student_id):
    sb = get_client()
    try: ativos = sb_exec(sb.table("emprestimos").select("id").eq("aluno_id",student_id).is_("devolvido_em","null"))
    except: ativos = [l for l in read_json(LOANS_FILE) if l.get("aluno_id")==student_id and not l.get("devolvido_em")]
    if ativos: return jsonify({"error":"Aluno possui empréstimos ativos"}),409
    if table_ok(sb,"alunos"):
        try:
            if has_deleted_at(sb,"alunos"): sb_exec(sb.table("alunos").update({"deleted_at":today_str()}).eq("id",student_id))
            else: sb_exec(sb.table("alunos").delete().eq("id",student_id))
            return jsonify({"success":True})
        except: pass
    s=read_json(ALUNOS_FILE)
    for st in s:
        if st.get("id")==student_id: st["deleted_at"]=today_str(); write_json(ALUNOS_FILE,s); return jsonify({"success":True})
    return jsonify({"error":"Aluno não encontrado"}),404


@students_bp.route("/<student_id>/access", methods=["PATCH", "POST"])
def toggle_librarian_access(student_id):
    """Concede ou revoga o título de Bibliotecário para um aluno (acesso ao painel via carteirinha)."""
    body = request.get_json(force=True) or {}
    grant = bool(body.get("is_librarian", True))
    upd = {"is_librarian": grant}
    sb = get_client()
    if table_ok(sb, "alunos"):
        try:
            rows = sb_exec(sb.table("alunos").update(upd).eq("id", student_id))
            if rows: return jsonify(rows[0])
        except Exception as e:
            m = str(e).lower()
            if not is_offline_error(e) and "is_librarian" not in m:
                raise
    # Fallback: arquivo local JSON
    s = read_json(ALUNOS_FILE)
    for st in s:
        if st.get("id") == student_id:
            st["is_librarian"] = grant
            write_json(ALUNOS_FILE, s)
            return jsonify(st)
    return jsonify({"error": "Aluno não encontrado"}), 404


@students_bp.route("/import/csv", methods=["POST"])
def import_csv():
    sb = get_client()
    raw = (request.files["file"].read().decode("utf-8","replace") if "file" in request.files else request.get_data(as_text=True))
    if not raw.strip(): return jsonify({"error":"Arquivo vazio"}),400
    sep = ";" if ";" in raw.split("\n")[0] else ","
    reader = csv.DictReader(io.StringIO(raw), delimiter=sep)
    try: rooms = sb_exec(sb.table("salas").select("id,codigo,nome"))
    except: rooms = read_json(ROOMS_FILE)
    ridx = {r["id"]:r for r in rooms}
    ridx.update({r["codigo"]:r for r in rooms if r.get("codigo")})
    ridx.update({r["nome"]:r for r in rooms if r.get("nome")})
    try: existing = {s.get("carteirinha","") for s in sb_exec(sb.table("alunos").select("carteirinha")) if s.get("carteirinha")}
    except: existing = {s.get("carteirinha","") for s in read_json(ALUNOS_FILE) if s.get("carteirinha")}
    added=0; skipped=0; batch=[]
    for row in reader:
        nome  = (row.get("nome") or row.get("Nome") or "").strip()
        turma = (row.get("turma") or row.get("Turma") or "").strip().upper()
        card  = (row.get("carteirinha") or row.get("matricula") or "").strip()
        sala  = (row.get("sala_id") or "").strip() or None
        if sala and sala in ridx: sala = ridx[sala]["id"]
        else: sala = None
        if not nome or not turma: skipped+=1; continue
        if card and card in existing: skipped+=1; continue
        batch.append({"id":new_id(),"nome":nome,"turma":turma,"carteirinha":card,"sala_id":sala})
        if card: existing.add(card)
        added+=1
    if batch:
        if table_ok(sb,"alunos"):
            try: sb_exec(sb.table("alunos").insert(batch))
            except: all_s=read_json(ALUNOS_FILE); all_s.extend(batch); write_json(ALUNOS_FILE,all_s)
        else:
            all_s=read_json(ALUNOS_FILE); all_s.extend(batch); write_json(ALUNOS_FILE,all_s)
    return jsonify({"added":added,"skipped":skipped})