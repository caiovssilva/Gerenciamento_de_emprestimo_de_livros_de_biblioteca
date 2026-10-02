"""utils/helpers.py — Funções auxiliares de data, ID e status."""
from datetime import date, timedelta
import uuid

def new_id()  -> str: return str(uuid.uuid4())
def today_str() -> str: return date.today().isoformat()
def add_days(from_date: str, days: int) -> str:
    return (date.fromisoformat(from_date) + timedelta(days=days)).isoformat()
def days_until(due_date: str) -> int:
    return (date.fromisoformat(str(due_date)[:10]) - date.today()).days
def loan_status(loan: dict) -> str:
    if loan.get("devolvido_em"): return "returned"
    due = loan.get("data_devolucao_prevista", "")
    return "overdue" if due and days_until(due) < 0 else "active"