# Auditoria Técnica de Reconhecimento

**Projeto:** gerenciamento de empréstimos de biblioteca escolar  
**Data:** 2026-10-22  
**Escopo:** leitura do código, configurações declarativas, SQL local, testes e documentação existentes.

## Escopo e certeza

Este documento descreve o repositório local observado. Não houve conexão com o Supabase publicado, consulta a dados, execução de SQL, migração, instalação de dependências ou execução de testes. Os arquivos de dados em `backend/data/` e valores de ambiente/segredos não foram inspecionados nem reproduzidos. O arquivo `database.sql` foi lido como texto, sem execução.

Somente este novo relatório foi criado. Nenhum arquivo de aplicação, configuração ou banco foi alterado.

## 1. Resumo do sistema

O projeto é uma aplicação web monolítica: Flask serve a SPA e a API no mesmo processo. O frontend é HTML/CSS e JavaScript sem framework; os módulos usam uma camada `API` em `frontend/assets/js/api.js`, um estado em memória/localStorage em `store.js` e um controlador central em `app.js`. O backend organiza domínios em Flask Blueprints e usa Supabase/PostgreSQL por `backend/utils/supabase_client.py`.

Os domínios implementados incluem livros e exemplares, alunos, salas, gêneros, empréstimos, renovações, devoluções, relatórios, autenticação, autoatendimento e QR Code. Há referências a JSON local como fallback em vários módulos. Porém, `backend/app.py` consulta a tabela `livros` antes de liberar quase todas as APIs de negócio; portanto, não se pode concluir que a aplicação opere efetivamente em modo offline apenas porque os módulos contêm fallback JSON.

## 2. Estrutura de pastas e responsabilidades

| Caminho | Responsabilidade observada |
|---|---|
| `backend/app.py` | Criação do Flask, carregamento de ambiente, CORS, registro dos Blueprints, middleware, health checks e entrega da SPA. |
| `backend/api/` | Autenticação (`auth.py`), livros/ISBN (`books.py`), alunos (`students.py`), empréstimos (`loans.py`), relatórios (`reports.py`), salas (`rooms.py`), gêneros (`genres.py`), permissões de autoatendimento (`controle.py`) e helpers JSON/esquema (`_helpers.py`). |
| `backend/utils/` | Cliente Supabase (`supabase_client.py`) e helpers de identificadores/datas/estado de empréstimo (`helpers.py`). |
| `backend/scanner/routes.py` | Decodificação, resolução, login e geração de QR/cartões. |
| `backend/data/` | JSON local usado por caminhos de fallback. Conteúdo não inspecionado por poder conter dados pessoais. |
| `backend/tests/` | Testes Python de API, autenticação, empréstimos, QR, ISBN, relatórios, reconexão e desempenho. |
| `frontend/index.html`, `frontend/assets/css/` | Estrutura da SPA e estilos. |
| `frontend/assets/js/` | API cliente, controlador, estado, scanner, relatórios, gráficos e utilitários. |
| `frontend/assets/js/pages/` | Telas e operações de livros, alunos, empréstimos, salas e gêneros. |
| `frontend/tests/` | Testes JavaScript de API, navegação, CRUD, ISBN, scanner, relatórios e modais. |
| `database.sql` | Script SQL com DDL, seeds, políticas RLS e views. O próprio arquivo contém comandos `DROP ... CASCADE`; não é uma migração incremental segura. |
| Raiz | Muitos relatórios/estudos com datas e níveis de atualização diferentes, além de `COMO_USAR.md`, `TESTES_EXECUTADOS.md` e dependências. |

Não foram localizados no projeto arquivos próprios de Docker, Compose, Procfile, configuração do Render ou manifesto npm (`package.json`). A configuração declarada de implantação está principalmente no README do backend e em um workflow GitHub Actions.

## 3. Arquitetura e fluxos de dados

1. O navegador carrega `frontend/index.html`, que inclui bibliotecas externas de Chart.js, jsQR e ícones, além dos estilos e scripts do projeto.
2. `frontend/assets/js/api.js` deriva a base da API de `window.location.origin`, inclui JSON por padrão, converte respostas para objeto e lança `Error` com status HTTP quando a resposta não é 2xx. Um retry opcional é usado para erros 502/503/504 no decode QR.
3. `app.js` executa login, navegação, sincronização dos livros/alunos/empréstimos, atualizações de interface e fluxos de autoatendimento. `Store` mantém estado em memória e uma cópia em localStorage.
4. Flask registra os Blueprints e, para quase toda requisição `/api/`, `require_database_for_api()` faz uma consulta de prova em `livros`. Exceções incluem health/readiness, configuração Supabase e as rotas de ISBN. Se a consulta falha, a API responde 503 antes de alcançar muitos fallbacks JSON.
5. Os handlers chamam `get_client()`/`sb_exec()` e constroem consultas Supabase. Alguns capturam exceções e leem/escrevem arquivos em `backend/data/`; a consistência e reconciliação entre esses arquivos e Supabase não são centralizadas.
6. Respostas JSON voltam pela camada `API`; `app.js`/páginas atualizam `Store`, redesenham a tela e exibem erros via mensagem/toast. `apiFetch` registra erros no console e propaga a exceção ao chamador.

