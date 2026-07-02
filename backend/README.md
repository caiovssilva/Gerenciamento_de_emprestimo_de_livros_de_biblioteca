# Biblioteca narceu de paiva filho — Campus Aracruz

Sistema completo de gerenciamento de biblioteca escolar com empréstimos, acervo, alunos, QR Code e relatórios.

**Stack:** Python 3.11+ · Flask · JavaScript Vanilla · Supabase (PostgreSQL) · Chart.js

---

## Sumário

1. [Pré-requisitos](#pré-requisitos)
2. [Instalação](#instalação)
3. [Rodando o projeto](#rodando-o-projeto)
4. [Login](#login)
5. [O que testar](#o-que-testar)
6. [Como funciona a conexão backend ↔ frontend](#como-funciona-a-conexão-backend--frontend)
7. [Modo offline](#modo-offline)
8. [Estrutura de pastas](#estrutura-de-pastas)
9. [Endpoints da API](#endpoints-da-api)
10. [Problemas comuns](#problemas-comuns)

---

## Pré-requisitos

| Ferramenta | Versão mínima | Download |
|------------|--------------|---------|
| Python | 3.11 | [python.org/downloads](https://www.python.org/downloads/) |
| Git | qualquer | [git-scm.com](https://git-scm.com/) |

Verifique antes de começar:
```bash
python --version   # deve mostrar 3.11 ou superior
git --version
```

---

## Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/SEU-USUARIO/SEU-REPOSITORIO.git
cd SEU-REPOSITORIO
```

### 2. Crie o ambiente virtual Python

O ambiente virtual isola as dependências do projeto e evita conflitos com outros projetos Python instalados no seu computador.

**Windows (Prompt de Comando ou PowerShell):**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

Você saberá que o ambiente está ativo quando o terminal mostrar `(venv)` no início da linha.

### 3. Instale as dependências

```bash
pip install -r backend/requirements.txt
```

> ⏳ Pode demorar 2–3 minutos na primeira vez. Os pacotes `opencv` e `pillow` são pesados.

### 4. Configure as variáveis de ambiente

O arquivo `backend/.env` já está incluído com as credenciais do projeto narceu de paiva filho, então **não é necessário configurar nada** para rodar localmente.

Se quiser usar seu próprio banco Supabase:
```bash
cp backend/.env.example backend/.env
# Edite backend/.env com sua SUPABASE_URL e SUPABASE_KEY
```

---

## Rodando o projeto

Com o ambiente virtual ativo, execute:

```bash
python backend/app.py
```

Você verá no terminal:
```
🚀 Biblioteca narceu de paiva filho v3 — http://localhost:5000
[supabase] ✅ Conectado com sucesso.
```

**ou** (se o Supabase não estiver disponível):
```
🚀 Biblioteca narceu de paiva filho v3 — http://localhost:5000
[supabase] ⚠️  Falha: ... — usando dados locais (JSON).
```

Em ambos os casos, abra **http://localhost:5000** no navegador.

> O backend serve o frontend automaticamente. Não é necessário abrir nenhum outro servidor.

---

## Login

O sistema possui **dois jeitos de entrar**:

### 1. Usuário e senha (administradores)

| Usuário | Senha | Papel |
|---------|-------|-------|
| `admin` | `narceu2026` | Administrador (acesso total) |
| `biblioteca` | `narceu2026` | Bibliotecária (acesso total) |

Esses são os usuários "reais" do sistema. Em **Configurações → Minha carteirinha de acesso**, qualquer um deles pode gerar uma **carteirinha PNG** com seu nome, usuário, senha e um **QR Code** que permite entrar direto na tela de login sem digitar nada (botão "Entrar com carteirinha").

### 2. Carteirinha com QR Code (Bibliotecário)

Qualquer **aluno** pode receber o título de **Bibliotecário** — veja [Acesso de Bibliotecário](#acesso-de-bibliotecário-para-alunos) abaixo. Depois disso, ele entra escaneando a própria carteirinha (QR) na tela de login, vendo a mensagem **"Você entrou como Bibliotecário"**.

---

## Acesso de Bibliotecário (para alunos)

Em **Alunos**, cada linha tem um botão **"Permitir acesso"** (ícone de carteirinha). Ao clicar:

- O aluno ganha o **título de Bibliotecário** (badge verde aparece ao lado do nome).
- A partir daí, ele pode entrar no sistema **escaneando a própria carteirinha** na tela de login.
- Clique no mesmo botão (agora vermelho) para **revogar** o acesso quando necessário.

### O que um Bibliotecário pode fazer

| Ação | Permitido? |
|------|-----------|
| Ver o acervo (Acervo) | ✅ |
| Cadastrar / editar / excluir livros | ❌ |
| Registrar novo empréstimo ("pegar") | ✅ |
| Registrar devolução | ✅ |
| Renovar empréstimo | ✅ |
| Cadastrar/editar Alunos, Salas, Gêneros | ❌ |
| Relatórios / Configurações | ❌ |

O menu lateral mostra apenas **Painel, Empréstimos e Acervo** para o Bibliotecário — as demais opções ficam ocultas.

---

## Câmera no topo (canto superior direito)

Em qualquer página do sistema, há um botão de **câmera** no topo direito. Ao clicar:

1. A câmera do dispositivo abre para ler um **QR Code**.
2. Se o código for a **carteirinha de um aluno**, abre o **Histórico do aluno** com:
   - Dados do aluno (nome, turma, sala, status).
   - **Empréstimos ativos**, cada um com botões **Renovar** e **Devolver**.
   - Um bloco **"Pegar livro emprestado"** para registrar um novo empréstimo na hora (buscar por título/ISBN ou escanear o livro).
   - Histórico completo de empréstimos anteriores.
3. Se o código for de um **livro**, mostra a disponibilidade de exemplares.

---

## O que testar

O projeto já vem com **dados de demonstração** prontos nos arquivos `backend/data/`.

| Funcionalidade | Como acessar |
|----------------|--------------|
| **Painel** | Tela inicial após login — métricas e empréstimos ativos |
| **Empréstimo atrasado** | Painel — aparece em vermelho (2 alunos com atraso) |
| **Devolver livro** | Painel → botão "Devolver" em qualquer linha |
| **Acervo** | Menu "Acervo" — 8 livros com gêneros e exemplares |
| **Novo livro** | Acervo → botão "Novo livro" — gera QR Code automaticamente |
| **Ver exemplares** | Acervo → botão `[lista]` em qualquer livro |
| **QR Code** | Acervo → botão `[qr]` — gera QR para impressão |
| **Cartão** | Acervo → botão `[impressora]` — abre cartão imprimível |
| **Alunos** | Menu "Alunos" — 6 alunos em 3 turmas |
| **Permitir acesso (Bibliotecário)** | Alunos → botão `[carteirinha]` em qualquer linha |
| **Histórico do aluno (com ações)** | Alunos → botão `[relógio]`, ou escanear a carteirinha na câmera do topo |
| **Renovar empréstimo** | Histórico do aluno → botão "Renovar" em um empréstimo ativo |
| **Pegar livro pelo histórico** | Histórico do aluno → bloco "Pegar livro emprestado" |
| **Câmera do topo** | Qualquer página → ícone de câmera no canto superior direito |
| **Novo empréstimo** | Menu "Empréstimos" → aba "Novo" → buscar livro pelo ISBN ou título → buscar aluno |
| **Minha carteirinha (admin)** | Configurações → "Gerar minha carteirinha" — gera PNG com nome, senha e QR de login |
| **Login por QR Code** | Tela de login → "Entrar com carteirinha (QR Code)" |
| **Salas** | Menu "Salas" — 3 salas cadastradas |
| **Gêneros** | Menu "Gêneros" — 5 gêneros com cores |
| **Relatórios** | Menu "Relatórios" — gráficos com atualização automática a cada 15s |
| **Exportar CSV** | Relatórios → botões "Exportar atrasados" e "Exportar histórico" |
| **Importar alunos** | Alunos → arrastar arquivo `.csv` na área indicada |
| **Testar conexão** | Menu "Configurações" → botão "Testar conexão" |

### Dados de demonstração incluídos

- **8 livros** — Informática, Literatura Brasileira, Matemática, Engenharia, Ficção Científica
- **6 alunos** — 3 turmas (INFO3A, ELET2B, EDIF1C) e 3 salas
- **6 empréstimos** — 2 ativos, 2 atrasados (em vermelho), 2 devolvidos
- **5 gêneros** com cores e ícones
- **3 salas** com capacidade

---

## Como funciona a conexão backend ↔ frontend

O backend Flask serve o frontend diretamente. Quando você acessa `http://localhost:5000`:

```
Navegador → http://localhost:5000
    ↓
Backend Flask (porta 5000)
    ├── GET /             → serve frontend/index.html
    ├── GET /assets/...   → serve arquivos CSS/JS do frontend
    └── GET /api/...      → responde com JSON (API)
```

O frontend descobre automaticamente onde está o backend:
```js
// assets/js/api.js
const API_BASE = window.location.origin + "/api";
// Em desenvolvimento: http://localhost:5000/api
// Em produção: https://seu-servidor.com/api
```

Isso significa que **não é necessário configurar nenhuma URL** — o sistema funciona em qualquer servidor ou porta automaticamente.

---

## Modo offline

Se o Supabase estiver indisponível (sem internet, credenciais expiradas, etc.), o sistema funciona completamente com os arquivos JSON em `backend/data/`:

| Arquivo | Conteúdo |
|---------|---------|
| `livros.json` | Acervo de livros |
| `alunos.json` | Cadastro de alunos |
| `emprestimos.json` | Histórico de empréstimos |
| `salas.json` | Salas cadastradas |
| `generos.json` | Gêneros de livros |

Todas as operações (criar, editar, deletar, emprestar, devolver, renovar, conceder acesso de Bibliotecário) funcionam no modo offline. O painel mostra `⚠️ Offline — cache local` quando o Supabase não está disponível.

> 💡 **Coluna `is_librarian` e `renovacoes`:** se você usa Supabase, o sistema funciona mesmo sem essas colunas na tabela `alunos`/`emprestimos` — nesse caso, o título de Bibliotecário e o contador de renovações são salvos automaticamente nos arquivos JSON locais como fallback. Para persistir tudo no Supabase, adicione `is_librarian boolean default false` em `alunos` e `renovacoes integer default 0` em `emprestimos`.

---

## Estrutura de pastas

```
.
├── README.md
├── .gitignore
├── backend/
│   ├── app.py                  ← entrada do servidor Flask
│   ├── requirements.txt        ← dependências Python
│   ├── .env                    ← credenciais (não vai ao GitHub)
│   ├── .env.example            ← modelo de credenciais
│   ├── api/
│   │   ├── _helpers.py         ← funções compartilhadas (leitura JSON, etc.)
│   │   ├── books.py            ← CRUD livros
│   │   ├── students.py         ← CRUD alunos + importação CSV
│   │   ├── loans.py            ← empréstimos e devoluções
│   │   ├── reports.py          ← gráficos e exportação CSV
│   │   ├── rooms.py            ← CRUD salas
│   │   └── genres.py           ← CRUD gêneros
│   ├── scanner/
│   │   └── routes.py           ← QR Code: geração, leitura e cartão PNG
│   ├── utils/
│   │   ├── supabase_client.py  ← conexão Supabase + modo offline
│   │   └── helpers.py          ← datas, IDs, status de empréstimo
│   └── data/                   ← dados locais (fallback offline)
│       ├── livros.json
│       ├── alunos.json
│       ├── emprestimos.json
│       ├── salas.json
│       └── generos.json
└── frontend/
    ├── index.html              ← SPA (página única)
    └── assets/
        ├── css/main.css
        └── js/
            ├── api.js          ← comunicação com o backend
            ├── app.js          ← autenticação, navegação, empréstimo
            ├── store.js        ← estado global + localStorage
            ├── utils.js        ← datas, toast, modal, DOM
            ├── charts.js       ← gráficos Chart.js
            ├── qr-scanner.js   ← câmera do browser → QR
            └── pages/
                ├── books.js
                ├── students.js
                ├── loans.js
                ├── rooms.js
                └── genres.js
```

---

## Endpoints da API

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/health` | Status da conexão |
| GET | `/api/books/` | Listar livros (filtros: `q`, `genre`) |
| POST | `/api/books/` | Criar livro |
| PUT | `/api/books/<id>` | Editar livro |
| DELETE | `/api/books/<id>` | Excluir livro |
| GET | `/api/students/` | Listar alunos (filtros: `q`, `class`, `sala_id`) |
| POST | `/api/students/` | Criar aluno |
| PUT | `/api/students/<id>` | Editar aluno |
| DELETE | `/api/students/<id>` | Excluir aluno |
| PATCH | `/api/students/<id>/access` | Conceder/revogar acesso de Bibliotecário |
| POST | `/api/students/import/csv` | Importar alunos em lote |
| GET | `/api/loans/` | Listar empréstimos (filtro: `status`) |
| POST | `/api/loans/` | Criar empréstimo |
| POST | `/api/loans/<id>/return` | Registrar devolução |
| POST | `/api/loans/<id>/renew` | Renovar empréstimo (estende prazo, `dias` no body) |
| GET | `/api/reports/chart-summary` | Dados para gráfico de pizza |
| GET | `/api/reports/top-books` | Top livros mais emprestados |
| GET | `/api/reports/by-class` | Empréstimos por turma |
| GET | `/api/reports/export/overdue` | CSV — empréstimos atrasados |
| GET | `/api/reports/export/all` | CSV — histórico completo |
| GET | `/api/rooms/` | Listar salas |
| POST | `/api/rooms/` | Criar sala |
| PUT | `/api/rooms/<id>` | Editar sala |
| DELETE | `/api/rooms/<id>` | Excluir sala |
| GET | `/api/genres/` | Listar gêneros |
| POST | `/api/genres/` | Criar gênero |
| PUT | `/api/genres/<id>` | Editar gênero |
| DELETE | `/api/genres/<id>` | Excluir gênero |
| POST | `/api/qr/decode` | Decodificar imagem QR |
| POST | `/api/qr/generate` | Gerar QR Code PNG |
| GET | `/api/qr/card/book/<id>` | Cartão imprimível do livro |
| GET | `/api/qr/card/student/<id>` | Carteirinha do aluno |
| GET | `/api/qr/card/admin/<login>` | Carteirinha do administrador (nome, senha e QR de login) |
| POST | `/api/qr/login` | Resolve carteirinha escaneada → admin / bibliotecário / negado |

---

## Problemas comuns

**`(venv)` não aparece no terminal**
O ambiente virtual não está ativo. Execute:
- Windows: `venv\Scripts\activate`
- Mac/Linux: `source venv/bin/activate`

**`ModuleNotFoundError: No module named 'flask'`**
O ambiente virtual não está ativo ou as dependências não foram instaladas. Execute:
```bash
# Ativar o venv (veja acima) e depois:
pip install -r backend/requirements.txt
```

**`Port 5000 already in use`**
Outra aplicação está usando a porta 5000. Mude no `backend/.env`:
```
FLASK_PORT=5001
```

**Tela em branco no navegador**
Aguarde 2–3 segundos e recarregue. O Flask pode demorar um pouco para iniciar. Verifique também se o terminal mostra `🚀 Biblioteca narceu de paiva filho v3`.

**`[supabase] ⚠️ Falha`** no terminal
Normal para ambiente sem internet. O sistema usa os dados locais automaticamente. Nenhuma ação necessária.

**QR Code não lê pela câmera do servidor**
Requer `pyzbar` instalado. No Windows pode ser necessário instalar [Visual C++ Redistributables](https://aka.ms/vs/17/release/vc_redist.x64.exe). A leitura pela câmera do **navegador** funciona sem dependências extras.

**Erro ao importar CSV**
Verifique se o arquivo usa `;` ou `,` como separador e se tem as colunas `nome`, `turma`, `carteirinha`. Veja o modelo em `backend/data/alunos_exemplo.csv`.

---

*Projeto acadêmico — narceu de paiva filho Campus Aracruz*