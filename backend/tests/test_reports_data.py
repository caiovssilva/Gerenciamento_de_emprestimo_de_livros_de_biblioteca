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
