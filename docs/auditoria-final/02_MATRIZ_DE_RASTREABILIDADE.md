# 02 — Matriz de rastreabilidade

Os campos abaixo ligam funcionalidade a arquivos, endpoints, persistência e
testes existentes. “Resultado” descreve somente o que foi executado nesta
auditoria. Teste mockado não é integração real.

| Funcionalidade | Arquivos/funções centrais | Endpoint/banco | Teste existente e resultado atual |
|---|---|---|---|
| Health | `backend/app.py:health` | `GET /api/health`; sem banco | `test_health_endpoints.py`: passou |
| Readiness | `backend/app.py:readiness` | `GET /api/ready`; consulta `livros` | `test_health_endpoints.py`: mock banco online/offline passou |
| Login credencial | `api/auth.py:login`, `_verify_password` | `POST /api/auth/login`; `usuarios` | testes auth no conjunto; suite não informa por nome todos os 180 aprovados |
| Autoatendimento | `auth.py:self_service_*`, `controle.py` | `/api/auth/self-service/*`; `alunos`, `emprestimos`, `livros`, JSON config | dois casos de busca de carteirinha falharam; restante parcial por conjunto |
| CRUD livro | `api/books.py:create_book/update_book/delete_book` | `/api/books/*`; `livros`, `emprestimos` | `test_unique_identifiers.py` falhou por resposta 503; não validou persistência |
| ISBN textual | `api/books.py:_lookup_isbn`, providers | `GET /api/books/isbn-lookup` | `test_isbn_lookup.py`; providers externos não foram chamados |
| ISBN Vision | `_vision_isbn_from_image` | `POST /api/books/isbn-vision`; APIs Groq/OpenAI | quatro testes Groq falharam antes do SDK por chave não configurada |
| Alunos/CSV | `api/students.py` | `/api/students/*`; `alunos`, `salas` | testes indiretos no conjunto; nenhuma escrita real |
| Permissão bibliotecário | `students.toggle_librarian_access`, `scanner.qr_login` | PATCH/POST `/api/students/<id>/access`; `alunos.is_librarian` | não executado como requisição autenticada/anônima; achado estático |
| Empréstimo | `loans._create_loan_record`, `_available_copies*` | `POST /api/loans/`; `emprestimos`, `livros`, `alunos` | testes unitários existentes; sem corrida real; middleware exige banco |
| Renovação/devolução | `loans.renew_loan`, `return_loan` | `/api/loans/<id>/{renew,return}`; `emprestimos` | testes locais/mocks existentes; sem transação/banco real |
| QR decode/resolução | `scanner.decode_image`, `_resolve_qr` | `POST /api/qr/decode`; `livros`, `alunos` | dois casos falharam por 503; decode físico não foi testado |
| Salas/gêneros | `api/rooms.py`, `genres.py` | CRUD `/api/rooms`, `/api/genres`; `salas`, `generos` | sem validação funcional isolada; banco real não testado |
| Relatórios/CSV | `api/reports.py:_build_report_data`, `_csv_resp` | `/api/reports/*`; várias tabelas | três casos falharam por 503; tests Node de relatórios passaram |
| Browser e modais | `app.js`, páginas, `utils.js` | chamadas cliente `API.*` | Node passou; sem navegador visual/E2E |
| Scanner frontend | `qr-scanner.js` | APIs nativas/`jsQR`, fallback `POST /api/qr/decode` | teste Node passou com mocks, sem câmera física |
| Supabase/RLS | `supabase_client.py`, `database.sql` | PostgREST/PostgreSQL | nenhum acesso ao banco; bloqueado |

## Resultado

Esta tabela não prova cobertura completa. Quatro falhas de visão e oito falhas de
rota estão discriminadas em [13_EVIDENCIAS.md](13_EVIDENCIAS.md). Operações de
escrita foram apenas exercitadas pelos testes existentes; nenhuma escrita foi
feita em banco real.
