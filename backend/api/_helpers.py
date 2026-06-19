"""api/_helpers.py — Funções compartilhadas entre todos os blueprints."""
import json
from pathlib import Path
from utils import sb_exec

def ensure(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists(): path.write_text("[]", encoding="utf-8")

def read_json(path: Path):
    ensure(path)
    try: return json.loads(path.read_text(encoding="utf-8") or "[]")
    except: return []

def write_json(path: Path, data):
    ensure(path)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def table_ok(sb, table: str) -> bool:
    try: sb_exec(sb.table(table).select("id").limit(1)); return True
    except Exception as e: return "could not find the table" not in str(e).lower()

def has_deleted_at(sb, table: str) -> bool:
    try: sb_exec(sb.table(table).select("deleted_at").limit(1)); return True
    except Exception as e:
        m = str(e).lower()
        return not ("could not find the 'deleted_at' column" in m or "column deleted_at does not exist" in m)

def is_offline_error(e: Exception) -> bool:
    m = str(e).lower()
    return "could not find the table" in m or "offline mode" in m