O frontend também chama `loadSupabaseConfig()` durante a inicialização. A função recebe URL e chave de endpoint público do backend, mas não foi encontrada uma chamada a `getSupabaseFrontend()` nem uso direto do cliente Supabase nos demais módulos pesquisados. Assim, o caminho de dados operacional observado é a API Flask, embora a configuração seja enviada ao navegador.

## 4. Inventário de rotas

**Autorização global:** não há decorador geral de autenticação nas rotas de negócio. O middleware aplica limitações quando a sessão Flask já tem `access_scope=staff_librarian` ou `self_service`; sem esse escopo, as rotas normalmente prosseguem. A exceção mais explícita é `PUT /api/controle/autoatendimento`, que exige escopo `staff_admin`. O middleware de banco pode responder 503 antes do handler. Isso significa que “autenticação exigida” abaixo descreve o handler/middleware atual, não a intenção da interface.

| Método e rota | Arquivo / handler | Autenticação exigida | Entrada, saída e chamadas observáveis |
|---|---|---|---|
| `GET /api/health`, `GET /api/ready` | `backend/app.py`: `health`, `readiness` | Não. Isentas do gate de banco; readiness consulta Supabase. | Sem entrada. JSON de liveness; readiness retorna conectado ou 503. |
| `GET /api/auth/config/supabase`, `GET /api/auth/supabase-config` | `backend/api/auth.py`: `get_supabase_config`, compatibilidade | Não | Sem entrada. JSON `{url,key}` ou campos vazios. A chave pode ser a chave de serviço dependendo do ambiente; ver riscos. |
| `GET /api/config/supabase`, `GET /api/supabase-config` | `backend/app.py`: `legacy_supabase_config` | Não | Alias para `get_supabase_config()`. |
| `POST /api/auth/login` | `backend/api/auth.py`: `login` | Credenciais no corpo; sem sessão prévia | `{login,password}`. Usa `_get_user_by_login`, `_verify_password`; limpa e define a sessão Flask. 200 com papel/id/login/nome; 400, 401, 503 ou 500. |
| `POST /api/auth/self-service/login`, `POST /api/auth/self-service/logout` | `backend/api/auth.py`: `self_service_login`, `self_service_logout` | Login por carteirinha; logout não exige autenticação explícita | Login recebe `{code}`, consulta `_get_student_by_card`, emite token assinado e define escopo na sessão; logout limpa a sessão. |
| `GET /api/auth/self-service/history`, `GET /api/auth/self-service/books` | `backend/api/auth.py`: `self_service_history`, `self_service_books` | Bearer token mais sessão de autoatendimento; disponibilidade/configuração habilitada | Histórico retorna aluno e empréstimos desse aluno; books retorna livros com cópias disponíveis. Consultam Supabase; history tem fallback JSON. |
| `POST /api/auth/self-service/loans`, `POST /api/auth/self-service/loans/<loan_id>/renew`, `POST /api/auth/self-service/loans/<loan_id>/return` | `backend/api/auth.py`: `self_service_create_loan`, `self_service_renew_loan`, `self_service_return_loan` | Bearer token, sessão e propriedade do empréstimo quando aplicável | Criação recebe `exemplar_qr`; renovação/devolução verificam vínculo aluno-empréstimo e encaminham a `_create_loan_record`, `renew_loan` ou `return_loan`. |
| `GET /api/books/`, `GET /api/books/<book_id>` | `backend/api/books.py`: `list_books`, `get_book` | Sem autenticação geral | Busca aceita `q`/`genre`; detalhe busca por id, ISBN ou identificador de exemplar. Retorna livros JSON e gênero enriquecido. |
| `GET /api/books/isbn-lookup`, `POST /api/books/isbn-vision` | `backend/api/books.py`: `lookup_isbn`, `lookup_isbn_from_image` | Sem autenticação geral; isentas do gate de banco | Lookup recebe `isbn` e `source`; visão recebe `{image,provider}`. Respostas de metadados ou `{error}` com 400, 404 ou 502. |
| `POST /api/books/`, `PUT /api/books/<book_id>`, `DELETE /api/books/<book_id>`, `DELETE /api/books/<book_id>/exemplars/<exemplar_code>` | `backend/api/books.py`: `create_book`, `update_book`, `delete_book`, `delete_exemplar` | Sem autenticação geral | Criação exige título/autor e gera metadados de exemplares; update recebe campos do livro; exclusões verificam empréstimos ativos/históricos. Saída é registro, `{success:true}` ou erro 400/404/409. |
| `GET /api/students/`, `GET /api/students/<student_id>` | `backend/api/students.py`: `list_students`, `get_student` | Sem autenticação geral | Lista filtra por `q`, `class`, `sala_id`; detalhe aceita carteirinha/id. Inclui dados de sala. |
| `POST /api/students/`, `PUT /api/students/<student_id>`, `DELETE /api/students/<student_id>`, `PATCH|POST /api/students/<student_id>/access`, `POST /api/students/import/csv` | `backend/api/students.py`: `create_student`, `update_student`, `delete_student`, `toggle_librarian_access`, `import_csv` | Sem autenticação geral | JSON para CRUD/acesso; CSV por arquivo ou corpo texto. Excluir verifica empréstimos ativos; exclusão pode ser lógica. Import responde contagem adicionada/ignorada. |
| `GET /api/loans/`, `GET /api/loans/<loan_id>` | `backend/api/loans.py`: `list_loans`, `get_loan` | Sem autenticação geral | Lista aceita `status` (`active`, `overdue`, `returned`) e ordena por data; detalhe por id. |
| `POST /api/loans/`, `POST /api/loans/<loan_id>/renew`, `POST /api/loans/<loan_id>/return` | `backend/api/loans.py`: `create_loan`, `renew_loan`, `return_loan` | Sem autenticação geral; sessão de bibliotecário pode ser limitada pelas opções do controle | Criação recebe `livro_id`, `aluno_id`, `dias`, datas/opcionais e exemplar; renovação usa prazo padrão do controle; devolução exige `exemplar_qr` e aceita referência opcional do aluno. Respostas de registro ou erro 400/403/404/409. |
| `GET /api/rooms/`, `GET /api/rooms/<room_id>`, `POST /api/rooms/`, `PUT /api/rooms/<room_id>`, `DELETE /api/rooms/<room_id>` | `backend/api/rooms.py`: handlers CRUD de salas | Sem autenticação geral | JSON; cria exige `nome`; listagem/detalhe inclui contagem/associação de alunos. Exclusão remove a associação de sala dos alunos antes de excluir. |
| `GET /api/genres/`, `POST /api/genres/`, `PUT /api/genres/<genre_id>`, `DELETE /api/genres/<genre_id>` | `backend/api/genres.py`: handlers CRUD de gêneros | Sem autenticação geral | JSON; criação exige `nome`; lista agrega quantidade de livros; exclusão limpa `genero_id` associado aos livros. |
| `GET|PUT /api/controle/autoatendimento` | `backend/api/controle.py`: `autoatendimento_settings` | GET não exige; PUT verifica `session.access_scope == staff_admin` | GET retorna configurações armazenadas em JSON; PUT exige quatro permissões booleanas e `renewal_days` entre 1 e 365. |
| `GET /api/reports/chart-summary`, `/top-books`, `/by-class`, `/monthly`, `/data` | `backend/api/reports.py`: `chart_summary`, `top_books`, `by_class`, `get_monthly`, `report_data` | Sem autenticação geral | JSON derivado de livros/alunos/empréstimos/relatórios; `top-books` aceita `limit`. |
| `POST /api/reports/monthly/generate` | `backend/api/reports.py`: `generate_monthly` | Sem autenticação geral | Recebe `mes_ano` opcional; agrega dados e faz upsert de relatório mensal; retorna registro (201). |
| `GET /api/reports/export/overdue`, `/all`, `/books`, `/by-class`, `/student-status`, `/students` | `backend/api/reports.py`: seis handlers `export_*` | Sem autenticação geral | Sem entrada; devolve CSV por `_build_report_data()`/`_csv_resp()`. Os relatórios incluem campos de aluno e empréstimos. |
| `POST /api/qr/start`, `POST /api/qr/stop`, `GET /api/qr/result`, `GET /api/qr/status` | `backend/scanner/routes.py`: handlers de câmera de servidor | Sem autenticação geral | Start aceita índice de câmera opcional; retorna estado. Result/status expõem resultado/estado globais do scanner do processo. |
| `POST /api/qr/decode` | `backend/scanner/routes.py`: `decode_image` | Sem autenticação geral; sessão self-service reduz os campos/type retornados | Aceita upload `file` ou imagem base64; tenta pyzbar/OpenCV e resolve código por `_resolve_qr`. Retorna códigos, primário, tipo e registro resolvido; 400 em exceções. |
| `POST /api/qr/login` | `backend/scanner/routes.py`: `qr_login` | Código; cartão admin exige senha; cartão aluno precisa estar marcado como bibliotecário | Recebe `{code,password?}`. Define escopo de sessão para admin/bibliotecário ou responde acesso negado. |
| `POST /api/qr/card/admin/<login>`, `POST /api/qr/generate`, `GET /api/qr/card/book/<book_id>`, `GET /api/qr/card/student/<student_id>` | `backend/scanner/routes.py`: `admin_card`, `generate_qr`, `book_card`, `student_card` | Cartão admin exige senha; as demais rotas não exigem sessão explícita | Gera imagem PNG em base64/cartões. `generate` recebe `data` e cor opcional; cartão de livro pode retornar vários exemplares. |
| `GET /`, `GET /<path>`, `GET /favicon.ico` | `backend/app.py`: `serve_frontend`, `favicon` | Não | Serve arquivo estático ou `index.html` para navegação SPA; caminhos desconhecidos sob `/api/` respondem 404. Favicon ausente responde 204. |

