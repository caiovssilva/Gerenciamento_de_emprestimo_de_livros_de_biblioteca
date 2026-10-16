import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app as app_module
import api.reports as reports_module


def test_report_data_and_csv_remove_duplicate_records(monkeypatch):
    loan = {
        "id": "l1",
        "livro_id": "b1",
        "aluno_id": "s1",
        "exemplar": "001",
        "data_emprestimo": "2026-06-01",
        "data_devolucao_prevista": "2026-06-08",
        "devolvido_em": None,
    }
    monkeypatch.setattr(reports_module, "get_client", lambda: None)
    monkeypatch.setattr(
        reports_module,
        "_fetch_all",
        lambda _sb: (
            [{"id": "b1", "titulo": "Duna", "autor": "Frank Herbert", "genero": "Ficção"}],
            [{"id": "s1", "nome": "Ana", "turma": "INFO3A"}],
            [loan, dict(loan)],
        ),
    )
    monkeypatch.setattr(reports_module, "loan_status", lambda _loan: "active")

    with app_module.app.test_client() as client:
        data_response = client.get("/api/reports/data")
        csv_response = client.get("/api/reports/export/all")

    assert data_response.status_code == 200
    reports = {report["id"]: report for report in data_response.get_json()}
    assert reports["all"]["rows"][1][0:4] == ["Ana", "INFO3A", "Duna", "001"]
    assert len(reports["all"]["rows"]) == 2
    assert reports["books"]["rows"][-1] == ["Duna", "Frank Herbert", "Ficção", 1]
    assert csv_response.status_code == 200
    assert csv_response.get_data(as_text=True).count('"Ana"') == 1


def test_student_directory_export_includes_students_without_loans_and_room_details(monkeypatch):
    monkeypatch.setattr(reports_module, "get_client", lambda: None)
    monkeypatch.setattr(reports_module, "_fetch_all", lambda _sb: (
        [],
        [
            {"id": "s1", "nome": "Bia", "carteirinha": "CARD-2", "turma": "INFO2", "sala_id": "r1"},
            {"id": "s2", "nome": "Ana", "carteirinha": "CARD-1", "turma": "INFO1", "is_librarian": True},
            {"id": "s3", "nome": "Removido", "deleted_at": "2026-01-01"},
        ],
        [{
            "id": "l1",
            "livro_id": "b1",
            "aluno_id": "s1",
            "exemplar": "001",
            "data_emprestimo": "2026-06-01",
            "data_devolucao_prevista": "2026-06-08",
            "devolvido_em": None,
        }],
    ))
    monkeypatch.setattr(reports_module, "loan_status", lambda loan: "overdue" if loan.get("id") == "l1" else "active")
    monkeypatch.setattr(
        reports_module,
        "read_json",
        lambda path: [{"id": "r1", "nome": "Sala 1", "codigo": "A"}] if str(path).endswith("salas.json") else [],
    )

    with app_module.app.test_client() as client:
        response = client.get("/api/reports/data")
        exported = client.get("/api/reports/export/students")

    assert response.status_code == 200
    report = next(row for row in response.get_json() if row["id"] == "students")
    assert report["rows"][0] == [
        "ID do aluno", "Carteirinha", "Nome", "Turma", "Sala", "Perfil",
        "Empréstimos ativos", "Em atraso", "Situação",
    ]
    assert report["rows"][1] == ["s2", "CARD-1", "Ana", "INFO1", "Sem sala", "Bibliotecário", 0, 0, "Regular"]
    assert report["rows"][2] == ["s1", "CARD-2", "Bia", "INFO2", "Sala 1 — A", "Aluno", 1, 1, "Com atraso"]
    assert all(row[2] != "Removido" for row in report["rows"][1:])
    assert exported.status_code == 200
    assert "cadastro-de-alunos.csv" in exported.headers["Content-Disposition"]
