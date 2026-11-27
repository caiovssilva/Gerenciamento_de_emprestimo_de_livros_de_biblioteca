# 01 — Inventário de funcionalidades identificadas

Inventário baseado em rotas Flask, chamadas do cliente HTTP, scripts carregados
por `frontend/index.html`, módulos de página e testes existentes. “Identificada”
não significa “validada funcionalmente”.

| Domínio | Funcionalidade identificada | Fontes principais |
|---|---|---|
| Inicialização | Flask, variáveis de ambiente, CORS, CSP, registro de blueprints e frontend estático | `backend/app.py` |
| Saúde | Health check e readiness Supabase | `backend/app.py` |
| Login de staff | Login por credenciais e sessão de papel admin/bibliotecário | `backend/api/auth.py`, `frontend/assets/js/app.js` |
| QR de staff | QR administrativo e QR de aluno que tenha flag bibliotecário | `backend/scanner/routes.py` |
| Autoatendimento | Ativar/configurar permissões, login de aluno, token, histórico, catálogo disponível, empréstimo, renovação, devolução e logout | `backend/api/auth.py`, `controle.py`, `loans.py` |
| Livros | Listagem/filtro, leitura individual, criação, edição, exclusão e gestão individual de exemplares | `backend/api/books.py`, `frontend/assets/js/pages/books.js` |
| ISBN | Validação, consulta manual/scanner, cache e fontes bibliográficas alternativas | `backend/api/books.py`, `frontend/assets/js/pages/books.js` |
| Visão | Envio de frame para Groq/OpenAI e normalização do ISBN | `backend/api/books.py`, `frontend/assets/js/qr-scanner.js` |
| Alunos | Listagem/filtros, leitura individual, cadastro, edição, exclusão lógica/física conforme schema, flag bibliotecário, importação CSV | `backend/api/students.py`, `frontend/assets/js/pages/students.js` |
| Empréstimos | Listagem/filtro, leitura individual, criação, escolha/disponibilidade de exemplar, renovação, devolução | `backend/api/loans.py`, `frontend/assets/js/pages/loans.js` |
| Salas | CRUD e associação com alunos | `backend/api/rooms.py`, `frontend/assets/js/pages/rooms.js` |
| Gêneros | CRUD e associação com livros | `backend/api/genres.py`, `frontend/assets/js/pages/genres.js` |
| Relatórios | Resumos de gráficos, ranking, turma, mensais, geração mensal, CSV de atrasos/histórico/livros/turma/alunos/status | `backend/api/reports.py`, `frontend/assets/js/reports.js`, `charts.js` |
| QR/câmera | Scanner de browser, decode de imagem no backend, geração de QR, cartões de livro/aluno/admin, scanner de câmera no servidor | `frontend/assets/js/qr-scanner.js`, `backend/scanner/routes.py` |
| Configuração | Estado de permissões de autoatendimento em JSON e endpoints legados de configuração Supabase | `backend/api/controle.py`, `auth.py`, `app.py` |
| Estado visual | Store em memória/localStorage, navegação, modais, mensagens, tema e painéis | `frontend/assets/js/app.js`, `store.js`, `utils.js` |

## Contagem de rotas declaradas

Busca estática encontrou 70 decoradores de rota: 7 em `app.py`, 11 em auth,
8 books, 7 students, 5 loans, 12 reports, 5 rooms, 4 genres, 1 controle e 10 QR.
Aliases e caminhos de catch-all podem gerar múltiplas URLs por função. Essa
contagem não é resultado de enumeração HTTP dinâmica.

## O que falta para inventário exaustivo

Não foi feita inspeção visual de todos os 109 controles HTML contados por
`rg`, nem rastreamento de cada callback/ramo/entrada. Não se afirma que toda
funcionalidade secundária foi testada; as subseções funcionais devem ser lidas
junto com a matriz de rastreabilidade e os status reais.