### Divergências entre cliente e servidor

- A maioria das chamadas mapeadas em `api.js` corresponde aos Blueprints registrados em `app.py`.
- O servidor expõe `GET /api/qr/status`, mas não há wrapper `API.qr.status` no cliente localizado.
- O servidor permite `GET /api/auth/self-service/books`; não há wrapper correspondente em `api.js` e o fluxo atual observado de autoatendimento empresta via QR individual, sem usar essa listagem.
- As exportações de relatório são construídas por URL dinâmica no frontend; os seis identificadores implementados têm handler no backend.
- Não foi identificada divergência de prefixo nos wrappers usados pelas telas. A presença de rotas extras não prova que sejam usadas.

## 5. Modelo de dados comprovado

O modelo abaixo é o que `database.sql` declara, não uma introspecção do banco remoto.

| Tabela | Campos/constraints observados |
|---|---|
| `usuarios` | `id` UUID PK, `nome`, `login` único obrigatório, `senha` obrigatória, `criado_em`. |
| `salas` | `id` UUID PK, `nome`, `codigo`, `descricao`, `capacidade`, `criado_em`; índice em código. |
| `generos` | `id` UUID PK, `nome`, `icone`, `cor`, `criado_em`. |
| `livros` | `id` UUID PK, `isbn`, `titulo` obrigatório, `autor`, `area`, `genero_id` FK para gênero com `ON DELETE SET NULL`, `exemplares >= 1`, `qr_id` único, arrays/metadata JSONB dos exemplares e `criado_em`. Índices em ISBN, título, área, gênero e QR. |
| `alunos` | `id` UUID PK, `nome`, `turma`, `carteirinha`, `sala_id` FK para sala com `ON DELETE SET NULL`, `qr_id` único, `is_librarian`, `deleted_at`, `criado_em`. Índices parciais únicos para carteirinha não vazia e QR não nulo; índices para nome/turma/sala. |
| `emprestimos` | `id` UUID PK, `livro_id` e `aluno_id` FKs com `ON DELETE CASCADE`, `exemplar`, `exemplar_id`, datas de empréstimo/prazo/devolução, observação, criador, `renovacoes >= 0`, `criado_em`. Índice único parcial por `(livro_id, exemplar)` onde ainda não devolvido impede dois empréstimos ativos do mesmo exemplar. |
| `relatorios_mensais` | `id` UUID PK, `mes_ano` único, totais, dados JSONB de livros/turmas, `gerado_em` e `gerado_por`. |

