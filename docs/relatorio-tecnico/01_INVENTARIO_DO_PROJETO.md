# 01 — Inventário do projeto

## Identificação observada

- Repositório: `Gerenciamento_de_emprestimo_de_livros_de_biblioteca`.
- Branch no início da inspeção: `fix/login-error-message`.
- `git status --short` estava vazio antes da auditoria.
- Aplicação web de biblioteca: Flask/Python no servidor, HTML/CSS/JavaScript
  estático no cliente e Supabase/PostgreSQL no caminho de dados principal.
- A documentação antiga já existente na raiz não foi sobrescrita; este conjunto
  novo foi criado em `docs/relatorio-tecnico/`.

## Arquivos e diretórios relevantes

| Caminho | Responsabilidade e relações | Situação observada |
|---|---|---|
| `backend/app.py` | Cria Flask, carrega dotenv, registra blueprints, middleware, erros, health/readiness e frontend estático. | Inicializador confirmado |
| `backend/api/auth.py` | Login administrativo e autoatendimento; assinatura/validação de token; config Supabase. | Rotas registradas |
| `backend/api/books.py` | CRUD, exemplares e consulta de ISBN/visão; consome provedores externos e Supabase. | Rotas registradas |
| `backend/api/students.py` | CRUD/importação CSV e alteração de flag de bibliotecário. | Rotas registradas |
| `backend/api/loans.py` | Disponibilidade, empréstimo, renovação e devolução. | Rotas registradas |
| `backend/api/reports.py` | Agregações e exportações CSV. | Rotas registradas |
| `backend/api/rooms.py`, `genres.py` | CRUD de salas e gêneros. | Rotas registradas |
| `backend/api/controle.py` | Configura permissões de autoatendimento em JSON local. | Rotas registradas |
| `backend/api/_helpers.py` | Leitura/escrita JSON, detecção de schema, cache de introspecção e erros. | Importado pelos módulos |
| `backend/utils/supabase_client.py` | Criação/cache do cliente e adaptador de consultas Supabase. | Importado pelo backend |
| `backend/utils/helpers.py` | IDs UUID, datas e estado de empréstimo. | Importado pelos módulos |
| `backend/scanner/routes.py` | Decodificação, resolução e geração de QR, carteirinhas e estado de câmera. | Blueprint registrado |
| `backend/data/*.json` | Dados locais e configuração do autoatendimento. Há leituras/escritas de fallback em vários módulos. | Versionados; não são a fonte principal garantida |
| `database.sql` | DDL, RLS, índices, views e dados iniciais. | Script SQL presente; não foi executado |
| `frontend/index.html` | SPA, marcação e carregamento de CSS/scripts/CDNs. | Servido pelo Flask |
| `frontend/assets/js/api.js` | Cliente HTTP `fetch` e catálogo de endpoints. | Carregado pela página |
| `frontend/assets/js/app.js` | Sessão visual, navegação, inicialização e orquestração das telas. | Carregado pela página |
| `frontend/assets/js/store.js` | Estado em memória e cópia no localStorage. | Carregado pela página |
| `frontend/assets/js/utils.js` | Datas, DOM, toast, modais e interações comuns. | Carregado pela página |
| `frontend/assets/js/pages/*.js` | Telas de livros, alunos, empréstimos, salas e gêneros. | Carregados explicitamente |
| `frontend/assets/js/qr-scanner.js`, `charts.js`, `reports.js` | Scanner de câmera, gráficos e exportação/apresentação de relatórios. | Carregados explicitamente |
| `backend/tests/*.py` | Testes de endpoints e funções Python, em geral com mocks. | Executados nesta auditoria |
| `frontend/tests/*.test.js` | Testes Node para comportamentos de API, telas, QR, CRUD e relatórios. | Executados nesta auditoria |
| `.github/workflows/*.yml` | Ping periódico do Render e consulta ao Supabase usando GitHub Secrets. | Configuração estática examinada |
| `backend/requirements.txt` | Dependências Python declaradas; a raiz `requirements.txt` apenas inclui esse arquivo. | Manifesto presente |
| `package-lock.json` | Lock npm sem pacotes (`packages: {}`). | Não demonstra dependências npm instaladas |

## Estrutura resumida

```text
backend/
  api/          blueprints e regras HTTP
  scanner/      QR e imagem
  utils/        cliente Supabase e utilitários
  data/         JSON locais/fallback
  tests/        pytest
frontend/
  assets/js/    SPA JavaScript sem framework de componentes
  assets/css/   estilos
  tests/        node:test
database.sql    schema e seed
docs/           relatórios desta auditoria
```

O inventário foi feito por arquivos do workspace e referências diretas. Não foi
feita prova dinâmica de carregamento de cada arquivo isoladamente; “carregado”
significa que existe import, registro, script tag, rota ou referência explícita.
