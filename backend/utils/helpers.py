"""
utils/helpers.py
Funções auxiliares: datas, IDs, status de empréstimo.
"""

from datetime import date, timedelta
import uuid


def new_id() -> str:
    return str(uuid.uuid4())


def today_str() -> str:
    return date.today().isoformat()


def add_days(from_date: str, days: int) -> str:
    d = date.fromisoformat(from_date)
    return (d + timedelta(days=days)).isoformat()


def days_until(due_date: str) -> int:
    """Positivo = dias restantes, negativo = dias de atraso."""
    due = date.fromisoformat(str(due_date)[:10])
    return (due - date.today()).days


def loan_status(loan: dict) -> str:
    """Retorna 'returned', 'overdue' ou 'active'."""
    if loan.get("devolvido_em"):
        return "returned"
    due = loan.get("data_devolucao_prevista", "")
    if not due:
        return "active"
    return "overdue" if days_until(due) < 0 else "active"
