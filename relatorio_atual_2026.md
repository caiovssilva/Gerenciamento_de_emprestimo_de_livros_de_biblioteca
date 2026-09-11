# Relatório Técnico Definitivo

**Projeto:** Gerenciamento de Empréstimo de Livros de Biblioteca  
**Data da auditoria:** 2026-08-23  
**Fonte de verdade:** código, SQL, dependências e testes presentes no repositório. README, comentários e relatórios anteriores não são prova.

## 1. VEREDITO GERAL

A aplicação é um sistema Flask que serve frontend HTML/CSS/JavaScript e APIs para livros, alunos, salas, gêneros, empréstimos, relatórios e QR. Supabase é o caminho principal; os módulos usam JSON local como fallback.

Há autenticação de credenciais e login por QR, mas não há sessão, cookie, token ou JWT. Após o login, o papel fica apenas em `currentUser` no navegador. A maior parte das restrições por papel é visual e as APIs de negócio não exigem autenticação.

## 2. PRINCIPAIS CORREÇÕES EM RELAÇÃO À VERSÃO ANTERIOR

- `access` é classificação (`admin`/`librarian`), não token.
- JWT, sessão, cookie e Bearer não foram encontrados.
- O backend valida credenciais, mas não aplica RBAC às rotas CRUD/relatórios.
- Login comum consulta `usuarios` no Supabase; não há fallback para usuários dos JSONs.
- QR `ADMIN-*` concede login administrativo direto; QR de aluno comum é identificação e pode ser negado.
- O scanner normal decodifica no navegador com `jsQR`/`BarcodeDetector`; `/api/qr/decode` é caminho separado.
- Fallback local não faz reconciliação com Supabase quando a conexão volta.
- `localStorage` é cache, não sessão nem fila offline.
- `SECRET_KEY` é definida, mas não foi encontrada sendo usada para sessão.
- CORS é aberto e a CSP permite `unsafe-inline`; o SQL semeia senha em texto puro.

## 3. VISÃO GERAL DO PROJETO