O SQL habilita RLS nas sete tabelas. As políticas de salas, gêneros, livros, alunos, empréstimos e relatórios usam `FOR ALL` com `USING(true)` e `WITH CHECK(true)`; para `usuarios`, há política `SELECT USING(true)`. Se aplicado como escrito, isso não representa isolamento por usuário. A permissão efetiva no Supabase remoto não foi examinada.

O script contém `DROP VIEW/TABLE ... CASCADE` antes de recriar objetos. Não executar como procedimento de atualização sem revisão, backup e confirmação explícita. O código também consulta colunas opcionais como `deleted_at`, tolerando schemas divergentes; por exemplo, no SQL local há `deleted_at` em alunos, mas não em livros. Isso indica tolerância a variantes, não comprova o schema publicado.

Views locais declaradas: `vw_emprestimos_ativos` e `vw_livros_ranking`. Não encontrei uso delas nos handlers lidos; as consultas de relatório calculam agregações no Python.

## 6. Fluxo de autenticação

### Equipe

1. O frontend envia usuário/senha por `POST /api/auth/login`.
2. `auth.login()` busca usuário na tabela `usuarios` por `_get_user_by_login()` e verifica senha em `_verify_password()`. O código aceita hashes suportados e também igualdade com valor legado sem `$`; se autenticar valor sem hash e a biblioteca estiver disponível, tenta gravar um hash.
3. O backend limpa a sessão Flask e define `access_scope` (`staff_admin` ou `staff_librarian`). O frontend, separadamente, define um cookie `biblioteca-session` contendo papel/login/nome em JSON legível por JavaScript, com expiração de inatividade controlada pelo próprio frontend.
4. A sessão Flask assinada é enviada pelo navegador como cookie; as APIs não verificam de forma geral que o escopo seja admin. O cookie `biblioteca-session` é apenas estado de interface, não uma credencial confiável para o backend.

### QR de funcionário/aluno bibliotecário

`POST /api/qr/login` resolve o QR. Cartão administrativo exige senha digitada; aluno com `is_librarian` verdadeiro recebe escopo `staff_librarian`; aluno comum é recusado. O frontend também oculta páginas/ações de admin para bibliotecário. A regra visual não substitui autorização de rota.

### Autoatendimento

O login consulta código de carteirinha e emite token com `URLSafeTimedSerializer`, válido por 30 minutos (`SELF_SERVICE_TOKEN_MAX_AGE`). Operações exigem Bearer token, sessão Flask com escopo `self_service` e identidade de aluno coerente. Histórico é filtrado pelo aluno; renovação/devolução verificam a propriedade do empréstimo. A chave padrão de desenvolvimento impede emitir token seguro e causa 503. As permissões também dependem de JSON local `self_service_settings.json`.

### Limites observados

- Não foi localizado middleware/decorador geral que exija sessão de equipe para CRUD, consultas, relatórios, importação ou emissão de vários tipos de QR.
- O middleware restringe alguns caminhos apenas quando encontra sessão de bibliotecário/autoatendimento; requisições sem sessão não recebem essa restrição por esse código.
- Não há configuração explícita no app para rate limit, proteção CSRF de mutações ou parâmetros próprios `SESSION_COOKIE_SECURE`/`SESSION_COOKIE_SAMESITE`.

