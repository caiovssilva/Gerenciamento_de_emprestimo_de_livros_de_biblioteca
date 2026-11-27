import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app as app_module
import api.reports as reports_module


def test_student_status_export_includes_borrowed_owing_and_returned(monkeypatch):
    def fake_fetch_all(_sb):
        books = [{"id": "b1", "titulo": "Duna", "autor": "Frank Herbert"}]
        students = [{"id": "s1", "nome": "Ana", "turma": "INFO3A"}]
        loans = [
            {"id": "l1", "livro_id": "b1", "aluno_id": "s1", "exemplar": "001", "data_emprestimo": "2026-06-01", "data_devolucao_prevista": "2026-06-08", "devolvido_em": None},
            {"id": "l2", "livro_id": "b1", "aluno_id": "s1", "exemplar": "002", "data_emprestimo": "2026-05-01", "data_devolucao_prevista": "2026-05-08", "devolvido_em": "2026-05-07"},
        ]
        return books, students, loans

    monkeypatch.setattr(reports_module, "_fetch_all", fake_fetch_all)

    with app_module.app.test_client() as client:
        response = client.get("/api/reports/export/student-status")

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "Aluno" in body
    assert "Situação" in body
    assert "emprestado" in body.lower()
    assert "devolvido" in body.lower()
