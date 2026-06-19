"""api/reports.py — Relatórios e exportações com fallback JSON local."""
from flask import Blueprint, jsonify, request, Response
from pathlib import Path
import csv, io, json
from utils import get_client, sb_exec, loan_status, days_until, today_str
from api._helpers import read_json, is_offline_error

reports_bp  = Blueprint("reports", __name__)
DATA_DIR    = Path(__file__).resolve().parent.parent / "data"
BOOKS_FILE  = DATA_DIR / "livros.json"
ALUNOS_FILE = DATA_DIR / "alunos.json"
LOANS_FILE  = DATA_DIR / "emprestimos.json"


def _fetch_all(sb):
    try:    books = sb_exec(sb.table("livros").select("*"))
    except: books = read_json(BOOKS_FILE)
    try:    students = sb_exec(sb.table("alunos").select("*"))
    except: students = read_json(ALUNOS_FILE)
    try:    loans = sb_exec(sb.table("emprestimos").select("*"))
    except: loans = read_json(LOANS_FILE)
    return books, students, loans


@reports_bp.route("/chart-summary", methods=["GET"])
def chart_summary():
    _, _, loans = _fetch_all(get_client())
    active=sum(1 for l in loans if loan_status(l)=="active")
    overdue=sum(1 for l in loans if loan_status(l)=="overdue")
    returned=sum(1 for l in loans if loan_status(l)=="returned")
    return jsonify({"labels":["Emprestados","Atrasados","Devolvidos"],"values":[active,overdue,returned],"colors":["#f59e0b","#ef4444","#22c55e"]})


@reports_bp.route("/top-books", methods=["GET"])
def top_books():
    limit = int(request.args.get("limit",8))
    books,_,loans = _fetch_all(get_client())
    counts={}
    for l in loans: counts[l["livro_id"]] = counts.get(l["livro_id"],0)+1
    bmap = {b["id"]:b for b in books}
    result=[{"titulo":bmap[bid]["titulo"],"autor":bmap[bid]["autor"],"area":bmap[bid].get("area",""),"total":c}
            for bid,c in sorted(counts.items(),key=lambda x:x[1],reverse=True)[:limit] if bid in bmap]
    return jsonify(result)


@reports_bp.route("/by-class", methods=["GET"])
def by_class():
    _,students,loans = _fetch_all(get_client())
    smap = {s["id"]:s.get("turma","?") for s in students}
    cc={}
    for l in loans:
        cls=smap.get(l["aluno_id"],"?")
        if cls not in cc: cc[cls]={"active":0,"overdue":0,"returned":0}
        cc[cls][loan_status(l)]+=1
    labels=sorted(cc.keys())
    return jsonify({"labels":labels,"active":[cc[c]["active"] for c in labels],"overdue":[cc[c]["overdue"] for c in labels],"returned":[cc[c]["returned"] for c in labels]})


@reports_bp.route("/monthly", methods=["GET"])
def get_monthly():
    sb = get_client()
    try: rows = sb_exec(sb.table("relatorios_mensais").select("*").order("mes_ano",desc=True))
    except: rows=[]
    return jsonify(rows)


@reports_bp.route("/monthly/generate", methods=["POST"])
def generate_monthly():
    from datetime import date
    sb = get_client()
    body = request.get_json(force=True) or {}
    mes_ano = body.get("mes_ano") or date.today().strftime("%Y-%m")
    books,students,loans = _fetch_all(sb)
    mes_loans = [l for l in loans if (l.get("data_emprestimo",""))[:7]==mes_ano]
    counts={}
    for l in mes_loans: counts[l["livro_id"]] = counts.get(l["livro_id"],0)+1
    bmap={b["id"]:b for b in books}
    top_livros=[{"titulo":bmap[bid]["titulo"],"total":c} for bid,c in sorted(counts.items(),key=lambda x:x[1],reverse=True)[:5] if bid in bmap]
    smap={s["id"]:s.get("turma","?") for s in students}
    tcnt={}
    for l in mes_loans: t=smap.get(l["aluno_id"],"?"); tcnt[t]=tcnt.get(t,0)+1
    payload={"mes_ano":mes_ano,"total_emprestimos":len(mes_loans),
             "total_devolucoes":sum(1 for l in loans if (l.get("devolvido_em",""))[:7]==mes_ano),
             "total_atrasos":sum(1 for l in mes_loans if loan_status(l)=="overdue"),
             "livros_mais_lidos":top_livros,
             "turmas_mais_ativas":[{"turma":t,"total":c} for t,c in sorted(tcnt.items(),key=lambda x:x[1],reverse=True)[:5]],
             "gerado_em":today_str()}
    try:
        rows=sb_exec(sb.table("relatorios_mensais").upsert(payload,on_conflict="mes_ano"))
        return jsonify(rows[0] if rows else payload),201
    except: return jsonify(payload),201


def _csv_resp(rows, filename):
    out=io.StringIO()
    csv.writer(out,quoting=csv.QUOTE_ALL).writerows(rows)
    return Response("\ufeff"+out.getvalue(),mimetype="text/csv; charset=utf-8",
                    headers={"Content-Disposition":f"attachment; filename={filename}"})


@reports_bp.route("/export/overdue", methods=["GET"])
def export_overdue():
    books,students,loans = _fetch_all(get_client())
    bmap={b["id"]:b for b in books}; smap={s["id"]:s for s in students}
    rows=[["Aluno","Turma","Livro","Exemplar","Emprestado em","Vencimento","Dias Atraso"]]
    for l in loans:
        if loan_status(l)!="overdue": continue
        b=bmap.get(l["livro_id"],{}); s=smap.get(l["aluno_id"],{})
        rows.append([s.get("nome",""),s.get("turma",""),b.get("titulo",""),l.get("exemplar",""),
                     l.get("data_emprestimo",""),l.get("data_devolucao_prevista",""),abs(days_until(l["data_devolucao_prevista"]))])
    return _csv_resp(rows,"emprestimos-atrasados.csv")


@reports_bp.route("/export/all", methods=["GET"])
def export_all():
    books,students,loans = _fetch_all(get_client())
    bmap={b["id"]:b for b in books}; smap={s["id"]:s for s in students}
    rows=[["Aluno","Turma","Livro","Exemplar","Emprestado em","Devolução prevista","Devolvido em","Status"]]
    for l in loans:
        b=bmap.get(l["livro_id"],{}); s=smap.get(l["aluno_id"],{})
        rows.append([s.get("nome",""),s.get("turma",""),b.get("titulo",""),l.get("exemplar",""),
                     l.get("data_emprestimo",""),l.get("data_devolucao_prevista",""),l.get("devolvido_em","") or "",loan_status(l)])
    return _csv_resp(rows,"historico-completo.csv")