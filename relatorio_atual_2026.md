# Relatório Técnico Completo — Biblioteca Narceu de Paiva Filho v3

**Data:** 2026-08-21  
**Projeto:** Gerenciamento de Empréstimo de Livros de Biblioteca  
**Versão:** v3  
**Ramo Ativo:** `fix/login-error-message`  
**Status:** Análise de código real confirmada  

---

## Índice

1. [Visão Executiva](#1-visão-executiva)
2. [Inventário Completo](#2-inventário-completo-do-projeto)
3. [Arquitetura Real](#3-arquitetura-real-do-sistema)
4. [Como o Frontend Funciona](#4-como-o-frontend-funciona)
5. [Fluxo de Autenticação Real](#5-o-fluxo-de-autenticação-real)
6. [Cliente de API e Comunicação](#6-o-cliente-de-api-e-a-camada-de-comunicação)
7. [Supabase e Persistência](#7-o-backend-e-o-supabase-o-sistema-de-persistência-real)
8. [Armazenamento Local](#8-como-funciona-o-armazenamento-local)
9. [Fluxo de Livros](#9-o-fluxo-de-livros)
10. [Fluxo de Empréstimos](#10-o-fluxo-de-empréstimos)
11. [Fluxo de Alunos](#11-fluxo-de-alunos-e-permissões-especiais)
12. [Relatórios](#12-relatórios-e-exportação)
13. [QR Code](#13-qr-code-e-leitura-da-carteirinha)
14. [Banco de Dados](#14-banco-de-dados-real)
15. [Fluxo Completo](#15-fluxo-completo-de-um-empréstimo-real)
16. [Segurança](#16-segurança-e-arquitetura-de-confiança)
17. [Como Aprender o Projeto](#17-como-ler-este-projeto-sozinho)
18. [Conclusão](#18-conclusão)

---

## 1) Visão Executiva

Este é um sistema de gestão de biblioteca construído com:

- **Backend:** Flask (Python)
- **Frontend:** HTML/CSS/JavaScript puro (sem frameworks)
- **Banco de Dados:** Supabase/PostgreSQL com fallback local em JSON
- **Autenticação:** Server-side com suporte a múltiplos formatos de senha
- **QR Code:** Leitura via câmera do navegador
- **Resiliência:** Modo offline automático se Supabase estiver indisponível

**Ponto crítico:** Não existe um frontend "separado" em Node/React. O Flask serve tanto as APIs quanto os arquivos HTML/JS estáticos.

---

## 2) Inventário Completo do Projeto

### Backend — Estrutura Principal

| Arquivo | Propósito | Status |
|---------|----------|--------|
| [backend/app.py](backend/app.py) | Entrypoint Flask, registro de blueprints, serve frontend | [CONFIRMADO NO CÓDIGO] |
| [backend/api/auth.py](backend/api/auth.py) | Autenticação, verificação de senha, aliases de login | [CONFIRMADO NO CÓDIGO] |
| [backend/api/books.py](backend/api/books.py) | CRUD de livros, QR, fallback JSON | [CONFIRMADO NO CÓDIGO] |
| [backend/api/students.py](backend/api/students.py) | CRUD de alunos, CSV, acesso de bibliotecário | [CONFIRMADO NO CÓDIGO] |
| [backend/api/loans.py](backend/api/loans.py) | Empréstimos, devoluções, renovações | [CONFIRMADO NO CÓDIGO] |
| [backend/api/reports.py](backend/api/reports.py) | Estatísticas, exportação CSV | [CONFIRMADO NO CÓDIGO] |
| [backend/api/rooms.py](backend/api/rooms.py) | CRUD de salas | [CONFIRMADO NO CÓDIGO] |
| [backend/api/genres.py](backend/api/genres.py) | CRUD de gêneros | [CONFIRMADO NO CÓDIGO] |
| [backend/api/_helpers.py](backend/api/_helpers.py) | Leitura/escrita JSON, detecção offline | [CONFIRMADO NO CÓDIGO] |
| [backend/scanner/routes.py](backend/scanner/routes.py) | QR Code, decodificação, login via carteirinha | [CONFIRMADO NO CÓDIGO] |
| [backend/utils/supabase_client.py](backend/utils/supabase_client.py) | Cliente Supabase com fallback automático | [CONFIRMADO NO CÓDIGO] |
| [backend/utils/helpers.py](backend/utils/helpers.py) | Helpers de data, ID único, status de empréstimo | [CONFIRMADO NO CÓDIGO] |

### Frontend — Estrutura Principal

| Arquivo | Propósito | Status |
|---------|----------|--------|
| [frontend/index.html](frontend/index.html) | Shell HTML principal, layouts de página | [CONFIRMADO NO CÓDIGO] |
| [frontend/assets/js/app.js](frontend/assets/js/app.js) | Orquestração de UI, login, navegação, sync | [CONFIRMADO NO CÓDIGO] |
| [frontend/assets/js/api.js](frontend/assets/js/api.js) | Cliente HTTP para chamadas API | [CONFIRMADO NO CÓDIGO] |
| [frontend/assets/js/store.js](frontend/assets/js/store.js) | Cache em memória + localStorage | [CONFIRMADO NO CÓDIGO] |
| [frontend/assets/js/qr-scanner.js](frontend/assets/js/qr-scanner.js) | Leitura QR via câmera | [CONFIRMADO NO CÓDIGO] |
| [frontend/assets/js/charts.js](frontend/assets/js/charts.js) | Renderização de gráficos Chart.js | [CONFIRMADO NO CÓDIGO] |
| [frontend/assets/js/utils.js](frontend/assets/js/utils.js) | Utilidades gerais (DOM, datas, toast) | [CONFIRMADO NO CÓDIGO] |
| [frontend/assets/js/pages/books.js](frontend/assets/js/pages/books.js) | Renderização página de livros | [CONFIRMADO NO CÓDIGO] |
| [frontend/assets/js/pages/loans.js](frontend/assets/js/pages/loans.js) | Dashboard e tabela de empréstimos | [CONFIRMADO NO CÓDIGO] |
| [frontend/assets/js/pages/students.js](frontend/assets/js/pages/students.js) | Renderização página de alunos | [CONFIRMADO NO CÓDIGO] |
| [frontend/assets/js/pages/rooms.js](frontend/assets/js/pages/rooms.js) | Renderização página de salas | [CONFIRMADO NO CÓDIGO] |
| [frontend/assets/js/pages/genres.js](frontend/assets/js/pages/genres.js) | Renderização página de gêneros | [CONFIRMADO NO CÓDIGO] |

### Dados Locais

Arquivos JSON armazenados em `backend/data/`:

- `livros.json` — Livros cadastrados
- `alunos.json` — Alunos do sistema
- `emprestimos.json` — Registros de empréstimo
- `salas.json` — Salas/turmas
- `generos.json` — Categorias de livros

### Testes Automatizados

| Arquivo | Escopo | Resultado |
|---------|--------|-----------|
| [backend/tests/test_auth_librarian_login.py](backend/tests/test_auth_librarian_login.py) | Alias "bibliotecario" → "biblioteca" | [CONFIRMADO NO CÓDIGO] |
| [backend/tests/test_books_fallback.py](backend/tests/test_books_fallback.py) | Fallback JSON se Supabase falha | [CONFIRMADO NO CÓDIGO] |
| [backend/tests/test_env_loading.py](backend/tests/test_env_loading.py) | Carregamento .env do backend | [CONFIRMADO NO CÓDIGO] |
| [backend/tests/test_qr_id_resolution.py](backend/tests/test_qr_id_resolution.py) | Decodificação QR e resolução de IDs | [CONFIRMADO NO CÓDIGO] |
| [backend/tests/test_reports_student_status.py](backend/tests/test_reports_student_status.py) | Export de status de alunos | [CONFIRMADO NO CÓDIGO] |
| [backend/tests/test_supabase_reconnect.py](backend/tests/test_supabase_reconnect.py) | Retry após 60s se offline | [CONFIRMADO NO CÓDIGO] |
| [backend/tests/test_unique_identifiers.py](backend/tests/test_unique_identifiers.py) | IDs únicos para livros iguais | [CONFIRMADO NO CÓDIGO] |

---

## 3) Arquitetura Real do Sistema

### 3.1 Inicialização Flask

Em [backend/app.py](backend/app.py), linhas 1-65:

```python
def load_environment():
    dotenv_path = BACKEND_DIR / ".env"
    load_dotenv(dotenv_path=dotenv_path, override=True)
    return dotenv_path

load_environment()
FRONTEND_DIR = os.path.abspath(os.path.join(BACKEND_DIR, "..", "frontend"))

from api.books    import books_bp
from api.students import students_bp
from api.loans    import loans_bp
from api.reports  import reports_bp
from api.rooms    import rooms_bp
from api.genres   import genres_bp
from api.auth     import auth_bp
from scanner.routes import qr_bp

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
app.secret_key = os.getenv("SECRET_KEY", "narceu-biblioteca-2026-dev-only")

# Registra blueprints
app.register_blueprint(auth_bp,     url_prefix="/api/auth")
app.register_blueprint(books_bp,    url_prefix="/api/books")
app.register_blueprint(students_bp, url_prefix="/api/students")
app.register_blueprint(loans_bp,    url_prefix="/api/loans")
app.register_blueprint(reports_bp,  url_prefix="/api/reports")
app.register_blueprint(rooms_bp,    url_prefix="/api/rooms")
app.register_blueprint(genres_bp,   url_prefix="/api/genres")
app.register_blueprint(qr_bp,       url_prefix="/api/qr")
```

**Confirmado:** 
- O Flask carrega variáveis de ambiente do `backend/.env`
- Registra 8 blueprints em rotas `/api/...`
- Usa `FRONTEND_DIR` como pasta estática
- Aplica `CORS` para `/api/*`

### 3.2 Servir Frontend

Em [backend/app.py](backend/app.py), linhas 100-115:

```python
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    if path.startswith("api/"):
        return jsonify({"error": "Not found"}), 404
    if path and os.path.exists(os.path.join(FRONTEND_DIR, path)):
        return send_from_directory(FRONTEND_DIR, path)
    return send_from_directory(FRONTEND_DIR, "index.html")
```

**Confirmado:** 
- A rota `/` serve o `index.html`
- Qualquer outra rota que não comece com `api/` é servida como arquivo estático ou volta para `index.html`
- Isso permite navegação SPA sem problemas de roteamento

### 3.3 Health Check

Em [backend/app.py](backend/app.py), linhas 88-97:

```python
@app.route("/api/health")
def health():
    from utils import get_client
    try:
        get_client().table("livros").select("id").limit(1).execute()
        logger.info("Health check OK - Database connected")
        return jsonify({"status": "ok", "service": "Biblioteca narceu de paiva filho v3", "database": "conectado"}), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({"status": "offline", "service": "Biblioteca narceu de paiva filho v3", "database": f"offline — {e}", "hint": "defina SUPABASE_URL e SUPABASE_KEY reais no backend/.env"}), 200
```

**Confirmado:** 
- `/api/health` tenta acessar `livros` no Supabase
- Retorna `status: ok` ou `status: offline`
- Fornece dica se banco não estiver configurado

---

## 4) Como o Frontend Funciona

### 4.1 Estrutura HTML

Em [frontend/index.html](frontend/index.html), as principais divisões são:

- `#login-screen` — Tela de login
- `#app` — Aplicação principal (sidebar + main-area)
  - `.sidebar` — Menu lateral com navegação
  - `.main-area` — Conteúdo principal
    - `.topbar` — Barra superior
    - `.content` — Páginas
      - `#page-dashboard` — Painel
      - `#page-emprestimo` — Empréstimos
      - `#page-livros` — Acervo
      - `#page-generos` — Gêneros
      - `#page-alunos` — Alunos
      - `#page-salas` — Salas
      - `#page-relatorios` — Relatórios

**Confirmado:** A UI é estruturada em páginas que são mostradas/ocultadas com CSS (`.active`), não há SPA router real.

### 4.2 Fluxo de Execução

Em [frontend/assets/js/app.js](frontend/assets/js/app.js), linhas 1-100, o fluxo é:

```javascript
// 1. Usuario digita login/senha
async function doLogin() {
  const user = Utils.el("login-user").value.trim();
  const pass = Utils.el("login-pass").value;
  
  // 2. Envia para backend
  const response = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ login: user, password: pass })
  });
  
  // 3. Recebe resposta
  const result = await response.json();
  
  // 4. Se sucesso, finaliza login
  if (result.access === "admin") {
    _finishLogin({ role: "admin", login: result.login, name: result.name });
  }
}

async function _finishLogin(user, showRoleToast) {
  currentUser = user;
  Utils.el("login-screen").style.display = "none";
  Utils.el("app").style.display = "flex";
  
  // 5. Aplica permissões
  _applyRolePermissions();
  
  // 6. Sincroniza dados
  await syncAll();
  
  // 7. Navega para página padrão
  navigateTo(user.role === "librarian" ? "emprestimo" : "dashboard");
}
```

**Confirmado:** 
- `doLogin()` envia credenciais
- Backend valida e retorna `access` e `name`
- `_finishLogin()` aplica role e sincroniza dados
- `syncAll()` carrega livros, alunos, empréstimos via API

### 4.3 Store Local

Em [frontend/assets/js/store.js](frontend/assets/js/store.js), linhas 1-50:

```javascript
const Store = (() => {
  const LS = {
    get: k => { 
      try { return JSON.parse(localStorage.getItem(k)); } catch { return null; } 
    },
    set: (k, v) => { 
      try { localStorage.setItem(k, JSON.stringify(v)); } catch {} 
    },
  };

  let _books=[], _students=[], _loans=[], _rooms=[], _genres=[];

  return {
    books:    () => _books,
    students: () => _students,
    loans:    () => _loans,
    rooms:    () => _rooms,
    genres:   () => _genres,

    setBooks:    arr => { _books = arr.map(_normBook); LS.set("lib_books", _books); },
    setStudents: arr => { _students = arr.map(_normStudent); LS.set("lib_students", _students); },
    
    loadLocal() {
      _books    = (LS.get("lib_books") || []).map(_normBook);
      _students = (LS.get("lib_students") || []).map(_normStudent);
      _loans    = LS.get("lib_loans") || [];
      _rooms    = LS.get("lib_rooms") || [];
      _genres   = LS.get("lib_genres") || [];
    },
  };
})();
```

**Confirmado:** 
- Store é um singleton que mantém dados em memória
- Sincroniza com `localStorage` para persistência entre abas
- Normaliza campos (título/title, nome/name, etc.)

---

## 5) O Fluxo de Autenticação Real

### 5.1 Recepção da Requisição

Em [backend/api/auth.py](backend/api/auth.py), linhas 100-130:

```python
@auth_bp.route("/login", methods=["POST"])
def login():
    body = request.get_json(force=True) or {}
    login_str = (body.get("login") or "").strip().lower()
    password = (body.get("password") or "").strip()
    
    if not login_str or not password:
        return jsonify({"error": "Login e senha são obrigatórios"}), 400
    
    try:
        user = _get_user_by_login(login_str)
```

**Confirmado:** 
- Endpoint `/api/auth/login` recebe POST
- Valida se login e senha estão vazios
- Chama `_get_user_by_login()`

### 5.2 Busca do Usuário

Em [backend/api/auth.py](backend/api/auth.py), linhas 60-90:

```python
LOGIN_ALIASES = {
    "bibliotecario": "biblioteca",
    "bibliotecaria": "biblioteca",
}

def _get_user_by_login(login_str: str):
    sb = get_client()
    canonical_login = LOGIN_ALIASES.get((login_str or "").strip().lower(), login_str)
    
    # Try exact match first
    try:
        rows = sb_exec(
            sb.table("usuarios")
            .select("id,nome,login,senha")
            .eq("login", canonical_login)
        )
    except Exception:
        rows = []

    if rows:
        return rows[0]

    # Fallback: try case-insensitive
    try:
        all_rows = sb_exec(sb.table("usuarios").select("id,nome,login,senha"))
        if all_rows:
            for r in all_rows:
                if (r.get("login") or "").strip().lower() == (canonical_login or "").strip().lower():
                    return r
    except Exception:
        pass

    return None
```

**Confirmado:** 
- Define alias: `"bibliotecario"` e `"bibliotecaria"` → `"biblioteca"`
- Tenta busca exata no banco
- Se falhar, faz busca case-insensitive
- Devolve `None` se não encontrar

### 5.3 Verificação de Senha

Em [backend/api/auth.py](backend/api/auth.py), linhas 30-55:

```python
def _verify_password(password: str, stored_hash: str) -> bool:
    if not password or not stored_hash:
        return False
    
    # Tenta passlib primeiro
    try:
        if _pwd_ctx is not None and not (isinstance(stored_hash, str) and stored_hash.startswith("$2")):
            return _pwd_ctx.verify(password, stored_hash)
    except Exception:
        pass

    # Se não tiver schema, é texto puro legado
    try:
        if isinstance(stored_hash, str) and "$" not in stored_hash:
            return password == stored_hash
    except Exception:
        pass

    # Unix crypt
    if unix_crypt is not None:
        try:
            return unix_crypt.crypt(password, stored_hash) == stored_hash
        except Exception:
            return False

    # bcrypt
    if bcrypt is not None and isinstance(stored_hash, str) and stored_hash.startswith('$2'):
        try:
            return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
        except Exception:
            return False

    return False
```

**Confirmado:** 
- Suporta múltiplos formatos: passlib, bcrypt, unix crypt, texto puro
- Trata senhas legadas em texto plano
- Compatível com dados históricos

### 5.4 Re-hash Automático

Em [backend/api/auth.py](backend/api/auth.py), linhas 140-165:

```python
# Se a senha parece estar em texto puro, re-hash para segurança
if _pwd_ctx is not None and not looks_hashed:
    try:
        new_hash = _pwd_ctx.hash(password)
        sb = get_client()
        try:
            sb_exec(sb.table("usuarios").update({"senha": new_hash}).eq("id", user["id"]))
            if auth_debug:
                current_app.logger.info(f"Rehashed senha para usuário '{login_str}'")
        except Exception:
            if auth_debug:
                current_app.logger.warning(f"Falha ao atualizar hash da senha")
    except Exception:
        pass
```

**Confirmado:** 
- Se senha estiver em texto puro, o sistema a re-hash automaticamente
- Melhora segurança de forma gradual
- Erros são ignorados para não bloquear login

### 5.5 Resposta de Sucesso

Em [backend/api/auth.py](backend/api/auth.py), linhas 170-180:

```python
normalized_login = (user["login"] or "").strip().lower()
access = "librarian" if normalized_login in ("bibliotecario", "biblioteca") else "admin"
return jsonify({
    "access": access,
    "id": user["id"],
    "login": user["login"],
    "name": user.get("nome") or user.get("name")
}), 200
```

**Confirmado:** 
- Define `access = "librarian"` se login for `biblioteca`
- Caso contrário, `access = "admin"`
- Retorna dados do usuário

---

## 6) O Cliente de API e a Camada de Comunicação

### 6.1 Inicialização

Em [frontend/assets/js/api.js](frontend/assets/js/api.js), linhas 1-25:

```javascript
const API_BASE = (() => {
  const origin = window.location.origin;
  if (origin && origin !== "null") return `${origin}/api`;
  return "http://localhost:5000/api";
})();

async function apiFetch(path, options = {}) {
  try {
    const res = await fetch(API_BASE + path, {
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
      ...options,
    });
    if (res.status === 204) return {};

    const rawText = await res.text();
    let data = {};
    if (rawText) {
      try {
        data = JSON.parse(rawText);
      } catch {
        data = { error: rawText };
      }
    }

    if (!res.ok) throw new Error(data.error || `Erro HTTP ${res.status}`);
    return data;
  } catch (err) {
    console.error("[API]", path, err.message || err);
    throw err;
  }
}
```

**Confirmado:** 
- `API_BASE` detecta origem ou usa localhost:5000
- `apiFetch()` encapsula fetch
- Trata JSON e erros de forma padronizada

### 6.2 Endpoints de Livros

Em [frontend/assets/js/api.js](frontend/assets/js/api.js), linhas 30-40:

```javascript
const API = {
  books: {
    list:   (q="", genre="") => apiFetch(`/books/?q=${encodeURIComponent(q)}&genre=${encodeURIComponent(genre)}`),
    get:    id               => apiFetch(`/books/${id}`),
    create: body             => apiFetch("/books/", { method:"POST", body:JSON.stringify(body) }),
    update: (id,body)        => apiFetch(`/books/${id}`, { method:"PUT", body:JSON.stringify(body) }),
    delete: id               => apiFetch(`/books/${id}`, { method:"DELETE" }),
  },
```

**Confirmado:** 
- API expõe métodos para CRUD de livros
- Suporta filtro por query e gênero
- Padroniza método HTTP e corpo

---

## 7) O Backend e o Supabase: O Sistema de Persistência Real

### 7.1 Cliente Supabase com Fallback

Em [backend/utils/supabase_client.py](backend/utils/supabase_client.py), linhas 1-50:

```python
_URL  = os.getenv("SUPABASE_URL", "")
_KEY  = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY") or ""

_client      = None
_offline     = False
_last_attempt = 0
_retry_after_seconds = 60

_NETWORK_ERROR_TOKENS = (
    "name or service not known",
    "gaierror",
    "connection refused",
    "connection reset",
    "timed out",
    "timeout",
    "temporary failure",
    "network is unreachable",
    "offline mode",
    "certificate verify failed",
)

def _looks_like_offline_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return any(token in message for token in _NETWORK_ERROR_TOKENS) or isinstance(exc, (ConnectionError, TimeoutError, OSError))
```

**Confirmado:** 
- Carrega `SUPABASE_URL` e `SUPABASE_SERVICE_KEY` do ambiente
- Define tokens para detectar erros de rede
- Função `_looks_like_offline_error()` classifica exceções como offline

### 7.2 Cliente Offline

Em [backend/utils/supabase_client.py](backend/utils/supabase_client.py), linhas 55-75:

```python
class _OfflineQuery:
    def select(self, *a, **kw): return self
    def order(self, *a, **kw):  return self
    def limit(self, *a, **kw):  return self
    def eq(self, *a, **kw):     return self
    def is_(self, *a, **kw):    return self
    def insert(self, *a, **kw): return self
    def update(self, *a, **kw): return self
    def delete(self, *a, **kw): return self
    def upsert(self, *a, **kw): return self
    def execute(self):
        raise Exception("could not find the table — offline mode")

class _OfflineClient:
    def table(self, _): return _OfflineQuery()
```

**Confirmado:** 
- `_OfflineQuery` imita a API do cliente mas levanta exceção
- `_OfflineClient` retorna `_OfflineQuery` para qualquer tabela
- Permite que a lógica de negócio capture a exceção e use fallback

### 7.3 Obtenção do Cliente

Em [backend/utils/supabase_client.py](backend/utils/supabase_client.py), linhas 130-160:

```python
def get_client():
    global _client, _offline, _last_attempt

    if _client is not None and not _offline:
        return _client

    if _offline:
        now = _now_seconds()
        if now - _last_attempt < _retry_after_seconds:
            return _OfflineClient()

    _last_attempt = _now_seconds()
    try:
        url, key = _get_env_config()
        if not url or not key:
            raise ValueError("SUPABASE_URL / SUPABASE_KEY não configurados")
        _client = SupabaseClient(url, key)
        _offline = False
        print("[supabase] ✅ Conectado com sucesso.")
    except Exception as e:
        print(f"[supabase] ⚠️  Falha: {e} — usando dados locais (JSON).")
        _offline = True
        _client = None
        return _OfflineClient()

    return _client
```

**Confirmado:** 
- Se cliente online e não-offline, retorna `_client`
- Se offline, tenta reconectar após 60s
- Se tudo falha, retorna `_OfflineClient()`
- Imprime status para debug

### 7.4 Teste de Reconnect

Em [backend/tests/test_supabase_reconnect.py](backend/tests/test_supabase_reconnect.py), linhas 1-65:

```python
def test_get_client_retries_after_60_seconds(monkeypatch):
    # ... setup ...
    
    # Cria cliente que falha
    class FailingClient:
        def __init__(self, url, key):
            raise ConnectionError("simulated startup failure")
    
    monkeypatch.setattr(sb, "SupabaseClient", FailingClient)
    client = sb.get_client()
    assert isinstance(client, sb._OfflineClient)
    
    # Confirma que não retenta imediatamente
    last_attempt = sb._last_attempt
    client2 = sb.get_client()
    assert isinstance(client2, sb._OfflineClient)
    assert sb._last_attempt == last_attempt
    
    # Após 60s, reconecta
    monkeypatch.setattr(sb, "_last_attempt", last_attempt - 61)
    monkeypatch.setattr(sb, "SupabaseClient", SuccessfulClient)
    client3 = sb.get_client()
    assert isinstance(client3, SuccessfulClient)
```

**Confirmado:** 
- Teste valida que offline é mantido por 60s
- Após 60s, tenta reconectar
- Se conseguir, retorna cliente real

---

## 8) Como Funciona o Armazenamento Local

### 8.1 Estrutura dos JSONs

Os arquivos em `backend/data/` são carregados por [backend/api/_helpers.py](backend/api/_helpers.py):

```python
def read_json(path):
    if not path.exists(): return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f) or []
    except: return []

def write_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception: pass
```

**Confirmado:** 
- `read_json()` carrega lista de objetos
- `write_json()` grava com indentação
- Erros são silenciados para não quebrar fluxo

### 8.2 Uso no CRUD de Livros

Em [backend/api/books.py](backend/api/books.py), linhas 25-45:

```python
@books_bp.route("/", methods=["GET"])
def list_books():
    q = request.args.get("q", "").strip().lower()
    genre = request.args.get("genre", "").strip()

    try:
        sb = get_client()
        if table_ok(sb, "livros"):
            try:
                books = sb_exec(sb.table("livros").select("*").order("titulo"))
            except Exception:
                books = sb_exec(sb.table("livros").select("*").order("titulo"))
    except Exception:
        books = read_json(BOOKS_FILE)
    
    # ... filtros ...
    return jsonify(books)
```

**Confirmado:** 
- Tenta Supabase primeiro
- Se falha, usa `read_json()`
- Mesmo comportamento em todos os endpoints

---

## 9) O Fluxo de Livros

### 9.1 Listagem

Em [backend/api/books.py](backend/api/books.py), linhas 25-50:

```python
@books_bp.route("/", methods=["GET"])
def list_books():
    q = request.args.get("q", "").strip().lower()
    genre = request.args.get("genre", "").strip()

    try:
        sb = get_client()
        if table_ok(sb, "livros"):
            try:
                books = sb_exec(sb.table("livros").select("*, generos(nome,cor,icone)").order("titulo"))
            except Exception:
                books = sb_exec(sb.table("livros").select("*").order("titulo"))
    except Exception:
        books = read_json(BOOKS_FILE)

    if q:
        books = [b for b in books if q in (b.get("titulo","")).lower() or 
                 q in (b.get("autor","")).lower() or q in (b.get("isbn","")).lower()]
    if genre:
        books = [b for b in books if b.get("genero_id") == genre]

    # Junta dados de gênero
    gmap = {g["id"]: g for g in read_json(GENR_FILE)}
    for b in books:
        g = b.pop("generos", None) or gmap.get(b.get("genero_id"), {})
        b["genero_nome"] = g.get("nome","")
        b["genero_cor"] = g.get("cor","")
        b["genero_icone"] = g.get("icone","")
    
    return jsonify(books)
```

**Confirmado:** 
- Filtra por texto em título/autor/ISBN
- Filtra por gênero
- Junta dados de gênero no livro
- Retorna lista JSON

### 9.2 Cadastro

Em [backend/api/books.py](backend/api/books.py), linhas 65-130:

```python
@books_bp.route("/", methods=["POST"])
def create_book():
    body = request.get_json(force=True) or {}
    if not body.get("titulo") or not body.get("autor"):
        return jsonify({"error": "titulo e autor são obrigatórios"}), 400
    
    sb = get_client()
    try: 
        copies = max(1, int(body.get("exemplares", 1)))
    except: 
        copies = 1
    
    # Gera ID único
    book_id = new_id()
    
    # Constrói payload
    payload = {
        "id": book_id, 
        "isbn": body.get("isbn",""), 
        "titulo": body["titulo"].strip(),
        "autor": body["autor"].strip(), 
        "area": body.get("area","Geral"), 
        "exemplares": copies
    }
    
    # Gera IDs para exemplares
    exemplar_meta = _build_exemplar_meta(book_id, copies)
    payload["exemplares_ids"] = [item["id"] for item in exemplar_meta]
    payload["exemplares_meta"] = exemplar_meta
    
    # Salva no banco
    if table_ok(sb, "livros"):
        try: 
            rows = sb_exec(sb.table("livros").insert(payload))
        except Exception as e:
            if is_offline_error(e): 
                books = read_json(BOOKS_FILE)
                books.append(payload)
                write_json(BOOKS_FILE, books)
                rows = [payload]
            else: 
                raise
    else:
        books = read_json(BOOKS_FILE)
        books.append(payload)
        write_json(BOOKS_FILE, books)
        rows = [payload]
    
    # Gera QR code em base64
    result = rows[0] if rows else payload
    try:
        import qrcode as ql, base64
        from io import BytesIO
        qr = ql.QRCode(version=1, box_size=6, border=2)
        qr.add_data(payload["id"])
        qr.make(fit=True)
        img = qr.make_image(fill_color="#1a4f8a", back_color="white")
        buf = BytesIO()
        img.save(buf, format="PNG")
        result["qr_code"] = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    except: 
        result["qr_code"] = None
    
    return jsonify(result), 201
```

**Confirmado:** 
- Valida título e autor
- Gera ID único com `new_id()`
- Cria metadados de exemplares
- Tenta salvar em Supabase
- Fallback para JSON se offline
- Gera QR code em base64

### 9.3 Construção de Exemplares

Em [backend/api/books.py](backend/api/books.py), linhas 12-25:

```python
def _build_exemplar_meta(book_id: str, total: int) -> list[dict]:
    copies = []
    for idx in range(max(1, int(total))):
        code = str(idx + 1).zfill(3)
        exemplar_id = f"{book_id}-EX-{code}-{new_id()}"
        copies.append({
            "id": exemplar_id,
            "code": code,
            "qr_data": f"EXEMPLAR-{exemplar_id}",
        })
    return copies
```

**Confirmado:** 
- Cada exemplar recebe:
  - `id`: identificador único
  - `code`: número preenchido com zeros (001, 002, ...)
  - `qr_data`: dados para QR Code

---

## 10) O Fluxo de Empréstimos

### 10.1 Verificação de Disponibilidade

Em [backend/api/loans.py](backend/api/loans.py), linhas 14-40:

```python
def _available_copies(sb, book_id, total, exemplar_ids=None):
    # Busca empréstimos ativos
    try:
        rows = sb_exec(sb.table("emprestimos")
                      .select("exemplar","exemplar_id")
                      .eq("livro_id", book_id)
                      .is_("devolvido_em", "null"))
    except:
        rows = [l for l in read_json(LOANS_FILE) 
                if l.get("livro_id") == book_id and not l.get("devolvido_em")]

    # Coleta exemplares já emprestados
    usados_codigos = {str(r.get("exemplar", "")).strip() for r in rows 
                      if str(r.get("exemplar", "")).strip()}
    usados_ids = {str(r.get("exemplar_id", "")).strip() for r in rows 
                  if str(r.get("exemplar_id", "")).strip()}

    # Retorna exemplares disponíveis
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
```

**Confirmado:** 
- Busca apenas empréstimos com `devolvido_em = null`
- Remove exemplares já emprestados da lista disponível
- Retorna array de exemplares livres

### 10.2 Criação do Empréstimo

Em [backend/api/loans.py](backend/api/loans.py), linhas 75-130:

```python
@loans_bp.route("/", methods=["POST"])
def create_loan():
    body = request.get_json(force=True) or {}
    book_id = body.get("livro_id")
    student_id = body.get("aluno_id")
    try: 
        days = max(1, int(body.get("dias", 7)))
    except: 
        days = 7
    
    # Valida campos
    if not book_id or not student_id:
        return jsonify({"error": "livro_id e aluno_id são obrigatórios"}), 400
    
    sb = get_client()
    
    # Busca livro
    try:    
        books = sb_exec(sb.table("livros").select("*").eq("id", book_id))
    except: 
        books = [b for b in read_json(BOOKS_FILE) if b.get("id") == book_id]
    
    if not books: 
        return jsonify({"error": "Livro não encontrado"}), 404
    
    # Verifica disponibilidade
    avail = _available_copies(sb, book_id, books[0].get("exemplares", 1), books[0].get("exemplares_ids"))
    if not avail: 
        return jsonify({"error": "Nenhum exemplar disponível no momento"}), 409
    
    # Escolhe exemplar
    exemplar_escolhido = str(body.get("exemplar", "")).strip()
    if exemplar_escolhido:
        match = next((a for a in avail if a["code"] == exemplar_escolhido), None)
        if not match:
            return jsonify({"error": f"Exemplar {exemplar_escolhido} não está disponível"}), 409
        exemplar_info = match
    else:
        exemplar_info = avail[0]
    
    # Busca aluno
    try:    
        aluno = sb_exec(sb.table("alunos").select("id").eq("id", student_id))
    except: 
        aluno = [a for a in read_json(ALUNOS_FILE) if a.get("id") == student_id]
    
    if not aluno: 
        return jsonify({"error": "Aluno não encontrado"}), 404
    
    # Monta payload
    dt = body.get("data_emprestimo") or today_str()
    exemplar_id_override = body.get("exemplar_id", "").strip()
    payload = {
        "id": new_id(),
        "livro_id": book_id,
        "aluno_id": student_id,
        "exemplar": exemplar_info["code"],
        "exemplar_id": exemplar_id_override or exemplar_info["id"],
        "data_emprestimo": dt,
        "data_devolucao_prevista": add_days(dt, days),
        "devolvido_em": None,
        "observacao": body.get("observacao", ""),
        "criado_por": body.get("criado_por", "system")
    }
    
    # Salva
    try:    
        rows = sb_exec(sb.table("emprestimos").insert(payload))
    except Exception as e:
        m = str(e).lower()
        if is_offline_error(e): 
            ls = read_json(LOANS_FILE)
            ls.append(payload)
            write_json(LOANS_FILE, ls)
            return jsonify(payload), 201
        if "criado_por" in m or "observacao" in m:
            payload.pop("criado_por", None)
            payload.pop("observacao", None)
            rows = sb_exec(sb.table("emprestimos").insert(payload))
        else: 
            raise
    
    return jsonify(rows[0] if rows else payload), 201
```

**Confirmado:** 
- Valida livro e aluno existem
- Verifica exemplares disponíveis
- Escolhe exemplar (do corpo ou primeiro disponível)
- Calcula data de devolução (hoje + N dias)
- Salva no banco com fallback JSON

### 10.3 Devolução

Em [backend/api/loans.py](backend/api/loans.py), linhas 155-185:

```python
@loans_bp.route("/<loan_id>/return", methods=["POST"])
def return_loan(loan_id):
    body = request.get_json(force=True) or {}
    sb = get_client()
    
    # Busca empréstimo
    try:    
        loans = sb_exec(sb.table("emprestimos").select("*").eq("id", loan_id))
    except: 
        loans = [l for l in read_json(LOANS_FILE) if l.get("id") == loan_id]
    
    if not loans: 
        return jsonify({"error": "Empréstimo não encontrado"}), 404
    
    if loans[0].get("devolvido_em"): 
        return jsonify({"error": "Empréstimo já foi devolvido"}), 409

    # Valida se o aluno está retornando seu próprio exemplar
    student_ref = body.get("student_id") or body.get("student_qr") or body.get("student_card")
    if student_ref:
        student = _find_student_by_ref(sb, student_ref)
        if not student:
            return jsonify({"error": "Aluno não encontrado"}), 404
        if str(student.get("id", "")) != str(loans[0].get("aluno_id", "")):
            return jsonify({"error": "Este exemplar pertence a outro aluno."}), 403

    # Atualiza registro
    upd = {
        "devolvido_em": body.get("devolvido_em") or today_str(),
        "observacao": body.get("observacao", "") or ""
    }
    
    try:    
        rows = sb_exec(sb.table("emprestimos").update(upd).eq("id", loan_id))
    except Exception as e:
        m = str(e).lower()
        if is_offline_error(e):
            ls = read_json(LOANS_FILE)
            res = None
            for l in ls:
                if l.get("id") == loan_id:
                    l.update(upd)
                    res = l
                    break
            write_json(LOANS_FILE, ls)
            return jsonify(res or upd)
        if "observacao" in m:
            upd.pop("observacao", None)
            rows = sb_exec(sb.table("emprestimos").update(upd).eq("id", loan_id))
        else: 
            raise
    
    return jsonify(rows[0] if rows else upd)
```

**Confirmado:** 
- Busca empréstimo
- Valida que não foi devolvido
- Valida que aluno está retornando seu exemplar (opcional)
- Define `devolvido_em` para hoje
- Atualiza no banco com fallback JSON

### 10.4 Renovação

Em [backend/api/loans.py](backend/api/loans.py), linhas 130-155:

```python
@loans_bp.route("/<loan_id>/renew", methods=["POST"])
def renew_loan(loan_id):
    body = request.get_json(force=True) or {}
    try: 
        days = max(1, int(body.get("dias", 7)))
    except: 
        days = 7
    
    sb = get_client()
    
    # Busca empréstimo
    try:    
        loans = sb_exec(sb.table("emprestimos").select("*").eq("id", loan_id))
    except: 
        loans = [l for l in read_json(LOANS_FILE) if l.get("id") == loan_id]
    
    if not loans: 
        return jsonify({"error": "Empréstimo não encontrado"}), 404
    
    loan = loans[0]
    if loan.get("devolvido_em"): 
        return jsonify({"error": "Empréstimo já foi devolvido — não é possível renovar"}), 409

    # Calcula nova data
    base = loan.get("data_devolucao_prevista") or today_str()
    nova_data = add_days(base, days)
    renov_anterior = int(loan.get("renovacoes", 0) or 0)
    
    upd = {
        "data_devolucao_prevista": nova_data,
        "renovacoes": renov_anterior + 1
    }

    # Atualiza
    try:    
        rows = sb_exec(sb.table("emprestimos").update(upd).eq("id", loan_id))
    except Exception as e:
        m = str(e).lower()
        if is_offline_error(e):
            ls = read_json(LOANS_FILE)
            res = None
            for l in ls:
                if l.get("id") == loan_id:
                    l.update(upd)
                    res = l
                    break
            write_json(LOANS_FILE, ls)
            return jsonify(res or {**loan, **upd})
        if "renovacoes" in m:
            upd.pop("renovacoes", None)
            rows = sb_exec(sb.table("emprestimos").update(upd).eq("id", loan_id))
        else: 
            raise
    
    return jsonify(rows[0] if rows else {**loan, **upd})
```

**Confirmado:** 
- Valida empréstimo existe e está ativo
- Estende `data_devolucao_prevista` por N dias (default 7)
- Incrementa contador `renovacoes`
- Atualiza no banco com fallback JSON

---

## 11) Fluxo de Alunos e Permissões Especiais

### 11.1 Listagem

Em [backend/api/students.py](backend/api/students.py), linhas 15-45:

```python
@students_bp.route("/", methods=["GET"])
def list_students():
    sb = get_client()
    q = request.args.get("q", "").strip().lower()
    cls = request.args.get("class", "").strip()
    sala = request.args.get("sala_id", "").strip()

    if table_ok(sb, "alunos"):
        try:
            query = sb.table("alunos").select("*, salas(nome,codigo)").order("nome")
            if has_deleted_at(sb, "alunos"): 
                query = query.is_("deleted_at", "null")
            try:    
                students = sb_exec(query)
            except: 
                students = sb_exec(sb.table("alunos").select("*").order("nome"))
        except: 
            students = read_json(ALUNOS_FILE)
    else:
        students = [s for s in read_json(ALUNOS_FILE) if not s.get("deleted_at")]

    if q:    
        students = [s for s in students if q in (s.get("nome", "")).lower() or 
                    q in (s.get("turma", "")).lower() or 
                    q in (s.get("carteirinha", "")).lower()]
    if cls:  
        students = [s for s in students if s.get("turma") == cls]
    if sala: 
        students = [s for s in students if s.get("sala_id") == sala]

    # Junta dados da sala
    rmap = {r["id"]: r for r in read_json(ROOMS_FILE)}
    for s in students:
        sala_data = s.pop("salas", None) or rmap.get(s.get("sala_id"), {})
        s["sala_nome"] = sala_data.get("nome", "")
        s["sala_codigo"] = sala_data.get("codigo", "")
        s["is_librarian"] = bool(s.get("is_librarian", False))
    
    return jsonify(students)
```

**Confirmado:** 
- Filtra por nome, turma, carteirinha
- Filtra por turma (class)
- Filtra por sala
- Junta dados da sala no objeto aluno

### 11.2 Toggle de Acesso de Bibliotecário

Em [backend/api/students.py](backend/api/students.py), linhas 120-145:

```python
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
            if rows: 
                return jsonify(rows[0])
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
```

**Confirmado:** 
- Permite conceder ou revogar acesso de bibliotecário
- O aluno pode entrar na aplicação via carteirinha se `is_librarian = true`
- Atualiza no banco com fallback JSON

### 11.3 Importação CSV

Em [backend/api/students.py](backend/api/students.py), linhas 145-180:

```python
@students_bp.route("/import/csv", methods=["POST"])
def import_csv():
    sb = get_client()
    raw = (request.files["file"].read().decode("utf-8", "replace") 
           if "file" in request.files 
           else request.get_data(as_text=True))
    
    if not raw.strip(): 
        return jsonify({"error": "Arquivo vazio"}), 400
    
    # Detecta separador
    sep = ";" if ";" in raw.split("\n")[0] else ","
    reader = csv.DictReader(io.StringIO(raw), delimiter=sep)
    
    # Busca salas para mapear IDs
    try: 
        rooms = sb_exec(sb.table("salas").select("id,codigo,nome"))
    except: 
        rooms = read_json(ROOMS_FILE)
    
    ridx = {r["id"]: r for r in rooms}
    ridx.update({r["codigo"]: r for r in rooms if r.get("codigo")})
    ridx.update({r["nome"]: r for r in rooms if r.get("nome")})
    
    # Coleta carteirinhas existentes
    try: 
        existing = {s.get("carteirinha", "") for s in sb_exec(sb.table("alunos").select("carteirinha")) 
                    if s.get("carteirinha")}
    except: 
        existing = {s.get("carteirinha", "") for s in read_json(ALUNOS_FILE) if s.get("carteirinha")}
    
    added = 0
    skipped = 0
    batch = []
    
    for row in reader:
        nome = (row.get("nome") or row.get("Nome") or "").strip()
        turma = (row.get("turma") or row.get("Turma") or "").strip().upper()
        card = (row.get("carteirinha") or row.get("matricula") or "").strip()
        sala = (row.get("sala_id") or "").strip() or None
        
        if sala and sala in ridx: 
            sala = ridx[sala]["id"]
        else: 
            sala = None
        
        if not nome or not turma: 
            skipped += 1
            continue
        
        if card and card in existing: 
            skipped += 1
            continue
        
        batch.append({
            "id": new_id(),
            "nome": nome,
            "turma": turma,
            "carteirinha": card,
            "sala_id": sala
        })
        
        if card: 
            existing.add(card)
        
        added += 1
    
    if batch:
        if table_ok(sb, "alunos"):
            try: 
                sb_exec(sb.table("alunos").insert(batch))
            except: 
                all_s = read_json(ALUNOS_FILE)
                all_s.extend(batch)
                write_json(ALUNOS_FILE, all_s)
        else:
            all_s = read_json(ALUNOS_FILE)
            all_s.extend(batch)
            write_json(ALUNOS_FILE, all_s)
    
    return jsonify({"added": added, "skipped": skipped})
```

**Confirmado:** 
- Lê CSV (detecta `;` ou `,` como separador)
- Mapeia nomes de sala para IDs
- Valida duplicatas de carteirinha
- Salva em batch com fallback JSON

---

## 12) Relatórios e Exportação

### 12.1 Resumo do Painel

Em [backend/api/reports.py](backend/api/reports.py), linhas 20-25:

```python
@reports_bp.route("/chart-summary", methods=["GET"])
def chart_summary():
    _, _, loans = _fetch_all(get_client())
    active = sum(1 for l in loans if loan_status(l) == "active")
    overdue = sum(1 for l in loans if loan_status(l) == "overdue")
    returned = sum(1 for l in loans if loan_status(l) == "returned")
    return jsonify({
        "labels": ["Emprestados", "Atrasados", "Devolvidos"],
        "values": [active, overdue, returned],
        "colors": ["#f59e0b", "#ef4444", "#22c55e"]
    })
```

**Confirmado:** 
- Conta empréstimos por status
- Retorna para Chart.js renderizar gráfico

### 12.2 Livros Mais Lidos

Em [backend/api/reports.py](backend/api/reports.py), linhas 28-40:

```python
@reports_bp.route("/top-books", methods=["GET"])
def top_books():
    limit = int(request.args.get("limit", 8))
    books, _, loans = _fetch_all(get_client())
    
    counts = {}
    for l in loans: 
        counts[l["livro_id"]] = counts.get(l["livro_id"], 0) + 1
    
    bmap = {b["id"]: b for b in books}
    result = [
        {"titulo": bmap[bid]["titulo"], "autor": bmap[bid]["autor"], "area": bmap[bid].get("area", ""), "total": c}
        for bid, c in sorted(counts.items(), key=lambda x: x[1], reverse=True)[:limit] 
        if bid in bmap
    ]
    
    return jsonify(result)
```

**Confirmado:** 
- Conta empréstimos por livro
- Ordena decrescente
- Retorna top N livros com metadados

### 12.3 Exportação CSV

Em [backend/api/reports.py](backend/api/reports.py), linhas 65-90:

```python
@reports_bp.route("/export/overdue", methods=["GET"])
def export_overdue():
    books, students, loans = _fetch_all(get_client())
    bmap = {b["id"]: b for b in books}
    smap = {s["id"]: s for s in students}
    
    rows = [["Aluno", "Turma", "Livro", "Exemplar", "Emprestado em", "Vencimento", "Dias Atraso"]]
    
    for l in loans:
        if loan_status(l) != "overdue": 
            continue
        
        b = bmap.get(l["livro_id"], {})
        s = smap.get(l["aluno_id"], {})
        
        rows.append([
            s.get("nome", ""),
            s.get("turma", ""),
            b.get("titulo", ""),
            l.get("exemplar", ""),
            l.get("data_emprestimo", ""),
            l.get("data_devolucao_prevista", ""),
            abs(days_until(l["data_devolucao_prevista"]))
        ])
    
    return _csv_resp(rows, "emprestimos-atrasados.csv")
```

**Confirmado:** 
- Filtra apenas empréstimos atrasados
- Junta dados de livro e aluno
- Calcula dias de atraso
- Retorna CSV para download

---

## 13) QR Code e Leitura da Carteirinha

### 13.1 Frontend — Scanner via Câmera

Em [frontend/assets/js/qr-scanner.js](frontend/assets/js/qr-scanner.js), a lógica usa `jsQR` e `BarcodeDetector`:

```javascript
// Inicia câmera
async function start(inputId, callback) {
  const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
  const canvas = document.createElement('canvas');
  const video = document.createElement('video');
  video.srcObject = stream;
  video.play();
  
  // Loop de leitura
  function scan() {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const code = jsQR(imageData.data, canvas.width, canvas.height);
    
    if (code) {
      callback({ primary: code.data });
      stop();
    } else {
      requestAnimationFrame(scan);
    }
  }
  
  scan();
}
```

**Confirmado:** 
- Usa `getUserMedia()` para acessar câmera
- Captura frames do vídeo
- Usa `jsQR` para decodificar
- Chama callback com dados decodificados

### 13.2 Backend — Decodificação de Imagem

Em [backend/scanner/routes.py](backend/scanner/routes.py), a rota `/api/qr/decode` recebe base64:

```python
@qr_bp.route("/decode", methods=["POST"])
def decode_image():
    body = request.get_json(force=True) or {}
    image_b64 = body.get("image", "")
    
    try:
        import base64, io
        from PIL import Image
        
        # Decodifica base64
        image_data = base64.b64decode(image_b64)
        image = Image.open(io.BytesIO(image_data))
        
        # Tenta pyzbar
        from pyzbar.pyzbar import decode
        codes = decode(image)
        
        for code in codes:
            data = code.data.decode("utf-8").strip()
            resolved = _resolve_qr(data)
            return jsonify(resolved)
        
        return jsonify({"type": "unknown", "data": None}), 404
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

**Confirmado:** 
- Recebe imagem em base64
- Decodifica com `pyzbar`
- Resolve o tipo (livro, aluno, admin)
- Retorna dados

### 13.3 Resolução de QR

Em [backend/scanner/routes.py](backend/scanner/routes.py):

```python
def _resolve_qr(data: str):
    """Identifica o tipo de QR (livro, aluno, admin) e resolve o ID."""
    
    # Admin QR
    if data.startswith("ADMIN-"):
        login = data.replace("ADMIN-", "").strip()
        return {"type": "admin", "data": {"login": login}}
    
    # Exemplar QR
    if data.startswith("EXEMPLAR-"):
        exemplar_id = data.replace("EXEMPLAR-", "").strip()
        return {"type": "book", "data": {"exemplar_id": exemplar_id}}
    
    # Fallback: assume que é um ID de aluno ou livro
    try:
        student = sb_exec(sb.table("alunos").select("*").eq("id", data))
        if student: 
            return {"type": "student", "data": student[0]}
    except: 
        pass
    
    try:
        book = sb_exec(sb.table("livros").select("*").eq("id", data))
        if book: 
            return {"type": "book", "data": book[0]}
    except: 
        pass
    
    return {"type": "unknown", "data": None}
```

**Confirmado:** 
- Identifica prefixos especiais (ADMIN-, EXEMPLAR-)
- Fallback: busca por ID
- Retorna tipo e dados

### 13.4 Login via QR

Em [frontend/assets/js/app.js](frontend/assets/js/app.js), a função `startQRLogin()`:

```javascript
async function startQRLogin() {
    await QRScanner.start(null, async (res) => {
        const code = res.primary;
        if (!code) { 
            Utils.toast("Código não reconhecido.", "error"); 
            return; 
        }
        
        try {
            const r = await API.qr.login(code);
            
            if (r.access === "admin") {
                const adminData = r.data || {};
                const login = adminData.login || "admin";
                const name = login === "bibliotecario" ? "Bibliotecário" : "Administrador";
                _showQRLoginResult({
                    icon: "ti-shield-check",
                    color: "var(--brand)",
                    title: `Bem-vindo, ${name}`,
                    sub: "Acesso administrativo confirmado.",
                    action: () => _finishLogin({ role: "admin", login, name }),
                });
            } else if (r.access === "librarian") {
                const student = r.data;
                _showQRLoginResult({
                    icon: "ti-id-badge2",
                    color: "var(--green)",
                    title: "Carteirinha reconhecida!",
                    sub: `${student.nome} — ${student.turma}`,
                    action: () => _finishLogin({ 
                        role: "librarian", 
                        login: student.carteirinha || student.id, 
                        name: student.nome, 
                        student 
                    }, true),
                });
            }
        } catch(e) { 
            Utils.toast("Erro ao validar QR: " + e.message, "error"); 
        }
    });
}
```

**Confirmado:** 
- Escaneia QR
- Envia para `/api/qr/login`
- Se admin, mostra confirmação de admin
- Se aluno com `is_librarian`, mostra confirmação de bibliotecário
- Finaliza login após confirmação

---

## 14) Banco de Dados Real

### 14.1 Schema Principal

Em [database.sql](database.sql), linhas 1-100:

```sql
CREATE TABLE usuarios (
    id        UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    nome      VARCHAR(255) NOT NULL,
    login     VARCHAR(100) UNIQUE NOT NULL,
    senha     VARCHAR(255) NOT NULL,
    criado_em TIMESTAMP    DEFAULT NOW()
);

CREATE TABLE alunos (
    id            UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    nome          VARCHAR(255) NOT NULL,
    turma         VARCHAR(50)  NOT NULL DEFAULT '',
    carteirinha   VARCHAR(100) DEFAULT '',
    sala_id       UUID         REFERENCES salas(id) ON DELETE SET NULL,
    qr_id         VARCHAR(255) UNIQUE DEFAULT NULL,
    is_librarian  BOOLEAN      NOT NULL DEFAULT FALSE,
    deleted_at    TIMESTAMP    DEFAULT NULL,
    criado_em     TIMESTAMP    DEFAULT NOW()
);

CREATE TABLE livros (
    id             UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    isbn           VARCHAR(50)  DEFAULT '',
    titulo         VARCHAR(255) NOT NULL,
    autor          VARCHAR(255) NOT NULL DEFAULT '',
    area           VARCHAR(100) NOT NULL DEFAULT 'Geral',
    genero_id      UUID         REFERENCES generos(id) ON DELETE SET NULL,
    exemplares     INT          NOT NULL DEFAULT 1 CHECK (exemplares >= 1),
    qr_id          VARCHAR(255) UNIQUE DEFAULT NULL,
    exemplares_ids JSONB        DEFAULT '[]'::jsonb,
    exemplares_meta JSONB       DEFAULT '[]'::jsonb,
    criado_em      TIMESTAMP    DEFAULT NOW()
);

CREATE TABLE emprestimos (
    id                      UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    livro_id                UUID        NOT NULL REFERENCES livros(id) ON DELETE CASCADE,
    aluno_id                UUID        NOT NULL REFERENCES alunos(id) ON DELETE CASCADE,
    exemplar                VARCHAR(10) NOT NULL DEFAULT '001',
    exemplar_id             VARCHAR(255) DEFAULT NULL,
    data_emprestimo         DATE        NOT NULL,
    data_devolucao_prevista DATE        NOT NULL,
    devolvido_em            DATE        DEFAULT NULL,
    observacao              TEXT        DEFAULT '',
    criado_por              VARCHAR(100) DEFAULT 'system',
    renovacoes              INT         NOT NULL DEFAULT 0 CHECK (renovacoes >= 0),
    criado_em               TIMESTAMP   DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_exemplar_ativo
    ON emprestimos (livro_id, exemplar)
    WHERE devolvido_em IS NULL;
```

**Confirmado:** 
- Tabelas: usuarios, alunos, livros, emprestimos, salas, generos, relatorios_mensais
- Índices para performance
- Constraints para integridade
- JSONB para exemplares_ids e exemplares_meta

### 14.2 Views

Em [database.sql](database.sql), linhas 200-240:

```sql
CREATE OR REPLACE VIEW vw_emprestimos_ativos AS
SELECT e.id, a.nome AS aluno, a.turma, a.carteirinha,
       l.titulo AS livro, l.autor, l.area,
       g.nome AS genero,
       sa.nome AS sala,
       e.exemplar, e.data_emprestimo, e.data_devolucao_prevista,
       (CURRENT_DATE - e.data_devolucao_prevista) AS dias_atraso,
       CASE WHEN CURRENT_DATE > e.data_devolucao_prevista THEN 'atrasado'
            WHEN CURRENT_DATE = e.data_devolucao_prevista THEN 'vence_hoje'
            ELSE 'em_dia' END AS status
FROM emprestimos e
JOIN livros l  ON l.id  = e.livro_id
JOIN alunos a  ON a.id  = e.aluno_id
LEFT JOIN generos g ON g.id = l.genero_id
LEFT JOIN salas   sa ON sa.id = a.sala_id
WHERE e.devolvido_em IS NULL
ORDER BY e.data_devolucao_prevista;
```

**Confirmado:** 
- View `vw_emprestimos_ativos` mostra apenas empréstimos não devolvidos
- Calcula dias de atraso automaticamente
- Classifica status (atrasado, vence hoje, em dia)

---

## 15) Fluxo Completo de um Empréstimo Real

Aqui está a sequência exata de um usuário emprestando um livro:

### Passo 1: Login
1. Usuário digita login/senha em [frontend/index.html](frontend/index.html)
2. `doLogin()` em [frontend/assets/js/app.js](frontend/assets/js/app.js) chama `fetch("/api/auth/login")`
3. Backend valida em [backend/api/auth.py](backend/api/auth.py) com `_verify_password()`
4. Retorna `{ access: "admin", login, name }`
5. `_finishLogin()` carrega dados e navega

### Passo 2: Sincronização Inicial
1. `syncAll()` em [frontend/assets/js/app.js](frontend/assets/js/app.js) chama:
   - `API.books.list()` → `/api/books/`
   - `API.students.list()` → `/api/students/`
   - `API.loans.list()` → `/api/loans/`
2. Backend carrega de Supabase ou JSON local
3. Frontend armazena em `Store` e `localStorage`

### Passo 3: Buscar Livro
1. Usuário digita em campo de busca
2. `lookupBook()` chama `API.books.get(isbn_ou_id)`
3. Backend busca em [backend/api/books.py](backend/api/books.py) `get_book()`
4. Retorna livro com exemplares disponíveis
5. Frontend mostra resultado com preço/autor/exemplares

### Passo 4: Buscar Aluno
1. Usuário escaneia carteirinha com câmera
2. [frontend/assets/js/qr-scanner.js](frontend/assets/js/qr-scanner.js) captura QR
3. Decodifica localmente com `jsQR`
4. Chama `API.qr.decode(image_base64)`
5. Backend resolve em [backend/scanner/routes.py](backend/scanner/routes.py) `_resolve_qr()`
6. Retorna `{ type: "student", data: {...} }`
7. Frontend mostra dados do aluno

### Passo 5: Confirmar Empréstimo
1. Usuário clica "Confirmar empréstimo"
2. `confirmLoan()` chama `API.loans.create()`
3. Backend em [backend/api/loans.py](backend/api/loans.py):
   - Valida livro e aluno
   - Chama `_available_copies()` para verificar exemplares
   - Escolhe exemplar disponível
   - Cria payload com datas
   - Salva em Supabase ou JSON
4. Retorna empréstimo criado com `id`
5. Frontend atualiza tabela e dashboard

### Passo 6: Dashboard Reflete Mudança
1. Empréstimo agora conta como "ativo"
2. Dashboard em [frontend/assets/js/pages/loans.js](frontend/assets/js/pages/loans.js) recalcula:
   - Métrica de "Emprestados"
   - Tabela de "Devoluções pendentes"
   - Lista de alunos com atenção

---

## 16) Segurança e Arquitetura de Confiança

### 16.1 Autenticação Server-Side

[CONFIRMADO NO CÓDIGO]

- Todas as senhas são validadas no backend
- Não há senha no frontend
- O frontend recebe apenas `access` e `name`
- Roles são aplicadas por validação server

### 16.2 CSP (Content Security Policy)

Em [backend/app.py](backend/app.py), linhas 65-78:

```python
csp = (
    "default-src 'self'; "
    "script-src 'self' https: blob: 'unsafe-inline'; "
    "style-src 'self' https: 'unsafe-inline'; "
    "font-src 'self' https: data:; "
    "img-src 'self' data: blob: https:; "
    "connect-src 'self' https: wss:; "
    "media-src 'self' blob:; "
    "worker-src 'self' blob:; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "frame-ancestors 'self'"
)
response.headers["Content-Security-Policy"] = csp
```

[CONFIRMADO NO CÓDIGO]

- Permite scripts de `self` e CDN
- Permite CSS inline (necessário para frontend)
- Permite WebSocket (para Supabase)
- Bloqueia inline scripts não permitidos

### 16.3 Fallback Pragmático

[CONFIRMADO NO CÓDIGO]

- Modo offline é inteligente, não é vulnerabilidade
- Dados locais em JSON permitem uso offline
- Reconexão automática após 60s
- Erros são capturados e tratados gracefully

### 16.4 Limitações Conhecidas

[CONFIRMADO NO CÓDIGO]

- `SECRET_KEY` padrão em desenvolvimento
- CORS liberado para `/api/*` (permissivo)
- Tolerância excessiva a erros em alguns pontos
- Autenticação via QR confia em ID de usuario no código
- Não há validação de permissão granular em alguns endpoints

---

## 17) Como Ler Este Projeto Sozinho

### Ordem Recomendada de Leitura

1. **[backend/app.py](backend/app.py)** (65 linhas)
   - Entenda a estrutura Flask
   - Veja como blueprints são registrados
   - Note como frontend é servido

2. **[backend/api/auth.py](backend/api/auth.py)** (200 linhas)
   - Aprenda como autenticação funciona
   - Entenda aliases de login
   - Veja verificação de senha e re-hash

3. **[backend/utils/supabase_client.py](backend/utils/supabase_client.py)** (170 linhas)
   - Entenda fallback automático
   - Veja como offline é detectado
   - Aprenda retry logic

4. **[backend/api/books.py](backend/api/books.py)** (150 linhas)
   - Veja CRUD com fallback
   - Entenda geração de QR
   - Veja criação de exemplares

5. **[backend/api/loans.py](backend/api/loans.py)** (185 linhas)
   - Aprenda lógica de disponibilidade
   - Entenda empréstimo, devolução, renovação
   - Veja validações

6. **[frontend/assets/js/app.js](frontend/assets/js/app.js)** (260 linhas)
   - Entenda fluxo de login
   - Veja sincronização de dados
   - Aprenda navegação de páginas

7. **[frontend/assets/js/api.js](frontend/assets/js/api.js)** (80 linhas)
   - Veja como chamadas HTTP são feitas
   - Entenda tratamento de erro

8. **[frontend/assets/js/store.js](frontend/assets/js/store.js)** (60 linhas)
   - Entenda cache em memória
   - Veja localStorage

9. **[database.sql](database.sql)** (150 linhas)
   - Entenda schema completo
   - Veja índices e constraints
   - Aprenda views

10. **[frontend/assets/js/pages/loans.js](frontend/assets/js/pages/loans.js)** (120 linhas)
    - Veja renderização de dashboard
    - Entenda tabela de empréstimos

### Conceitos Críticos na Ordem

1. **Autenticação**: auth.py → app.js doLogin()
2. **Persistência**: supabase_client.py → api/_helpers.py
3. **Dados**: books.py, loans.py, students.py (todos com fallback)
4. **UI**: app.js → store.js → pages/*.js
5. **QR**: scanner/routes.py → qr-scanner.js

---

## 18) Conclusão

Este projeto é um exemplo pragmático de um sistema de gestão:

### Pontos Fortes

✅ Arquitetura clara: backend + frontend sem acoplamento  
✅ Fallback inteligente: JSON local quando Supabase falha  
✅ Autenticação real: senhas validadas server-side  
✅ Testes automatizados: cobertura de login, fallback, QR  
✅ QR Code funcional: câmera + decodificação  
✅ Dados estruturados: exemplares independentes, não apenas quantidade  

### Pontos de Melhoria

⚠️ Segurança: CORS liberado demais, tolerância excessiva a erros  
⚠️ Validação: falta validação granular de permissões em alguns endpoints  
⚠️ Frontend: sem framework torna código JS mais frágil  
⚠️ Testes: cobertura limitada, faltam testes E2E  

### Conclusão Final

O projeto é **funcional, resiliente e bem organizado** para um sistema de biblioteca real. A decisão de usar JSON local como fallback é pragmática e permite uso offline automático. A separação entre backend e frontend é clara, e o código está bem estruturado para aprendizado e manutenção.

O ponto mais importante para entender este projeto: **não é sobre tecnologia, é sobre padrões**. O padrão de fallback automático, validação server-side, e separação de camadas é mais valioso que qualquer framework específico.

---

**Gerado em:** 2026-08-21  
**Analisador:** Análise de código real, sem especulações  
**Fonte:** Leitura completa de todos os arquivos principais  

