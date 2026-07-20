"""api/_helpers.py — Funções compartilhadas entre todos os blueprints."""
import json
import logging
from pathlib import Path
from utils import sb_exec
from flask import current_app

logger = logging.getLogger(__name__)

def ensure(path: Path):
    """Garante que o arquivo JSON existe."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("[]", encoding="utf-8")


def read_json(path: Path):
    """Lê um arquivo JSON com tratamento de erro."""
    ensure(path)
    try:
        content = path.read_text(encoding="utf-8") or "[]"
        return json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao decodificar JSON em {path}: {e}")
        return []
    except Exception as e:
        logger.error(f"Erro ao ler JSON de {path}: {e}")
        return []


def write_json(path: Path, data: list) -> bool:
    """Escreve dados em arquivo JSON com validação."""
    ensure(path)
    try:
        if not isinstance(data, (list, dict)):
            logger.warning(f"Tentativa de escrever dados inválidos em {path}")
            return False
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8"
        )
        return True
    except Exception as e:
        logger.error(f"Erro ao escrever JSON em {path}: {e}")
        return False


_table_ok_cache = {}

def table_ok(sb, table: str) -> bool:
    """Verifica se a tabela Supabase existe e está acessível.
    Respostas positivas ficam em cache (a tabela não deixa de existir
    durante a execução do app). Respostas negativas nunca ficam em
    cache, para o sistema continuar tentando se reconectar sozinho
    quando o Supabase estiver temporariamente fora do ar."""
    if _table_ok_cache.get(table):
        return True
    try:
        sb_exec(sb.table(table).select("id").limit(1))
        _table_ok_cache[table] = True
        return True
    except Exception as e:
        error_msg = str(e).lower()
        if "could not find the table" in error_msg:
            return False
        logger.debug(f"Erro ao verificar tabela {table}: {e}")
        return False


_deleted_at_cache = {}

def has_deleted_at(sb, table: str) -> bool:
    """Verifica se a tabela tem coluna 'deleted_at' (soft delete).
    Isso é uma característica fixa do esquema do banco (não muda com
    o app rodando), então o resultado fica em cache dos dois jeitos,
    assim que confirmado."""
    if table in _deleted_at_cache:
        return _deleted_at_cache[table]
    try:
        sb_exec(sb.table(table).select("deleted_at").limit(1))
        _deleted_at_cache[table] = True
        return True
    except Exception as e:
        error_msg = str(e).lower()
        if any(msg in error_msg for msg in ["could not find the 'deleted_at' column", "column deleted_at does not exist"]):
            _deleted_at_cache[table] = False
            return False
        logger.debug(f"Erro ao verificar coluna deleted_at: {e}")
        return False


def is_offline_error(e: Exception) -> bool:
    """Detecta se o erro é de conexão/modo offline."""
    error_msg = str(e).lower()
    offline_keywords = [
        "could not find the table",
        "offline mode",
        "connection refused",
        "connection reset",
        "timed out",
        "temporary failure",
        "network is unreachable",
    ]
    return any(keyword in error_msg for keyword in offline_keywords)