## 7. Fluxo completo do ISBN

### Busca de metadados

1. `pages/books.js` normaliza o texto e chama `API.books.lookupIsbn()`, cujo `source` padrão é `manual`. O caminho atualmente encontrado para leitura de ISBN também chama explicitamente `lookupBookIsbn("manual")`.
2. `GET /api/books/isbn-lookup` usa `_normalize_isbn()` e `_validate_isbn()`, com checksum para ISBN-10 e ISBN-13.
3. `_lookup_isbn()` consulta primeiro cache em memória por ISBN, TTL 15 minutos e tamanho máximo de 128 entradas.
4. No modo `manual`, Google Books API, ISBNsearch (HTML) e Open Library API são executados em paralelo. O Groq só é incluído quando o parâmetro recebido é exatamente `source=scanner`; o frontend observado não envia esse valor no fluxo atual de formulário/câmera.
5. Cada chamada HTTP via `_open_provider()` tem timeout de 6 segundos e até duas tentativas, com pausa de 0,2 s para erros de rede e certos códigos HTTP. Groq via SDK OpenAI tem timeout de 6 segundos e `max_retries=0`.
6. Se as fontes primárias não fornecerem pelo menos algum resultado completo com título e autor, o código tenta Google Books HTML e Open Library Search em paralelo; ISBNdb entra nesse grupo somente quando `ISBNDB_API_KEY` está configurada.
7. `_select_metadata_field()` aceita consenso se duas fontes normalizadas concordarem; sem consenso, escolhe o primeiro valor não vazio na ordem de resultados. Categorias são unidas sem duplicatas. Se fontes não fornecerem um campo, os campos do Groq podem preencher a lacuna. O sistema mapeia categorias para gênero cadastrado e devolve `area="Geral"`.
8. Cache só guarda resultado que tenha título, autor e ao menos uma categoria. Em erro, a página mostra mensagem e permite preenchimento manual.

### Visão e códigos de barras

`POST /api/books/isbn-vision` seleciona Groq ou OpenAI Vision por `provider`/`ISBN_VISION_PROVIDER`, decodifica o número da imagem e valida o ISBN. Depois chama `_lookup_isbn(..., use_groq=False)`, portanto Groq pode ser usado como leitor visual e não como sugestão de metadados nesse caminho. OpenAI é usado em visão, não apareceu como fonte de metadados bibliográficos. O leitor local `pyzbar`/OpenCV e as alternativas de navegador `jsQR`/`BarcodeDetector` também aparecem no scanner.

### Comparação com a regra desejada

| Regra desejada | Comportamento comprovado |
|---|---|
| Groq sugere metadados | A função existe, mas a consulta de metadados do Groq só é adicionada para `source=scanner`. O frontend localizado usa `manual` no fluxo de formulário/câmera. |
| Outras fontes confirmam | Google Books, ISBNsearch e Open Library consultam em paralelo; fallback usa Google Books HTML, Open Library Search e ISBNdb opcional. |
| Se nenhuma fonte utilizável, preservar sugestão Groq | Se Groq foi chamado e retornou dados, seus campos são usados como fallback mesmo sem confirmação. Também podem preencher campos ausentes de resultados parciais. |
| Divergências entre fontes | Não há decisão por confiança/validação manual de divergência: usa consenso simples por campo ou primeiro resultado não vazio; categorias são combinadas. Google Books pode devolver identificador ISBN diferente sem comparação explícita com o pedido no código lido. |

Assim, a regra não está comprovadamente implantada no fluxo padrão do frontend: há implementação parcial no backend, mas o acionamento de sugestão Groq é condicionado a um `source` que não foi encontrado sendo usado na chamada observada. ISBNdb está presente no fallback, apesar de não ser uma das fontes nomeadas na regra. Resultados e disponibilidade externos não foram testados nesta auditoria.

## 8. Fluxo de empréstimos e QR Code

### Empréstimo

1. Na tela de empréstimos, o usuário procura livro por identificador, título ou ISBN e identifica aluno. O frontend consulta `/api/books/`/`<id>` e `/api/students/`, mantendo seleções em `pendingLoan`.
2. Confirmação envia livro, aluno, dias e, quando selecionado, exemplar a `POST /api/loans/`.
3. `_create_loan_record()` valida existência de livro/aluno, calcula cópias livres por empréstimos ativos, atribui exemplar, data e prazo via `today_str()`/`add_days()`, grava registro com `devolvido_em=null` e responde 201. Datas vêm de funções auxiliares e entrada `data_emprestimo` é aceita; não há validação explícita visível de formato ou limite de prazo na rota.
4. A disponibilidade é calculada a partir de empréstimos sem `devolvido_em`, confrontando código e id do exemplar. O índice único parcial do SQL oferece uma proteção adicional para código de exemplar em banco que use esse schema.

### Renovação e devolução