A entrada é [`backend/app.py`](backend/app.py#L1-L151): carrega `.env`, cria Flask, registra blueprints, aplica CORS/CSP e serve [`frontend/index.html`](frontend/index.html#L1-L485). APIs e persistência ficam em `backend/`; a interface fica em `frontend/`.

## 4. INVENTÁRIO COMPLETO

Backend: `app.py`, `api/auth.py`, `books.py`, `students.py`, `loans.py`, `rooms.py`, `genres.py`, `reports.py`, `api/_helpers.py`, `scanner/routes.py`, `utils/supabase_client.py` e `utils/helpers.py`. Frontend: `index.html`, CSS, `app.js`, `api.js`, `store.js`, `qr-scanner.js`, `charts.js`, `utils.js`, `pages/*.js` e `lib/supabase-config.js`. Dados: cinco JSONs em `backend/data/`. Testes: 11 Python e 1 JavaScript.

## 5. ESTRUTURA DE PASTAS

`backend/` contém servidor, APIs, scanner, utilitários, dados e testes. `frontend/` contém shell, estilos e scripts. `database.sql` contém schema, políticas, views e seeds. Não foi encontrado `package.json` com dependências efetivas de frontend.

## 6. TECNOLOGIAS REALMENTE UTILIZADAS

Python/Flask em [`app.py`](backend/app.py#L5-L37); Flask-CORS em [`app.py`](backend/app.py#L47-L47); `python-dotenv` em [`app.py`](backend/app.py#L17-L21); Supabase e JSON em [`supabase_client.py`](backend/utils/supabase_client.py#L44-L153) e [`_helpers.py`](backend/api/_helpers.py#L17-L39); QR/Pillow/OpenCV/NumPy/Pyzbar em [`routes.py`](backend/scanner/routes.py#L10-L154); Passlib/bcrypt/crypt em [`auth.py`](backend/api/auth.py#L5-L75); JavaScript vanilla, Chart.js, jsQR e Tabler Icons referenciados por [`index.html`](frontend/index.html#L10-L16).

## 7. TECNOLOGIAS DECLARADAS MAS NÃO CONFIRMADAS COMO UTILIZADAS

`gunicorn` está em [`backend/requirements.txt`](backend/requirements.txt#L1-L12), mas não há comando ou configuração de produção confirmada. `pytest` é usado pelos testes, mas não aparece nos requirements. `DATABASE_MODE` aparece no modelo de ambiente, mas não é lido. O cliente Supabase do frontend é preparado, mas não há biblioteca carregada nem uso efetivo confirmado. JWT/PyJWT/flask-jwt/Bearer/Authorization não têm implementação real. [NÃO IMPLEMENTADO]

## 8. ARQUITETURA REAL

Flask serve frontend e API no mesmo processo; os blueprints são registrados em [`app.py`](backend/app.py#L24-L59). Cada endpoint escolhe Supabase ou JSON dentro da própria operação. O frontend usa scripts clássicos, estado em memória e páginas mostradas/ocultadas; não há roteador SPA real.

## 9. FRONTEND COMPLETO

`index.html` define login, navegação, páginas e modais. `app.js` coordena autenticação, navegação, sync e empréstimos. `api.js` encapsula `fetch`; `store.js` mantém snapshots; `pages/*.js` renderiza entidades; `charts.js` consulta relatórios; `qr-scanner.js` controla câmera local.

## 10. BACKEND COMPLETO

`auth.py` trata login/configuração; `books.py`, `students.py`, `rooms.py` e `genres.py` tratam CRUD; `loans.py` trata disponibilidade, empréstimo, devolução e renovação; `reports.py` agrega dados/CSV; `scanner/routes.py` trata QR e cartões; helpers tratam JSON e cliente Supabase.

## 11. API E COMUNICAÇÃO

`apiFetch()` monta URL `/api`, envia JSON, interpreta resposta, lança erro em status não-2xx e registra no console em [`api.js`](frontend/assets/js/api.js#L6-L28). Há contratos para livros, alunos, empréstimos, relatórios, salas, gêneros, QR e health em [`api.js`](frontend/assets/js/api.js#L30-L84). Exportações usam URLs diretas.

## 12. BANCO DE DADOS

[`database.sql`](database.sql#L19-L153) cria `usuarios`, `salas`, `generos`, `livros`, `alunos`, `emprestimos` e `relatorios_mensais`. Há UUIDs, FKs, índices, JSONB de exemplares, unicidade parcial de carteirinha/exemplar ativo, `deleted_at` e contador de renovações.

## 13. SUPABASE

`get_client()` lê URL e chave, prioriza `SUPABASE_SERVICE_KEY`, cria e cacheia o cliente em [`supabase_client.py`](backend/utils/supabase_client.py#L44-L141). `sb_exec()` converte resposta em dados e erros em exceções em [`supabase_client.py`](backend/utils/supabase_client.py#L143-L153). Criar o cliente não testa conectividade real; a falha pode surgir na consulta.

## 14. POSTGRESQL

O SQL usa recursos PostgreSQL/Supabase: UUID, JSONB, índices parciais, `FILTER`, `CURRENT_DATE` e views em [`database.sql`](database.sql#L84-L153). O backend não abre conexão PostgreSQL diretamente e não consulta as views; usa tabelas via Supabase.

## 15. FALLBACK JSON

`read_json()` cria arquivo ausente e retorna lista vazia em erro; `write_json()` serializa e silencia falhas em [`_helpers.py`](backend/api/_helpers.py#L17-L39). Endpoints tentam Supabase e caem em `livros.json`, `alunos.json`, `emprestimos.json`, `salas.json` ou `generos.json`. Não existe fila, merge, marcação pendente ou upload posterior. Há risco real de divergência, perda silenciosa, duplicação após falha de resposta e corrida de exemplares.

## 16. RECONEXÃO

Após falha de criação, `get_client()` marca offline; durante 60 segundos retorna `_OfflineClient`, e depois tenta criar cliente novamente em [`supabase_client.py`](backend/utils/supabase_client.py#L119-L141). [`test_supabase_reconnect.py`](backend/tests/test_supabase_reconnect.py#L8-L39) cobre essa janela. Reconectar cliente não migra dados locais.

## 17. SINCRONIZAÇÃO DE DADOS

`_finishLogin()` chama `syncAll()`; `syncData()` busca livros, alunos e empréstimos, grava `Store` e, em falha, chama `loadLocal()` em [`app.js`](frontend/assets/js/app.js#L161-L188) e [`app.js`](frontend/assets/js/app.js#L282-L299). Não há sincronização bidirecional nem listener `storage`; sincronização entre abas não foi confirmada.

## 18. AUTENTICAÇÃO REAL

`doLogin()` envia `POST /api/auth/login` em [`app.js`](frontend/assets/js/app.js#L57-L100). `login()` normaliza login, busca usuário e valida senha em [`auth.py`](backend/api/auth.py#L113-L148). `_verify_password()` aceita Passlib, bcrypt/crypt e texto puro sem `$` em [`auth.py`](backend/api/auth.py#L43-L75); após sucesso tenta re-hash, ignorando falha, em [`auth.py`](backend/api/auth.py#L151-L174).

A resposta contém `access`, `id`, `login` e `name`. O frontend grava objeto em `currentUser`; não persiste usuário e não cria sessão, cookie, token, JWT ou restauração após recarregar.

## 19. AUTORIZAÇÃO E PERMISSÕES REAIS

Criar/editar/excluir livros, alunos, salas e gêneros; criar/devolver/renovar empréstimos; acessar relatórios e alterar acesso de aluno não exige papel ou sessão nas rotas. Há apenas validações de dados e regras de negócio, como `create_loan()` em [`loans.py`](backend/api/loans.py#L82-L128). O frontend esconde páginas de bibliotecário em [`app.js`](frontend/assets/js/app.js#L191-L203), o que não protege a API. A devolução compara aluno apenas quando uma referência é fornecida em [`loans.py`](backend/api/loans.py#L164-L181). Administração de usuários não foi implementada.

## 20. JWT: EXISTE OU NÃO?

JWT não é usado. A busca por `jwt`, `PyJWT`, `flask_jwt`, `flask_jwt_extended`, `encode`, `decode`, `access_token`, `refresh_token`, Bearer e `Authorization` não encontrou implementação real. `access` em [`auth.py`](backend/api/auth.py#L179-L187) é somente classificação. [NÃO IMPLEMENTADO]

## 21. RBAC: EXISTE OU NÃO?

RBAC backend não existe. Há papéis calculados no login, `is_librarian` no aluno e ocultação visual. Não há middleware/decorator que imponha esses papéis às rotas. O login QR de bibliotecário está em [`routes.py`](backend/scanner/routes.py#L258-L281); a UI está em [`app.js`](frontend/assets/js/app.js#L191-L203).

## 22. LIVROS

`list_books()` filtra título/autor/ISBN/gênero em [`books.py`](backend/api/books.py#L27-L48). `create_book()` exige título/autor, usa `new_id()`, cria exemplares e persiste em [`books.py`](backend/api/books.py#L73-L113). `_build_exemplar_meta()` gera códigos `001`, IDs e `EXEMPLAR-...` em [`books.py`](backend/api/books.py#L12-L23). Atualização remove campos derivados; exclusão bloqueia empréstimo ativo.

## 23. ALUNOS

CRUD e filtros estão em [`students.py`](backend/api/students.py#L15-L191). Cadastro exige nome/turma, valida sala, cria carteirinha padrão e QR com o ID. CSV aceita `;` ou `,`, mapeia sala e evita carteirinhas repetidas em [`students.py`](backend/api/students.py#L193-L246). `is_librarian` pode ser alterado sem autenticação em [`students.py`](backend/api/students.py#L168-L191).

## 24. SALAS

`rooms.py` implementa CRUD, contagem de alunos e desvinculação ao excluir em [`rooms.py`](backend/api/rooms.py#L13-L95). Não há autorização e `codigo` não é unique no SQL observado.

## 25. GÊNEROS

`genres.py` implementa CRUD, contagem de livros e limpeza de `genero_id` ao excluir em [`genres.py`](backend/api/genres.py#L13-L74). Não há autorização nem unicidade de nome.

## 26. EMPRÉSTIMOS

`create_loan()` exige livro/aluno, confirma existência, chama `_available_copies()`, escolhe exemplar, calcula datas e grava em [`loans.py`](backend/api/loans.py#L82-L128). A verificação e gravação não formam transação no código; o índice SQL reduz conflito apenas no banco.

## 27. DEVOLUÇÕES

`return_loan()` rejeita empréstimo inexistente ou já devolvido, opcionalmente confere aluno, define `devolvido_em` e atualiza Supabase/JSON em [`loans.py`](backend/api/loans.py#L156-L202). `confirmDevolution()` chama a rota em [`app.js`](frontend/assets/js/app.js#L565-L597); a interface pode devolver sem enviar carteirinha.

## 28. RENOVAÇÕES

`renew_loan()` rejeita devolvidos, soma dias e incrementa `renovacoes` em [`loans.py`](backend/api/loans.py#L130-L154). O frontend chama a rota em [`app.js`](frontend/assets/js/app.js#L600-L635). Não há limite de renovações implementado.

## 29. QR CODE

Livro novo gera QR PNG com o ID em [`books.py`](backend/api/books.py#L105-L113); aluno novo gera QR com ID em [`students.py`](backend/api/students.py#L108-L118); exemplares usam `EXEMPLAR-<id>` em [`books.py`](backend/api/books.py#L12-L23). QR de identificação é distinto do QR `ADMIN-*`, que é aceito como credencial de login.

## 30. SCANNER

O caminho normal é câmera no navegador: `QRScanner.start()` usa `getUserMedia`, vídeo/canvas e intervalo de 600 ms; `_capture()` tenta jsQR e depois `BarcodeDetector` em [`qr-scanner.js`](frontend/assets/js/qr-scanner.js#L188-L319). `/api/qr/decode` tenta Pillow, Pyzbar e OpenCV em [`routes.py`](backend/scanner/routes.py#L102-L154). Endpoints de câmera no servidor também existem, mas não são chamados pelo fluxo frontend confirmado.

## 31. RELATÓRIOS

`reports.py` fornece resumo por status, ranking, turma, mensais e CSV de atrasados, histórico, livros, turma e status de alunos em [`reports.py`](backend/api/reports.py#L25-L189). Calcula sobre tabelas/JSON, não sobre as views SQL. Nenhum endpoint exige autenticação.

## 32. LOCALSTORAGE E ESTADO DO FRONTEND

`Store` mantém cinco arrays e grava `lib_books`, `lib_students`, `lib_loans`, `lib_rooms` e `lib_genres` em [`store.js`](frontend/assets/js/store.js#L4-L49). `loadLocal()` só ocorre no fallback de sync. `currentUser` fica apenas em memória. LocalStorage é cache, não sessão nem fila.

## 33. TRATAMENTO DE ERROS

Flask trata HTTP e exceções genéricas como JSON em [`app.py`](backend/app.py#L80-L95); `apiFetch()` propaga erros. Muitos `except:` amplos transformam falhas de schema/configuração em fallback ou ocultam problemas. JSON inválido vira lista vazia e escrita com erro é silenciosa.

## 34. SEGURANÇA REALMENTE IMPLEMENTADA

Há validação de senha no backend, headers CSP, `object-src 'none'`, `base-uri`, `frame-ancestors`, validações de campos e constraints SQL. Limitações confirmadas: CORS `*` em [`app.py`](backend/app.py#L47-L47); CSP com `unsafe-inline` em [`app.py`](backend/app.py#L63-L78); possibilidade de devolver service key em [`auth.py`](backend/api/auth.py#L192-L215); senha seed em texto puro em [`database.sql`](database.sql#L19-L27); QR admin sem segundo fator; ausência de autorização. `SECRET_KEY` usa fallback previsível em [`app.py`](backend/app.py#L37-L37), sem uso de sessão encontrado.

## 35. TESTES

Os testes cobrem login/alias, fallback de livros, ambiente, QR/resolução, exportação de status, reconexão e IDs únicos. O teste JavaScript cobre callback básico do scanner em [`frontend/tests/qr-scanner.test.js`](frontend/tests/qr-scanner.test.js#L123-L145). Não há cobertura confirmada para autorização, CRUD completo, empréstimo/devolução/renovação, concorrência, RLS, integração Supabase, câmera backend ou E2E. A suíte não foi executada nesta auditoria; aprovação não foi confirmada.

## 36. DEPENDÊNCIAS

As dependências backend estão em [`backend/requirements.txt`](backend/requirements.txt#L1-L12). QR usa qrcode/Pillow/OpenCV/NumPy/Pyzbar; servidor usa Flask/CORS/dotenv/Supabase; login usa Passlib/bcrypt/crypt. `gunicorn` é declarado, mas não confirmado no fluxo. Não há dependências npm efetivas confirmadas.

## 37. CONFIGURAÇÃO E INICIALIZAÇÃO

`load_environment()` carrega `backend/.env` antes dos blueprints em [`app.py`](backend/app.py#L17-L31). O servidor usa `PORT`/`FLASK_PORT`, debug conforme `FLASK_ENV` e host `0.0.0.0` em [`app.py`](backend/app.py#L137-L151). URL/chave operacional real e `backend/.env` não foram encontrados na árvore auditada.

## 38. MAPA DE IMPORTAÇÕES

`app.py` importa todos os blueprints; APIs importam cliente, IDs/datas/status e helpers; scanner usa dependências opcionais de visão; scripts dependem dos globais `API`, `Store`, `Utils`, `Charts` e `QRScanner`. Imports aparentemente não usados: `current_app` em `_helpers.py`, `json` em `reports.py`, `re` e `send_file` em `routes.py`. [POSSIVELMENTE NÃO UTILIZADO]

## 39. MAPA DE DADOS

`usuarios` alimenta login; `livros` acervo/relatórios; `alunos` identificação/empréstimos; `salas` vínculo escolar; `generos` categorização; `emprestimos` relações e datas; `relatorios_mensais` agregados. JSONs representam os mesmos domínios como fallback, mas podem divergir do schema. Exemplares são listas em JSON local e JSONB no banco.

## 40. FLUXO COMPLETO DO SISTEMA

Flask entrega shell; usuário autentica; `_finishLogin()` define estado, esconde login, sincroniza e navega. Listagens consultam API; API tenta Supabase/JSON; mutações persistem em um caminho e o frontend sincroniza/renderiza novamente. Não há continuidade autenticada entre requisições.

## 41. FLUXO COMPLETO DE LOGIN

1. `doLogin()` faz POST para `/api/auth/login` ([`app.js`](frontend/assets/js/app.js#L57-L100)).
2. `login()` busca usuário e chama `_verify_password()` ([`auth.py`](backend/api/auth.py#L113-L148)).
3. Pode tentar re-hash e retorna `access`, ID, login e nome ([`auth.py`](backend/api/auth.py#L151-L187)).
4. `_finishLogin()` guarda `currentUser` e sincroniza ([`app.js`](frontend/assets/js/app.js#L161-L188)).
5. Nenhuma requisição posterior leva credencial e nenhuma rota exige uma.

## 42. FLUXO COMPLETO DE EMPRÉSTIMO

1. `lookupBook()` pesquisa o `Store`, não `API.books.get()`, em [`app.js`](frontend/assets/js/app.js#L402-L463).
2. `lookupStudent()` ou `scanLoanStudent()` seleciona aluno em [`app.js`](frontend/assets/js/app.js#L475-L526).
3. `confirmLoan()` chama `API.loans.create()` em [`app.js`](frontend/assets/js/app.js#L528-L552).
4. `create_loan()` valida IDs, disponibilidade, exemplar e datas em [`loans.py`](backend/api/loans.py#L82-L113).
5. Persiste em Supabase ou `emprestimos.json` e retorna 201 ([`loans.py`](backend/api/loans.py#L114-L128)).
6. O frontend limpa formulário, sincroniza e renderiza o novo estado.

## 43. FLUXO COMPLETO DE QR CODE

`QRScanner` obtém câmera e decodifica localmente; o callback passa o texto a `resolveQRCode*`, que diferencia `ADMIN-*`, `EXEMPLAR-*`, ID, ISBN e carteirinha em [`app.js`](frontend/assets/js/app.js#L643-L696). Para login, `startQRLogin()` chama `/api/qr/login`; `_resolve_qr()` consulta Supabase e depois JSON, e `qr_login()` retorna admin, librarian ou denied em [`routes.py`](backend/scanner/routes.py#L166-L281). `/api/qr/decode` é fluxo separado.

## 44. PROBLEMAS E LIMITAÇÕES REAIS

Ausência de autorização API; QR admin como credencial portadora; CORS/CSP permissivos; chave padrão; senhas seed em texto puro; fallback sem reconciliação; exceções silenciosas; ausência de transação na escolha de exemplar; divergência JSON/schema; relatórios sem autenticação; `top-books` pode gerar 500 para `limit` não inteiro; login não funciona offline via JSON.

## 45. CÓDIGO POSSIVELMENTE NÃO UTILIZADO

No fluxo frontend observado, `API.qr.start`, `stop`, `result` e endpoints equivalentes não são chamados; o uso real é `QRScanner` local. [CONFIRMADO NO FLUXO OBSERVADO] `_read_local_record()`, imports listados na seção 38, views SQL e `supabase-config.js` são possivelmente não utilizados. Consumidores externos desses pontos não puderam ser excluídos.

## 46. CONTRADIÇÕES ENCONTRADAS E RESOLVIDAS

O relatório anterior dizia autorização server-side, mas o papel CRUD é visual. Dizia `lookupBook()` via API, mas ele pesquisa `Store`. Dizia `/api/qr/decode` no fluxo normal, mas o scanner usa jsQR/BarcodeDetector. Dizia sync entre abas e Supabase, mas não há listener, fila ou reconciliação. Dizia QR por `qr_id`, mas geração observada usa `id`. Dizia autenticação contínua/RBAC; não há sessão, token, middleware ou decorator.

## 47. ARQUIVOS MAIS IMPORTANTES

[`backend/app.py`](backend/app.py#L17-L151), [`backend/api/auth.py`](backend/api/auth.py#L43-L230), [`backend/utils/supabase_client.py`](backend/utils/supabase_client.py#L30-L153), [`backend/api/loans.py`](backend/api/loans.py#L12-L202), [`backend/api/books.py`](backend/api/books.py#L12-L160), [`backend/scanner/routes.py`](backend/scanner/routes.py#L102-L281), [`frontend/assets/js/app.js`](frontend/assets/js/app.js#L57-L758), [`frontend/assets/js/store.js`](frontend/assets/js/store.js#L4-L63) e [`database.sql`](database.sql#L19-L153).

## 48. ORDEM CORRETA PARA ESTUDAR O PROJETO

Leia `app.py`; `api.js` e `app.js`; `auth.py`; `supabase_client.py` e `_helpers.py`; `books.py`, `students.py`, `loans.py`, `reports.py`; `store.js` e páginas; `routes.py`, `qr-scanner.js`; `database.sql`; e testes.

## 49. PLANO PARA ENTENDER O PROJETO SOZINHO

1. Execute com ambiente Supabase conhecido e observe `/api/health`.
2. Inspecione Network no login e confirme ausência de token.
3. Compare respostas Supabase e JSON em ambiente isolado.
4. Siga `lookupBook()`, `scanLoanStudent()`, `confirmLoan()` e `create_loan()`.
5. Teste QR de ID, exemplar, aluno e `ADMIN-*` separadamente.
6. Execute testes e registre falhas reais.
7. Revise RLS, seeds de senha e constraints no Supabase.

## 50. CONCLUSÃO FINAL

O sistema é funcional para gestão básica de biblioteca, mas o código real não sustenta afirmações de JWT, sessão persistente, RBAC backend ou sincronização offline bidirecional. Os riscos prioritários são autorização ausente, QR administrativo sem prova adicional, exposição potencial de service key, senhas em texto puro, divergência entre armazenamentos e tratamento silencioso de falhas. Este documento substitui o relatório anterior e explicita o que foi confirmado, não implementado ou não pôde ser confirmado.