- `POST /api/loans/<id>/renew` recusa inexistente ou já devolvido, usa `renewal_days` do controle, soma ao prazo atual e incrementa `renovacoes`. Se schema não tiver a coluna, remove esse campo e tenta atualizar novamente.
- `POST /api/loans/<id>/return` exige `exemplar_qr`, compara livro/código/id do exemplar com `_matches_loan_exemplar_qr()` e, se enviada referência de aluno, verifica identidade do titular. Atualiza `devolvido_em` para data informada ou hoje.
- O frontend apresenta estados `active`, `overdue` e `returned` a partir da devolução e data prevista; o histórico de autoatendimento exibe “Em andamento”, “Atrasado” ou “Devolvido”. A definição detalhada de status está em `backend/utils/helpers.py` e `Store.loanStatus()`.
- Quando o backend trata Supabase indisponível, alguns handlers escrevem JSON local. O gate global de `app.py` normalmente bloqueia a requisição antes que esses handlers usem o fallback; comportamento offline não é uniforme.

### QR Code / identificadores internos

Livros recebem `id` interno e cada exemplar tem metadata com `id`, código numérico e `qr_data` como `EXEMPLAR-...`. QR do exemplar é resolvido por `_resolve_qr()` e validado contra metadados existentes em `_is_known_exemplar_qr()`. QR de livro inteiro também pode conter id/ISBN, mas autoatendimento restringe operação a QR individual de exemplar. QR de aluno usa id/carteirinha; prefixo administrativo é resolvido por rota QR.

`QRScanner` tenta câmera local com `jsQR`/`BarcodeDetector`; para ISBN, páginas também usam chamada de visão em frames ou API de decode conforme opção. Backend decode usa Pillow, `pyzbar`/OpenCV e `QRCodeDetector` como alternativas. Rotas `/qr/start`/`stop` usam estado global de processo e câmera conectada ao servidor, não câmera do navegador.

### Exclusão e recuperação

- Livro: exclusão é recusada se houver empréstimo ativo. Se existir coluna `deleted_at`, tenta soft delete; se há histórico e não existe coluna, responde 409 para preservar histórico. Sem empréstimos, remove registro.
- Exemplar: não remove último exemplar nem exemplar com empréstimo ativo; atualiza metadata e ids. Histórico antigo permanece.
- Aluno: recusa exclusão com empréstimo ativo; se tiver `deleted_at`, marca exclusão lógica, senão apaga do banco. A listagem filtra registros excluídos quando reconhece a coluna.
- Empréstimo: não foi encontrada rota de exclusão nem recuperação de empréstimo devolvido. Rotas de atualização disponíveis são renovação e devolução.
- Não foi localizada rota explícita de restauração (`undelete`). O `PUT` do aluno recebe campos genéricos depois de remover apenas alguns campos; o código não documenta nem valida uma operação de recuperação, portanto recuperação por payload não deve ser assumida como funcional ou autorizada.

## 9. Configuração, inicialização e implantação

- Ambiente: `backend/app.py` carrega `backend/.env` via `python-dotenv` sem sobrescrever variáveis já definidas. `utils.supabase_client` lê `SUPABASE_URL` e `SUPABASE_SERVICE_KEY` ou `SUPABASE_KEY`; a precedência no endpoint de configuração frontend é diferente.
- Inicialização local documentada: `python backend/app.py`. Porta `PORT`, depois `FLASK_PORT`, depois 5000; host `0.0.0.0`. Debug depende de `FLASK_ENV` e assume `development` quando ausente.
- Dependências declaradas: raiz `requirements.txt` apenas inclui dependências do backend; `backend/requirements.txt` lista Flask/CORS, dotenv, QR/Pillow, OpenCV, pyzbar, NumPy, Supabase, Groq, OpenAI, Gunicorn, passlib e bcrypt. Não há pacote frontend próprio declarado; a SPA busca algumas bibliotecas por CDN.
- Render documentado em `backend/README.md`: build `pip install -r requirements.txt`, start `gunicorn --chdir backend app:app`, health check `/api/health`, e variáveis Supabase/secretos no ambiente do serviço. Isso é instrução documental, não confirmação de deploy ativo ou configuração real.
- `.github/workflows/Manter render ativo.yml` executa um ping agendado a cada dez minutos e permite execução manual. Isso confirma apenas uma automação declarada no repositório.
- `/api/health` é liveness sem banco; `/api/ready` testa consulta real e retorna 503 quando banco indisponível. `frontend/app.js` fica em repetição de 3 segundos aguardando readiness antes de liberar a interface.
- O código habilita CORS com origem `*`. A CSP permite scripts e estilos inline, necessários segundo comentário para handlers legados.

## 10. Testes disponíveis e resultados

**Nenhum teste foi executado nesta auditoria.** Portanto, não há resultado atual de aprovação/reprovação.

Há 15 módulos Python em `backend/tests/` e 7 testes JavaScript em `frontend/tests/`. Os assuntos cobertos incluem login/perfil bibliotecário, autoatendimento, fallback de livros, ISBN, QR, exemplares, loans/devolução, reports, contagens, health, variáveis de ambiente, reconexão Supabase, navegação, CRUD, retry da API, scanner, modais e relatórios.

Não há `package.json`, `pytest.ini`, `pyproject.toml`, `tox.ini` ou script de tarefas do projeto localizados (fora de diretórios gerados/dependências). Com as ferramentas correspondentes já disponíveis, comandos convencionais possíveis a partir da raiz são:

```bash
PYTHONPATH=backend python -m pytest -q backend/tests
node --test frontend/tests/*.test.js
```

São comandos inferidos pela organização/imports dos testes, não scripts definidos pelo projeto nem executados agora. `pytest` não aparece na lista de `backend/requirements.txt`; o ambiente precisa ter a ferramenta separadamente. `TESTES_EXECUTADOS.md` e `auditoria-documentacao.md` registram execuções anteriores, com datas e resultados que não foram reproduzidos nesta etapa; não devem ser tratados como estado atual.

## 11. Problemas comprovados

1. **Autorização insuficiente nas APIs:** CRUD, listagens, empréstimos, importação e relatórios não exigem globalmente sessão de equipe nos handlers/middleware. A interface esconde controles, mas chamadas diretas continuam sem essa checagem quando não há sessão de escopo restrito.
2. **Possível exposição de chave privilegiada:** `get_supabase_config()` escolhe `SUPABASE_KEY` antes de `SUPABASE_SERVICE_KEY`, enquanto o cliente backend dá precedência à chave de serviço. Se o serviço estiver configurado apenas com `SUPABASE_SERVICE_KEY`, a rota pública retorna essa chave ao browser. O impacto depende do ambiente implantado, não examinado.
3. **Políticas RLS amplas no SQL local:** várias tabelas têm política `FOR ALL` com condições verdadeiras; tabela de usuários tem política de leitura ampla. Se o script for aplicado, as regras não restringem por identidade. Estado remoto desconhecido.
4. **Credencial de assinatura de desenvolvimento:** `app.py` tem fallback hardcoded para `secret_key`; ausência de `SECRET_KEY` segura compromete a segurança de sessões assinadas. O valor não é reproduzido aqui.
5. **Cartão administrativo inclui a senha enviada na imagem:** `admin_card()` coloca o campo de senha no cartão PNG, aumentando risco de exposição física/digital da credencial.
6. **Dados de aluno podem ser retornados pelo decode QR:** para sessão não restrita, `_resolve_qr()` retorna o registro do aluno; a rota não exige autenticação explícita. Relatórios CSV também não exigem autenticação e incluem dados identificáveis/carteirinha.
7. **Risco de acesso amplo por CORS e rotas públicas:** CORS `*` amplia origens capazes de chamar endpoints; combinado com autorização ausente, as rotas públicas de leitura/escrita devem ser tratadas como exposição, não como proteção por UI.
8. **Script SQL destrutivo:** `database.sql` remove views/tabelas com `CASCADE` antes de criá-las; não é adequado como migração incremental sem processo específico.
9. **Fallbacks e bloqueio de banco contraditórios:** handlers implementam arquivos JSON, mas `require_database_for_api()` bloqueia a maioria das APIs sem confirmar acesso à tabela `livros`; frontend espera readiness do Supabase. “Modo offline” documentado não é comprovado como modo funcional end-to-end.
10. **Documentação inconsistente/histórica:** arquivos de uso/teste relatam credenciais/resultados e capacidades antigas que não correspondem ao código atual. O conteúdo sensível desses documentos foi omitido deste relatório.
11. **Sem limitação de tentativas de login encontrada:** não foi localizado rate limit para senha nem para geração de cartões/login QR.
12. **Cliente local pode ser adulterado:** cookie de interface `biblioteca-session` é JSON sem assinatura e legível por JavaScript. Ele não deve ser considerado autorização; o backend também não o verifica.

## 12. Hipóteses que ainda precisam de confirmação

- Se o Render está ativo, qual commit/branch está implantado e quais variáveis existem. O workflow só mostra uma URL de ping declarada.
- Se `SUPABASE_SERVICE_KEY` está atualmente configurada, se também há `SUPABASE_KEY` e qual valor o endpoint efetivamente entrega.
- Se SQL local foi aplicado ao projeto remoto, quando, com quais adaptações, policies e versões de coluna.
- Se a configuração de CORS/cookies e as políticas de infraestrutura colocam controles adicionais não versionados.
- Se chamadas de navegador fora da SPA acessam diretamente o banco; a configuração é carregada, mas não foi encontrado uso do cliente Supabase frontend.
- Se provedores ISBN respondem conforme o código, se há limites/cotas, e se resultados divergentes ocorrem em casos reais.
- Se registros excluídos podem ser restaurados por uso manual de `PUT`; não há fluxo explícito de recuperação documentado.
- Se os caminhos JSON têm backup, persistência de volume, permissões adequadas ou reconciliação com Supabase no deploy.

## 13. Informações faltantes para compreender completamente o projeto

- Schema e policies atuais do Supabase com export seguro e sem linhas/dados, além da confirmação da chave de papel usada pelo servidor (sem revelar o valor).
- Ambiente real de produção, versão implantada, comando efetivo, configuração de domínio/TLS, cookies e logs de acesso.
- Processo de backup/restauração e política de retenção de empréstimos, alunos e auditoria.
- Contrato formal de papéis/permissões para admin, bibliotecário e autoatendimento, incluindo endpoints por papel.
- Regras institucionais de prazo, quantidade máxima, renovações, multas e validação de datas, se existirem fora do código.
- Procedimento seguro de migração incremental; atualmente só foi localizado script SQL recriador.
- Configuração de CI executando backend/frontend tests e respectivos resultados atuais.
- Decisão de produto sobre o fluxo ISBN desejado e quando `source=scanner` deve ser enviado.
- Inventário formal de dados pessoais, retenção, acesso e requisitos legais aplicáveis. Os JSONs não foram examinados.

## 14. Plano de documentação recomendado

1. Manter um documento de arquitetura curto que referencie os entrypoints, Blueprints, responsabilidade dos módulos e versões suportadas.
2. Gerar/documentar contrato OpenAPI a partir das rotas reais, incluindo autenticação, status, esquemas de entrada/saída e erros.
3. Criar matriz de autorização por papel e associá-la a testes de endpoint negativos/positivos antes de descrever qualquer rota como protegida.
4. Documentar esquema remoto por migrações incrementais versionadas; separar schema de seeds e proibir scripts de reset em deploy normal.
5. Registrar o fluxo ISBN com precedência das fontes, heurística de consenso, timeout/cache, fallback e exemplos sintéticos sem credenciais.
6. Documentar execução local/deploy com variáveis apenas por nome, health versus readiness, dependências nativas do scanner, backup e rollback.
7. Definir comandos oficiais de testes e executá-los no CI; distinguir resultado histórico de resultado do commit atual.
8. Consolidar relatórios sobrepostos em uma fonte técnica atual e marcar documentos antigos como histórico, sem replicar dados pessoais ou credenciais.

## Tabela final de evidências

| Assunto | Evidência encontrada | Arquivo de referência | Grau de certeza | Próximo passo |
|---|---|---|---|---|
| Inicialização Flask e blueprints | App cria Flask, registra nove blueprints e entrega frontend | [backend/app.py](backend/app.py) | Alto: código local | Confirmar comando/processo efetivo no deploy |
| Comunicação frontend/API | `API_BASE`, `apiFetch`, agrupamento de wrappers por domínio | [frontend/assets/js/api.js](frontend/assets/js/api.js) | Alto | Adotar contrato OpenAPI e teste de contrato |
| Autenticação por sessão | `login()` define `access_scope`; token de autoatendimento tem expiração | [backend/api/auth.py](backend/api/auth.py) | Alto para implementação local | Criar matriz e testes de autorização de todas as rotas |
| Gate de banco | Prova consulta tabela `livros` em quase todas as APIs | [backend/app.py](backend/app.py) | Alto | Definir comportamento offline esperado e remover ambiguidade documental |
| Cliente Supabase | Chave de serviço tem precedência no cliente backend | [backend/utils/supabase_client.py](backend/utils/supabase_client.py) | Alto | Verificar nomes de variáveis no deploy sem expor valores |
| Exposição de configuração | Endpoint devolve URL/chave e tem precedência diferente do cliente backend | [backend/api/auth.py](backend/api/auth.py) | Alto no código; impacto depende de ambiente | Corrigir/validar com revisão de segurança antes de divulgar qualquer segredo |
| Livros e exemplares | CRUD, códigos internos, geração/remoção e bloqueios por empréstimo ativo | [backend/api/books.py](backend/api/books.py) | Alto | Adicionar testes de contrato e autorização |
| Alunos e exclusão | CRUD, CSV, acesso bibliotecário e soft delete condicional | [backend/api/students.py](backend/api/students.py) | Alto | Documentar restauração/retention ou afirmar que não existe |
| Empréstimos | Disponibilidade, datas, renovação, QR obrigatório na devolução | [backend/api/loans.py](backend/api/loans.py) | Alto | Definir/testar limites de data, renovação e concorrência |
| Resolução de QR | Livro/exemplar/aluno/admin resolvidos por `_resolve_qr()` | [backend/scanner/routes.py](backend/scanner/routes.py) | Alto | Testar em integração e revisar dados pessoais retornados |
| ISBN | Validadores, provedores, fallback, cache e consenso por campo | [backend/api/books.py](backend/api/books.py) | Alto para código; baixo para disponibilidade externa | Decidir acionamento de Groq e teste controlado por provedor |
| Banco local | Tabelas, constraints, RLS e views declaradas no SQL | [database.sql](database.sql) | Alto para arquivo; desconhecido para produção | Fazer introspecção segura/read-only e versionar migrações incrementais |
| Testes | 15 módulos backend e 7 frontend existentes; nenhum executado nesta auditoria | [backend/tests](backend/tests), [frontend/tests](frontend/tests) | Alto para presença; sem resultado atual | Formalizar comandos/CI e executar em ambiente isolado |
| Execução e deploy documentados | Flask local, Gunicorn/Render e health check descritos | [backend/README.md](backend/README.md) | Alto para documentação; deploy real desconhecido | Comparar com configuração atual do provedor |
| Registros históricos de testes | Documentos antigos contêm resultados e afirmações de outras datas | [TESTES_EXECUTADOS.md](TESTES_EXECUTADOS.md), [auditoria-documentacao.md](auditoria-documentacao.md) | Alto para existência; não validado como atual | Reexecutar e datar resultados por commit |