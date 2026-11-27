# Relatório técnico do estado atual do sistema

**Projeto:** Gerenciamento de empréstimo de livros de biblioteca

**Data da análise:** 2026-09-14

**Fonte de verdade:** código atual, `database.sql`, dependências, testes executados e histórico Git. Relatórios, comentários e README foram usados somente como contexto histórico. Quando há conflito, o código atual prevalece.

## 1. Regra de interpretação

Este documento descreve o que foi encontrado no estado atual do repositório. Não foram inferidas funcionalidades a partir de telas, nomes de arquivos ou planos antigos.

Quando uma informação não pôde ser comprovada, foi usada a frase:

> Não foi possível confirmar esta informação no estado atual do projeto.

Não foram incluídas credenciais, senhas, chaves ou tokens.

## 2. Visão geral

O projeto é uma aplicação web para organizar o acervo de uma biblioteca e registrar a circulação de livros. O contexto informado pelo responsável é que, antes da digitalização, os empréstimos eram controlados em papel por meio de uma lista grande, dificultando consultar e atualizar manualmente o livro, o aluno, a data do empréstimo, a devolução e a situação atual.

O sistema atual possui:

- frontend HTML, CSS e JavaScript sem framework;
- backend Python com Flask;
- APIs HTTP organizadas em blueprints;
- persistência principal prevista em Supabase, usando PostgreSQL no lado do banco;
- arquivos JSON locais presentes no repositório e usados como fallback interno em vários módulos;
- cadastro de livros, alunos, salas e gêneros;
- empréstimos, devoluções e renovações;
- consulta de livros por ISBN;
- geração e leitura de QR Codes;
- geração de cartões imprimíveis;
- relatórios em gráficos e CSV;
- login por usuário/senha e login por QR Code.

A aplicação Flask serve o frontend e as APIs pelo mesmo processo. O frontend chama o backend por `/api`. O backend consulta o Supabase quando consegue utilizá-lo e vários módulos possuem caminhos alternativos para JSON local. Porém, `backend/app.py` possui um `before_request` que verifica a tabela `livros` e retorna `503` para quase toda API quando não consegue confirmar a conexão com o banco. Portanto, a existência de código de fallback não significa que todo o sistema opere offline pela interface em qualquer situação.

## 3. Estrutura real do projeto

### 3.1 Backend

| Parte | Localização | Função e relação |
|---|---|---|
| Entrada do servidor | `backend/app.py` | Cria a aplicação Flask, carrega ambiente, registra blueprints, aplica CORS e headers, serve o frontend e expõe health check. |
| APIs | `backend/api/` | Contém os módulos de autenticação, livros, alunos, empréstimos, relatórios, salas e gêneros. |
| Helpers das APIs | `backend/api/_helpers.py` | Leitura/escrita JSON, detecção de tabelas, detecção de `deleted_at` e identificação de alguns erros de indisponibilidade. |
| Scanner e cartões | `backend/scanner/routes.py` | Decodificação de imagens, resolução de códigos, login por QR, geração de QR e imagens de cartões. |
| Cliente do banco | `backend/utils/supabase_client.py` | Cria e mantém o cliente Supabase, normaliza a URL e executa consultas. |
| Regras auxiliares | `backend/utils/helpers.py` | UUIDs, data atual, soma de dias, dias restantes e status de empréstimo. |
| Dados locais | `backend/data/*.json` | Arquivos de livros, alunos, empréstimos, gêneros e salas usados como dados locais/fallback em módulos. |
| Testes | `backend/tests/` | Testes Python de autenticação, fallback, ISBN, QR, relatórios, identificadores, ambiente e Supabase. |

### 3.2 Frontend

| Parte | Localização | Função e relação |
|---|---|---|
| Shell da aplicação | `frontend/index.html` | Define login, navegação, páginas, formulários, tabelas, gráficos, modais e ordem dos scripts. |
| Estilos | `frontend/assets/css/main.css` | Estilos da interface. |
| Comunicação HTTP | `frontend/assets/js/api.js` | Centraliza `fetch`, serialização JSON e os caminhos dos endpoints. |
| Controle principal | `frontend/assets/js/app.js` | Login, cookie de sessão do navegador, navegação, sincronização, empréstimos, devoluções e renovações. |
| Estado local | `frontend/assets/js/store.js` | Mantém arrays de livros, alunos, empréstimos, salas e gêneros; também grava cache no `localStorage`. |
| Scanner do navegador | `frontend/assets/js/qr-scanner.js` | Usa câmera, canvas, `jsQR`, `BarcodeDetector` e fallback de decodificação no backend. |
| Gráficos | `frontend/assets/js/charts.js` | Usa Chart.js para renderizar os dados das APIs de relatórios. |
| Páginas | `frontend/assets/js/pages/` | Renderização e operações de livros, alunos, empréstimos, salas e gêneros. |
| Configuração Supabase do frontend | `frontend/assets/js/lib/supabase-config.js` | Tenta obter configuração por endpoints do backend; não foi confirmado uso efetivo de cliente Supabase direto no frontend. |
| Testes JavaScript | `frontend/tests/` | Testes Node dos fluxos de ISBN no formulário e callback do scanner. |

### 3.3 Banco e configuração

- `database.sql` define o esquema PostgreSQL esperado para o Supabase, políticas, índices, views e dados iniciais.
- `backend/requirements.txt` declara as dependências Python.
- `requirements.txt` da raiz apenas referencia `backend/requirements.txt`.
- `backend/.env.example` documenta variáveis de ambiente.
- Não foi encontrado `package.json` no projeto. Não foi possível confirmar um gerenciamento de dependências npm para o frontend.
- O arquivo `backend/.env` não foi encontrado na árvore analisada. Não foi possível confirmar as configurações operacionais reais do ambiente local ou de produção.

## 4. Tecnologias confirmadas

### 4.1 Backend e infraestrutura de aplicação

- **Python:** linguagem dos arquivos em `backend/` e dos testes Python.
- **Flask:** framework HTTP usado em `backend/app.py` e nos blueprints.
- **Flask-CORS:** aplicado em `app.py` para `/api/*`, com origem `*`.
- **python-dotenv:** usado para carregar `backend/.env`.
- **Supabase:** usado pelo cliente Python em `backend/utils/supabase_client.py`.
- **PostgreSQL:** confirmado pelo SQL do Supabase, que usa UUID, JSONB, índices parciais, `FILTER`, `CURRENT_DATE`, views e políticas RLS.
- **Gunicorn:** aparece em `backend/requirements.txt`, mas não há configuração, comando de execução ou deploy efetivo confirmado.

### 4.2 Livros, imagens e QR

- **qrcode:** gera imagens PNG de QR no cadastro e nos cartões.
- **Pillow:** abre imagens recebidas e constrói cartões PNG.
- **OpenCV:** usado na decodificação de imagem e no scanner de câmera do backend.
- **NumPy:** usado para converter imagens para matrizes antes da decodificação.
- **PyZbar:** usado para tentar decodificar códigos de barras/QR no backend.
- **jsQR:** carregado por CDN e usado no scanner do navegador.
- **BarcodeDetector:** API nativa do navegador, tentada quando disponível.
- **Tabler Icons:** folha de ícones carregada por CDN no `index.html`.
- **Chart.js:** carregado por CDN e usado em `charts.js`.

### 4.3 Autenticação

- **Passlib:** usado, quando disponível, para verificar hashes e gerar novo hash.
- **bcrypt:** usado como alternativa para hashes bcrypt.
- **crypt:** usado como alternativa de verificação de hashes Unix.

### 4.4 Tecnologias não confirmadas como uso efetivo

- `DATABASE_MODE` aparece no exemplo de ambiente, mas não é lido pelo código observado.
- O cliente Supabase direto do frontend é preparado em `supabase-config.js`, mas não há biblioteca Supabase carregada no `index.html` nem chamada efetiva confirmada no fluxo analisado.
- Node.js foi usado para executar os dois testes JavaScript nesta análise, mas não há `package.json` nem dependência de aplicação Node confirmada.
- Render é mencionado em documentação/histórico, mas não foi encontrado arquivo de configuração ou evidência de deploy ativo. Não foi possível confirmar este deploy no estado atual do projeto.
- OpenCV, PyZbar, Pillow e qrcode são confirmados no código e nas dependências, mas a disponibilidade dos binários e bibliotecas em produção não foi confirmada.

## 5. Funcionamento geral

O fluxo nominal é:

1. O navegador acessa a aplicação Flask.
2. Flask entrega `frontend/index.html` e os arquivos estáticos.
3. O usuário interage com as páginas da SPA visual, que são blocos HTML mostrados e ocultados por `app.js`; não há roteador frontend dedicado.
4. `api.js` monta chamadas para `/api/...` usando `fetch`.
5. O blueprint correspondente valida a entrada e consulta ou altera o Supabase.
6. Se o caminho interno permitir e ocorrer uma falha compatível, alguns módulos leem ou escrevem os JSON de `backend/data/`.
7. A API devolve JSON ou CSV.
8. O frontend atualiza `Store`, `localStorage` e a tela.

O `before_request` de `app.py` faz uma verificação de `livros` para APIs que não são health/configuração. Se ela falha, a requisição recebe `503` antes da lógica normal da rota. O frontend exibe uma tela de espera do banco nesse cenário.

## 6. Módulos funcionais

### 6.1 Autenticação e papéis

**Arquivos:** `backend/api/auth.py`, `backend/scanner/routes.py`, `frontend/assets/js/app.js`, `frontend/index.html`.

O login tradicional envia `POST /api/auth/login` com `login` e `password`. O backend busca o usuário na tabela `usuarios`, aceita aliases de bibliotecário e verifica o valor armazenado usando Passlib, `crypt`, bcrypt ou, como compatibilidade legada, comparação de texto sem `$`.

A resposta informa `access`, `id`, `login` e `name`. O frontend classifica o usuário como `admin` ou `librarian`.

O frontend grava um cookie chamado `biblioteca-session` contendo dados de papel, login, nome, eventual aluno e horário da última atividade. O cookie tem validade declarada de sete dias e o JavaScript considera a sessão expirada após trinta minutos sem atividade. Esse cookie não é `HttpOnly`, não é validado pelo backend e não transforma as requisições seguintes em requisições autenticadas. O backend não encontrou middleware, decorator, JWT, bearer token ou verificação de papel nas APIs de negócio.

A interface esconde páginas administrativas de bibliotecários, mas essa é uma restrição visual. Uma chamada direta às APIs não recebe, no código atual, uma autorização correspondente ao papel.

### 6.2 Livros e acervo

**Arquivos:** `backend/api/books.py`, `frontend/assets/js/pages/books.js`, `database.sql`, `frontend/index.html`.

O cadastro exige `titulo` e `autor`. Também utiliza `isbn`, `area`, `genero_id` e `exemplares`. Cada livro recebe um UUID próprio. Ao criar o livro, o backend gera metadados de exemplares com código como `001`, identificador individual e `qr_data` no formato interno observado no código.

A listagem permite filtrar por texto em título, autor ou ISBN e por gênero. O frontend mostra total de exemplares e calcula disponíveis pela quantidade total menos os empréstimos ativos carregados.

O ISBN é um campo bibliográfico opcional. O identificador principal criado para o registro é o UUID `id`; o ISBN não substitui esse identificador. O QR de livro simples é gerado com o `id` do livro. Para múltiplos exemplares, os metadados guardam QR individual do exemplar.

### 6.3 ISBN

**Arquivos:** `backend/api/books.py`, `frontend/assets/js/pages/books.js`, `frontend/assets/js/qr-scanner.js`, `frontend/tests/books-isbn.test.js`.

O endpoint é `GET /api/books/isbn-lookup?isbn=...`.

O valor é normalizado removendo caracteres que não sejam números ou `X`, com conversão para maiúsculo. O backend valida checksum de ISBN-10 e ISBN-13 antes de consultar fontes externas.

O Groq é consultado primeiro por `_groq_lookup()` usando `GROQ_API_KEY`, `GROQ_API` ou `API_GROQ`, com resposta JSON estruturada. Depois, Google Books, ISBNsearch e Open Library são consultadas em paralelo para confirmação e complementação. O resultado pode conter `isbn`, `titulo`, `autor`, `categorias`, `area`, `genero_id` e `genero_nome`. Dados parciais do Groq são preservados quando as fontes externas não retornam dados. Há duas tentativas para falhas de rede/HTTP consideradas temporárias, timeout de seis segundos por tentativa, pequeno intervalo entre tentativas e cache em memória por quinze minutos, limitado a 128 itens. Resultados incompletos não são colocados no cache.

Verificação externa em 2026-09-22: o Secret chegou ao Codespaces, mas o Groq respondeu HTTP 403/código 1010; Google Books respondeu HTTP 429; ISBNsearch respondeu HTTP 200; Open Library respondeu HTTP 404 nos ISBNs testados. A integração está preparada, mas o acesso do Groq ainda depende de uma chave autorizada.

Erros confirmados pelo código:

- ISBN inválido: `400`;
- livro não encontrado: `404`;
- fonte externa indisponível: `502`.

Limitações: o sistema depende de serviços externos, ISBNsearch é interpretado como HTML e o comportamento desses provedores pode mudar. Não foi possível confirmar disponibilidade de cada provedor para todos os ISBNs.

### 6.4 Alunos

**Arquivos:** `backend/api/students.py`, `frontend/assets/js/pages/students.js`, `database.sql`.

Campos usados no cadastro: `nome`, `turma`, `carteirinha` e `sala_id`. O nome e a turma são obrigatórios. A turma é convertida para maiúsculo. Se a carteirinha não for informada, o backend cria um valor derivado de parte do UUID.

O aluno possui UUID interno. O cadastro também devolve uma imagem QR em base64 cujo conteúdo é o UUID do aluno. A resolução posterior aceita UUID ou `carteirinha`.

O módulo permite listar, buscar, consultar individualmente, criar, editar, excluir, importar CSV e conceder/revogar `is_librarian`. A exclusão é recusada quando há empréstimo ativo. Quando há suporte a `deleted_at`, o código tenta soft delete; caso contrário usa exclusão física ou marcação no JSON.

A importação aceita CSV enviado como arquivo ou texto, identifica `;` ou `,`, reconhece `nome`, `turma`, `carteirinha`/`matricula` e `sala_id`, e informa quantos registros foram adicionados e ignorados.

### 6.5 Salas

**Arquivos:** `backend/api/rooms.py`, `frontend/assets/js/pages/rooms.js`, `database.sql`.

Campos: `nome`, `codigo`, `descricao` e `capacidade`. O nome é obrigatório. A listagem calcula `total_alunos`. A exclusão desvincula os alunos da sala antes de remover a sala.

### 6.6 Gêneros

**Arquivos:** `backend/api/genres.py`, `frontend/assets/js/pages/genres.js`, `database.sql`.

Campos: `nome`, `icone` e `cor`. O nome é obrigatório. A listagem calcula `total_livros`. Ao remover um gênero, os livros associados têm `genero_id` definido como nulo.

### 6.7 Empréstimos

**Arquivos:** `backend/api/loans.py`, `frontend/assets/js/pages/loans.js`, `frontend/assets/js/app.js`, `database.sql`.

Para criar um empréstimo, o sistema exige `livro_id` e `aluno_id`. O backend confirma que ambos existem, verifica exemplares ativos, escolhe um exemplar disponível e registra:

- `id`;
- `livro_id`;
- `aluno_id`;
- `exemplar`;
- `exemplar_id`;
- `data_emprestimo`;
- `data_devolucao_prevista`;
- `devolvido_em`, inicialmente nulo;
- `observacao`;
- `criado_por`.

O prazo padrão é sete dias e o código aceita a quantidade de dias enviada, garantindo pelo menos um dia. A data do empréstimo pode ser informada; caso contrário usa a data atual.

O banco possui índice único para impedir dois empréstimos ativos do mesmo livro e exemplar. A verificação de disponibilidade e a inserção não são uma única transação no código Python; em concorrência, a constraint do banco é a proteção adicional observada.

O frontend permite localizar livro por título, autor, ISBN, ID ou QR de exemplar e localizar aluno por nome, carteirinha ou ID. A tela de empréstimos também mostra seleção de prazo e exemplar.

### 6.8 Devoluções

A rota `POST /api/loans/<loan_id>/return` rejeita empréstimo inexistente ou já devolvido. Atualiza `devolvido_em` com a data enviada ou a data atual e pode salvar uma observação.

Se o corpo enviar `student_id`, `student_qr`, `student_card` ou `carteirinha`, o backend resolve a referência e confirma que o aluno corresponde ao empréstimo. Se essa referência não for enviada, o código permite a devolução sem essa conferência adicional.

### 6.9 Renovação

A rota `POST /api/loans/<loan_id>/renew` rejeita empréstimos já devolvidos, acrescenta dias à data de devolução prevista e incrementa `renovacoes`. O código atual não impõe limite máximo de renovações.

### 6.10 Status e atrasos

A função `loan_status` usa somente estes status de API/frontend:

- `returned`: existe `devolvido_em`;
- `overdue`: não devolvido e a data prevista já passou;
- `active`: não devolvido e a data prevista não passou.

A interface também mostra textos como “Em dia”, “Atrasado” e “Vence hoje”. A view SQL `vw_emprestimos_ativos` possui os textos `atrasado`, `vence_hoje` e `em_dia`, mas o backend de relatórios observado calcula os status por Python e não consulta essa view.

### 6.11 QR Code e scanner

**Arquivos:** `backend/scanner/routes.py`, `backend/api/books.py`, `backend/api/students.py`, `frontend/assets/js/qr-scanner.js`, `frontend/assets/js/app.js`.

Há dois caminhos de leitura:

- o scanner normal do navegador usa `getUserMedia`, vídeo, canvas, `jsQR`, `BarcodeDetector` quando disponível e pode chamar `/api/qr/decode` como fallback;
- o backend recebe uma imagem base64 ou arquivo em `/api/qr/decode`, tenta Pillow, PyZbar/OpenCV e depois `cv2.QRCodeDetector`.

O resolvedor reconhece:

- `ADMIN-...` como cartão administrativo;
- código de exemplar no formato interno `EXEMPLAR-...`;
- ID de livro;
- ISBN de livro;
- ID de aluno;
- carteirinha de aluno.

A geração simples em `/api/qr/generate` recebe `data` e uma cor opcional e retorna PNG base64. O cadastro de livro e aluno gera QR automaticamente, usando o ID. Cartões imprimíveis são produzidos no backend como imagens PNG de 600x260 pixels.

O cartão de livro exibe título, autor, gênero, exemplar/quantidade e ISBN quando disponíveis. Para livros com `exemplares_meta`, pode retornar vários cartões, um por exemplar. Livros antigos sem metadados de exemplar recebem um cartão único com o ID do livro.

A carteirinha de aluno exibe nome, turma, sala, carteirinha e parte do ID; o QR representa o ID completo do aluno. A carteirinha administrativa exige senha validada no backend e informa usuário, perfil e outros dados visuais do cartão. O código atual monta um campo de senha no cartão administrativo; isso é uma limitação de segurança porque a senha pode aparecer no material gerado.

### 6.12 Relatórios

**Arquivos:** `backend/api/reports.py`, `frontend/assets/js/charts.js`, `frontend/index.html`.

Existem relatórios para:

- resumo de empréstimos ativos, atrasados e devolvidos;
- livros mais emprestados;
- empréstimos por turma;
- relatórios mensais armazenados em `relatorios_mensais`;
- geração de relatório mensal;
- exportação de atrasados em CSV;
- exportação de histórico completo;
- exportação de livros mais emprestados;
- exportação por turma;
- exportação de status de alunos.

Os gráficos usam Chart.js. Os CSVs são gerados no backend com cabeçalho UTF-8 e download pelo navegador.

As rotas de relatório não aplicam autenticação no backend. O acesso administrativo é imposto apenas pela interface que esconde a página de relatórios para bibliotecários.

## 7. Banco de dados confirmado pelo SQL

O `database.sql` cria estas tabelas:

| Tabela | Função e campos principais confirmados |
|---|---|
| `usuarios` | Usuários de login: UUID, nome, login, senha e data de criação. |
| `salas` | Salas: UUID, nome, código, descrição, capacidade e data de criação. |
| `generos` | Gêneros: UUID, nome, ícone, cor e data de criação. |
| `livros` | Livros: UUID, ISBN, título, autor, área, gênero, quantidade, `qr_id`, IDs/metadados JSONB de exemplares e data de criação. |
| `alunos` | Alunos: UUID, nome, turma, carteirinha, sala, `qr_id`, `is_librarian`, `deleted_at` e data de criação. |
| `emprestimos` | Relação aluno/livro: UUID, livro, aluno, exemplar, exemplar_id, datas, devolução, observação, criador, renovações e criação. |
| `relatorios_mensais` | Mês, totais, rankings JSONB, turmas JSONB, data e criador. |

Relacionamentos confirmados:

- `livros.genero_id` referencia `generos.id` com `ON DELETE SET NULL`;
- `alunos.sala_id` referencia `salas.id` com `ON DELETE SET NULL`;
- `emprestimos.livro_id` referencia `livros.id` com `ON DELETE CASCADE`;
- `emprestimos.aluno_id` referencia `alunos.id` com `ON DELETE CASCADE`.

O SQL também cria índices de busca, índices de UUID/relacionamento, unicidade parcial para carteirinhas, unicidade parcial para QR IDs e unicidade de exemplar ativo. Há duas views: `vw_emprestimos_ativos` e `vw_livros_ranking`.

O código de aplicação não usa diretamente as views observadas. A estrutura real do banco em um projeto Supabase externo depende de o SQL ter sido executado e de eventuais alterações posteriores. Não foi possível confirmar a estrutura externa em produção.

O SQL habilita RLS, mas as policies observadas permitem `true` em várias tabelas. A efetividade operacional dessas policies não foi testada contra um projeto Supabase externo.

## 8. Lista completa de endpoints reais

Os prefixos dos blueprints são registrados em `backend/app.py`.

### 8.1 Aplicação, health e configuração

| Método | Caminho | Finalidade |
|---|---|---|
| GET | `/api/health` | Testa a consulta à tabela `livros` e informa status do serviço/banco. |
| GET | `/api/auth/config/supabase` | Retorna URL e chave configuradas para o frontend, sem reproduzir valores neste relatório. |
| GET | `/api/auth/supabase-config` | Alias de compatibilidade da configuração Supabase. |
| GET | `/api/config/supabase` | Alias legado de configuração Supabase. |
| GET | `/api/supabase-config` | Alias legado de configuração Supabase. |
| GET | `/` e `/<path:path>` | Serve arquivos do frontend ou `index.html`; caminhos iniciados por `api/` retornam 404 se não houver rota. |
| GET | `/favicon.ico` | Serve favicon se existir ou retorna 204. |

### 8.2 Autenticação

| Método | Caminho | Entrada/retorno |
|---|---|---|
| POST | `/api/auth/login` | Recebe `login` e `password`; retorna classificação de acesso, ID, login e nome ou erro. |

### 8.3 Livros

| Método | Caminho | Entrada/retorno |
|---|---|---|
| GET | `/api/books/` | Query `q` e `genre`; lista livros enriquecidos com dados de gênero. |
| GET | `/api/books/isbn-lookup` | Query `isbn`; retorna dados bibliográficos ou erro 400/404/502. |
| GET | `/api/books/<book_id>` | Busca por ID, ISBN ou ID de exemplar. |
| POST | `/api/books/` | Recebe título, autor, ISBN, área, exemplares e gênero; cria livro e QR. |
| PUT | `/api/books/<book_id>` | Atualiza dados permitidos do livro. |
| DELETE | `/api/books/<book_id>` | Exclui ou marca livro; recusa se houver empréstimo ativo. |

### 8.4 Alunos

| Método | Caminho | Entrada/retorno |
|---|---|---|
| GET | `/api/students/` | Query `q`, `class` e `sala_id`; lista alunos e dados de sala. |
| GET | `/api/students/<student_id>` | Busca por ID ou carteirinha. |
| POST | `/api/students/` | Recebe nome, turma, carteirinha e sala; cria aluno e QR. |
| PUT | `/api/students/<student_id>` | Atualiza dados do aluno. |
| DELETE | `/api/students/<student_id>` | Exclui ou marca aluno; recusa se houver empréstimos ativos. |
| PATCH/POST | `/api/students/<student_id>/access` | Define `is_librarian`. |
| POST | `/api/students/import/csv` | Recebe arquivo multipart ou texto CSV e retorna contadores `added`/`skipped`. |

### 8.5 Empréstimos

| Método | Caminho | Entrada/retorno |
|---|---|---|
| GET | `/api/loans/` | Query `status` com `active`, `overdue` ou `returned`; lista empréstimos. |
| GET | `/api/loans/<loan_id>` | Busca empréstimo por ID. |
| POST | `/api/loans/` | Recebe livro, aluno, dias, data opcional, exemplar e observação; cria empréstimo. |
| POST | `/api/loans/<loan_id>/renew` | Recebe `dias`; estende vencimento e incrementa renovações. |
| POST | `/api/loans/<loan_id>/return` | Recebe data/observação e, opcionalmente, referência do aluno; registra devolução. |

### 8.6 Salas

| Método | Caminho | Entrada/retorno |
|---|---|---|
| GET | `/api/rooms/` | Lista salas com contagem de alunos. |
| GET | `/api/rooms/<room_id>` | Busca sala e alunos vinculados. |
| POST | `/api/rooms/` | Recebe nome, código, descrição e capacidade; cria sala. |
| PUT | `/api/rooms/<room_id>` | Atualiza sala. |
| DELETE | `/api/rooms/<room_id>` | Desvincula alunos e exclui sala. |

### 8.7 Gêneros

| Método | Caminho | Entrada/retorno |
|---|---|---|
| GET | `/api/genres/` | Lista gêneros com quantidade de livros. |
| POST | `/api/genres/` | Recebe nome, ícone e cor; cria gênero. |
| PUT | `/api/genres/<genre_id>` | Atualiza gênero. |
| DELETE | `/api/genres/<genre_id>` | Desvincula livros e exclui gênero. |

### 8.8 Relatórios

| Método | Caminho | Finalidade |
|---|---|---|
| GET | `/api/reports/chart-summary` | Dados agregados de ativos, atrasados e devolvidos. |
| GET | `/api/reports/top-books` | Ranking de livros; query opcional `limit`. |
| GET | `/api/reports/by-class` | Agregação por turma. |
| GET | `/api/reports/monthly` | Lista relatórios mensais persistidos. |
| POST | `/api/reports/monthly/generate` | Gera/upsert de relatório para `mes_ano`. |
| GET | `/api/reports/export/overdue` | CSV de empréstimos atrasados. |
| GET | `/api/reports/export/all` | CSV do histórico completo. |
| GET | `/api/reports/export/books` | CSV de livros mais emprestados. |
| GET | `/api/reports/export/by-class` | CSV por turma. |
| GET | `/api/reports/export/student-status` | CSV de situação dos empréstimos por aluno. |

### 8.9 QR e cartões

| Método | Caminho | Entrada/retorno |
|---|---|---|
| POST | `/api/qr/start` | Inicia thread de câmera no servidor; recebe índice opcional de câmera. |
| POST | `/api/qr/stop` | Interrompe a câmera do servidor. |
| GET | `/api/qr/result` | Retorna último resultado e flag `scanning`. |
| GET | `/api/qr/status` | Retorna estado da câmera e último resultado. |
| POST | `/api/qr/decode` | Recebe arquivo ou imagem base64; retorna códigos e resolução. |
| POST | `/api/qr/login` | Recebe `code` e senha quando necessária; resolve admin, bibliotecário, aluno ou negado. |
| POST | `/api/qr/card/admin/<login>` | Recebe senha; gera cartão administrativo PNG base64. |
| POST | `/api/qr/generate` | Recebe `data` e cor; retorna QR PNG base64. |
| GET | `/api/qr/card/book/<book_id>` | Gera cartão do livro, potencialmente um por exemplar. |
| GET | `/api/qr/card/student/<student_id>` | Gera carteirinha do aluno. |

Os endpoints de câmera do servidor existem no backend, mas o fluxo principal confirmado do frontend usa o scanner local do navegador. Não foi possível confirmar que `/api/qr/start`, `/api/qr/stop` ou `/api/qr/result` sejam chamados pela interface atual.

## 9. Segurança e autenticação

### Implementado

- Verificação de credenciais no backend.
- Suporte a vários formatos de hash e tentativa de re-hash de senhas legadas.
- Mensagem genérica para falha de usuário/senha.
- `Content-Security-Policy` configurada.
- `object-src 'none'`, `base-uri` e `frame-ancestors` definidos.
- Validações básicas de campos e constraints no SQL.
- Separação visual de funções de bibliotecário e administrador.

### Limitações confirmadas

- O cookie de sessão é criado pelo JavaScript, não é `HttpOnly` e não é verificado no backend.
- As rotas de negócio não exigem sessão, token ou papel.
- Um usuário com acesso à API pode chamar CRUD, relatórios e alteração de `is_librarian` sem o controle visual da interface.
- CORS aceita `*` para as APIs.
- A CSP permite `'unsafe-inline'` para scripts e estilos devido ao frontend atual.
- `SECRET_KEY` possui valor padrão de desenvolvimento se a variável não estiver definida; não foi encontrado uso dessa chave para autenticação de sessão.
- O SQL contém seeds de usuários com senhas legadas em valor literal; os valores não são reproduzidos aqui.
- O endpoint de configuração pode escolher `SUPABASE_SERVICE_KEY` como chave devolvida; a segurança desse arranjo depende da configuração real e é um risco relevante.
- O cartão administrativo pode incluir a senha no texto visual gerado.
- QR administrativo funciona como credencial portadora e exige senha no fluxo de login, mas não foi encontrado segundo fator adicional.
- As políticas RLS do SQL são amplas (`true`) para diversas tabelas. A aplicação real pode exigir revisão desse controle.

## 10. Histórico de modificações

O Git confirma, entre outros, os seguintes marcos recentes:

- `ad4ff99`: implementação inicial de leitor de código de barras.
- `fcf8098`: ajustes de foco e scanner QR.
- `f64d934`: suporte a `exemplar_id` e melhoria da busca por QR.
- `aa4b050`: validação de senha no login e geração de carteirinha administrativa.
- `c946b81`: ajuste da chave da Google Books.
- `3922445`: busca adicional na Open Library, normalização e ajustes de login.
- `3ccc4a4`: normalização de categorias e preenchimento de campos do livro.
- `d8a6a9f`: validação de ISBN, fallback de provedores e tratamento de erros.
- `c3cb933`: ajuste do tamanho do cartão administrativo.
- `cccbd24`: mensagens de erro e tela de espera para o banco.
- `6824b2f`: atualização dos relatórios até o estado atual do branch.

Esses commits comprovam que houve alterações nessas áreas, mas não comprovam por si só que uma funcionalidade esteja correta em produção. A implementação atual deve ser lida nos arquivos atuais.

### Implementado x planejado

**Implementado no código atual:** CRUDs, empréstimos, devolução, renovação, ISBN com provedores, QR, cartões, relatórios, login e tela de espera do banco.

**Não confirmado como implementado:** deploy Render ativo, reconciliação automática entre JSON e Supabase, autorização server-side por papel, JWT, fila offline, sincronização entre abas, cobertura E2E completa, monitoramento de produção e execução em câmera física.

## 11. Problemas e limitações classificadas

| Item | Estado | Evidência |
|---|---|---|
| Controle de acesso server-side | Ainda existente | Não há middleware/decorator de autenticação nas rotas de negócio. |
| Uso de cookie como sessão segura | Parcialmente resolvido | O frontend controla expiração, mas o backend não valida o cookie. |
| CORS permissivo | Ainda existente | `CORS(app, resources={r"/api/*": {"origins": "*"}})`. |
| CSP permissiva para o modelo atual | Ainda existente | Inclui `'unsafe-inline'`. |
| Fallback local | Parcialmente resolvido | Vários módulos possuem fallback, mas o `before_request` bloqueia APIs sem confirmação do banco. |
| Reconciliação após retorno do banco | Pendente | Não há fila, merge ou migração automática observada. |
| Concorrência na disponibilidade | Parcialmente resolvido | Há índice SQL de exemplar ativo, mas consulta e inserção não formam transação Python. |
| Senhas seed legadas | Ainda existente no SQL | O esquema inicial contém valores literais; o login tenta re-hash após sucesso. |
| Testes desatualizados/incompatíveis | Ainda existente | A execução atual encontrou nove falhas Python. |
| QR e cartões | Implementado com limitações | Geração e resolução existem; segurança do cartão admin e dependência de bibliotecas continuam riscos. |
| Deploy em Render | Não confirmado | Apenas referências documentais/nominais foram encontradas; não há configuração operacional confirmada. |

## 12. Testes

### Testes existentes

Python em `backend/tests/`:

- `test_auth_librarian_login.py`: login administrativo, alias de bibliotecário, senha legada e fallback esperado;
- `test_books_fallback.py`: listagem com cliente Supabase indisponível;
- `test_card_generation_performance.py`: geração de cartões;
- `test_env_loading.py`: carregamento de `.env` do backend;
- `test_isbn_lookup.py`: validação, fallback, cache e códigos de erro;
- `test_qr_id_resolution.py`: criação e resolução de livros/alunos por QR/ID;
- `test_reports_student_status.py`: exportação de situação de alunos;
- `test_supabase_reconnect.py`: expectativa de reconexão/cache do cliente;
- `test_unique_identifiers.py`: UUIDs e QR distintos.

JavaScript:

- `frontend/tests/books-isbn.test.js`: fluxo do formulário de ISBN;
- `frontend/tests/qr-scanner.test.js`: callback básico do scanner.

### Execução realizada nesta análise

Comando Python: `pytest -q` no ambiente virtual `.venv312`.

- **13 testes passaram.**
- **9 testes falharam.**
- Total observado: **22 testes Python**.

Falhas observadas:

- quatro testes de login esperavam comportamentos que não ocorreram com o cliente fake/estado atual;
- o teste de ambiente esperava `backend/.env`, que não foi encontrado;
- um teste referenciava `books.LookupError`, atributo que não existe no módulo atual;
- um teste de rota ISBN esperava `400`, mas a função monkeypatched fez a rota retornar `404`;
- dois testes esperavam atributos `_offline` e lógica de reconexão que não existem no `supabase_client.py` atual.

Comando JavaScript: `node --test frontend/tests/*.test.js`.

- **2 testes passaram.**
- **0 falharam.**

Esses resultados comprovam somente esta execução neste ambiente. Não comprovam disponibilidade de Supabase, funcionamento de câmera física, deploy, segurança de produção ou E2E.

## 13. Ambiente, execução e deploy

O servidor pode ser iniciado pelo bloco `if __name__ == "__main__"` de `backend/app.py`. Ele usa `PORT` ou `FLASK_PORT`, host `0.0.0.0` e modo debug quando `FLASK_ENV` é `development`.

O código carrega variáveis de `backend/.env` com `python-dotenv`. As variáveis esperadas no exemplo incluem URL do Supabase, chave do Supabase, chave secreta, porta e modo de ambiente.

`gunicorn` está declarado como dependência, mas não foi encontrado comando, Procfile, manifesto ou configuração de produção. Render é mencionado na documentação histórica, mas sua execução atual não foi comprovada.

O projeto usa Supabase como banco remoto previsto. Não foi possível confirmar a URL, o projeto remoto, o estado de RLS, o conteúdo real do banco ou um ambiente de produção ativo.

## 14. COMO UM ESTUDANTE DEVE ENTENDER ESTE PROJETO

### Frontend

Frontend é a parte que o usuário vê e utiliza no navegador. Neste projeto, ele está em `frontend/`. `index.html` contém as telas; `main.css` define a aparência; os arquivos JavaScript reagem a cliques, preenchem tabelas e chamam as APIs.

### Backend

Backend é a parte executada no servidor. Aqui ele está em Python/Flask, principalmente em `backend/app.py` e `backend/api/`. Ele recebe requisições do navegador, valida dados, aplica regras de empréstimo e acessa o banco.

### Banco de dados

Banco de dados é o local persistente dos registros. O sistema foi estruturado para usar Supabase, que fornece acesso a um banco PostgreSQL. O esquema SQL define livros, alunos, empréstimos, usuários, salas, gêneros e relatórios mensais.

### API

API é o conjunto de caminhos que permite ao frontend conversar com o backend. Por exemplo, o frontend chama a API de livros para listar ou criar um livro.

### Endpoint

Endpoint é um caminho específico da API, combinado com um método HTTP. `GET /api/books/` é um endpoint de listagem; `POST /api/books/` é outro endpoint no mesmo caminho, mas para criação.

### HTTP

HTTP é o protocolo usado pelas requisições do navegador. `GET` consulta, `POST` cria ou executa uma ação, `PUT` atualiza, `PATCH` altera parcialmente e `DELETE` remove.

### UUID

UUID é um identificador textual de 128 bits gerado pelo código com `uuid.uuid4()`. Livros, alunos, empréstimos e outras entidades recebem IDs próprios. No cadastro de livro, esse UUID é diferente do ISBN.

### QR Code

QR Code é uma imagem que representa um texto. Neste sistema, o texto pode ser o UUID do livro, o UUID do aluno, um identificador de exemplar ou um código administrativo. O QR Code não é automaticamente o ISBN.

### ISBN

ISBN é um identificador bibliográfico do livro, usado para consultar dados em fontes externas e armazenado no campo `isbn`. O sistema também possui seus próprios UUIDs e identificadores de exemplares. Portanto, ISBN, ID interno e QR Code são conceitos diferentes.

### Flask

Flask é o framework Python que cria o servidor HTTP. `app.py` registra os blueprints e entrega o frontend; os módulos de API implementam as funções de cada área.

### Supabase

Supabase é o serviço usado pelo projeto para acessar o banco PostgreSQL por uma API cliente. O backend chama `get_client().table(...).select/insert/update/delete` e executa a consulta. Os JSON locais aparecem como fallback em módulos, mas o estado atual também contém uma barreira que exige confirmar o banco para liberar quase todas as APIs.

### Como tudo se conecta

O usuário preenche uma tela do frontend. O JavaScript chama um endpoint HTTP. Flask recebe a chamada, o módulo da API valida os dados e consulta o Supabase. A resposta volta em JSON ou CSV. O frontend atualiza o estado do `Store` e redesenha a tela.

No empréstimo, por exemplo: o usuário seleciona um livro e um aluno; `app.js` envia IDs para `POST /api/loans/`; `loans.py` confirma livro, aluno e exemplar; calcula o vencimento; grava o empréstimo; e o frontend mostra o status.

## 15. Mapa de arquivos importantes

| Arquivo | Função | Parte do sistema | Importância |
|---|---|---|---|
| `backend/app.py` | Inicialização, blueprints, bloqueio por banco, health e arquivos estáticos | Servidor | Muito alta |
| `backend/api/auth.py` | Login e configuração Supabase | Autenticação | Muito alta |
| `backend/api/books.py` | CRUD de livros, ISBN e metadados de exemplares | Acervo | Muito alta |
| `backend/api/students.py` | CRUD, CSV e acesso de bibliotecário | Alunos | Muito alta |
| `backend/api/loans.py` | Criação, disponibilidade, devolução e renovação | Circulação | Muito alta |
| `backend/api/reports.py` | Agregações, relatório mensal e CSV | Relatórios | Alta |
| `backend/api/rooms.py` | CRUD e vínculos de salas | Cadastros | Média |
| `backend/api/genres.py` | CRUD e vínculos de gêneros | Cadastros | Média |
| `backend/scanner/routes.py` | Decodificação, QR, login QR e cartões PNG | QR/carteirinhas | Muito alta |
| `backend/api/_helpers.py` | JSON, tabelas e flags de schema | Persistência auxiliar | Alta |
| `backend/utils/supabase_client.py` | Cliente e execução Supabase | Banco | Muito alta |
| `backend/utils/helpers.py` | UUID, datas e status | Regras compartilhadas | Alta |
| `database.sql` | Schema, relações, índices, RLS, views e seeds | Banco | Muito alta |
| `frontend/index.html` | Estrutura das telas e carregamento de scripts | Interface | Muito alta |
| `frontend/assets/js/api.js` | Cliente HTTP do frontend | Comunicação | Muito alta |
| `frontend/assets/js/app.js` | Fluxos globais, login e circulação | Controle frontend | Muito alta |
| `frontend/assets/js/store.js` | Estado/cache da interface | Estado frontend | Alta |
| `frontend/assets/js/qr-scanner.js` | Câmera e leitura no navegador | Scanner | Alta |
| `frontend/assets/js/pages/books.js` | Acervo e ISBN no frontend | Livros | Alta |
| `frontend/assets/js/pages/students.js` | Alunos e histórico | Alunos | Alta |
| `frontend/assets/js/pages/loans.js` | Tabelas de empréstimos e painel | Circulação | Alta |
| `frontend/assets/js/charts.js` | Gráficos | Relatórios | Média |
| `backend/requirements.txt` | Dependências Python | Ambiente | Alta |
| `backend/tests/` | Testes automatizados | Qualidade | Alta |
| `frontend/tests/` | Testes JavaScript | Qualidade | Média |

## 16. Resumo do estado atual

### Problema original

O controle manual em papel dificultava consultar e atualizar empréstimos, alunos, livros, datas de devolução e situação dos exemplares.

### Solução criada

Foi criada uma aplicação web Flask com frontend JavaScript para cadastrar acervo e alunos, registrar circulação, gerar relatórios e usar QR Codes, com Supabase/PostgreSQL como persistência prevista e caminhos JSON presentes em módulos.

### Funcionalidades confirmadas

- login por usuário e senha;
- classificação frontend de administrador/bibliotecário;
- cookie de sessão controlado pelo JavaScript, sem autenticação server-side correspondente;
- cadastro, consulta, edição e exclusão de livros;
- ISBN opcional, validação e consulta em três fontes externas;
- exemplares e QR por livro/exemplar;
- cadastro, consulta, edição, exclusão e importação CSV de alunos;
- salas e gêneros;
- concessão/revogação de `is_librarian`;
- empréstimos, devoluções e renovações;
- status ativo, atrasado e devolvido;
- scanner de navegador e decodificação backend;
- login por QR administrativo/bibliotecário;
- cartões PNG de livro, aluno e administrador;
- gráficos, relatórios mensais e exportações CSV;
- health check e tela de espera do banco.

### Tecnologias confirmadas

Python, Flask, Flask-CORS, python-dotenv, cliente Supabase, PostgreSQL pelo SQL, JavaScript sem framework, HTML, CSS, Chart.js, jsQR, Tabler Icons, qrcode, Pillow, OpenCV, NumPy, PyZbar, Passlib, bcrypt e crypt. Gunicorn está declarado, mas seu uso em deploy não foi confirmado.

### Melhorias realizadas

O histórico Git confirma melhorias recentes em scanner/foco de câmera, identificadores e exemplares, login e carteirinha administrativa, integração/fallback de ISBN, validação de checksum, combinação de provedores, normalização de categorias, relatórios e mensagens/tela de espera do banco.

### Pendências

- autenticação e autorização server-side das APIs;
- revisão das policies RLS;
- reconciliação entre JSON e Supabase;
- transação ou estratégia robusta para concorrência de exemplares;
- correção/alinhamento dos testes Python falhos;
- confirmação e configuração de deploy;
- testes E2E e testes reais de câmera;
- revisão de exposição de chaves, cookies, CORS, CSP, seed de senhas e cartão administrativo.

### Limitações

- Dependência de Supabase e provedores externos de ISBN.
- Fallback JSON pode divergir do banco e não possui reconciliação confirmada.
- Papéis são aplicados visualmente no frontend, não nas rotas de negócio.
- O cookie de sessão não é uma sessão server-side segura.
- Muitas exceções amplas podem esconder falhas de schema ou configuração.
- Não há limite de renovações no backend.
- Não foi confirmada infraestrutura de produção.

### Informações não confirmadas

- quantidade atual de livros, alunos, usuários ou empréstimos em produção;
- estado e conteúdo do Supabase remoto;
- deploy ativo no Render;
- execução de Gunicorn;
- funcionamento de câmera física em dispositivos reais;
- cobertura E2E completa;
- reconciliação automática de dados;
- efetividade das policies RLS em ambiente externo;
- uso real dos endpoints de câmera do servidor pela interface;
- estabilidade e disponibilidade dos provedores externos para qualquer ISBN.

Para cada item acima: Não foi possível confirmar esta informação no estado atual do projeto.

## 17. INFORMAÇÕES IMPORTANTES PARA OUTRA IA

Ao responder perguntas futuras sobre este projeto, use estas regras factuais:

- O problema de origem é a substituição de uma lista manual em papel por controle digital de livros, alunos, empréstimos e devoluções.
- O objetivo funcional observado é organizar o acervo e a circulação, mas não devem ser inventadas estatísticas ou quantidades.
- A arquitetura é uma aplicação Flask que serve uma interface HTML/CSS/JavaScript e APIs no mesmo processo.
- O frontend chama o backend com `fetch` em caminhos `/api`.
- O backend usa Supabase como caminho principal de persistência; módulos também possuem fallback JSON, mas o `before_request` pode bloquear APIs quando não confirma o banco.
- O SQL confirma as tabelas `usuarios`, `salas`, `generos`, `livros`, `alunos`, `emprestimos` e `relatorios_mensais`, além de views e policies.
- O banco usa PostgreSQL por meio do Supabase; o backend não abre uma conexão PostgreSQL direta.
- Livro tem UUID interno, ISBN opcional, título, autor, área, gênero e exemplares. ISBN não deve ser descrito como o ID principal.
- QR de livro/aluno representa normalmente o ID interno; QR de exemplar usa metadado próprio; `ADMIN-*` representa cartão administrativo.
- ISBN usa Groq como fonte inicial e Google Books, ISBNsearch e Open Library em confirmação paralela, com validação, retry, combinação de dados e cache limitado. O Groq preserva dados parciais quando as fontes externas não respondem.
- Aluno tem UUID, nome, turma, carteirinha, sala e flag `is_librarian`; o QR de aluno usa o ID.
- Empréstimo relaciona livro e aluno, escolhe exemplar, registra datas, observação, criador e possível `exemplar_id`.
- Os status de aplicação são `active`, `overdue` e `returned`.
- Devolução atualiza `devolvido_em`; renovação estende a data e incrementa `renovacoes`, sem limite observado.
- Login verifica credenciais no backend, mas a autorização posterior não é aplicada às APIs por sessão, token ou papel.
- O frontend mantém `currentUser` e um cookie JavaScript de atividade; isso não equivale a autenticação server-side.
- O frontend esconde telas conforme o papel, mas não se deve afirmar que isso protege endpoints.
- Chart.js é usado nos gráficos; jsQR e BarcodeDetector no scanner do navegador; OpenCV/PyZbar/Pillow aparecem no caminho backend.
- Cartões de livro podem ser gerados por exemplar; carteirinha de aluno inclui dados de identificação e QR.
- Relatórios existem em JSON e CSV, mas seus endpoints não exigem autenticação observada.
- Gunicorn aparece como dependência, mas Render/produção não estão confirmados.
- Os testes atuais não estão todos verdes: a execução observada teve 13 aprovações e 9 falhas Python; os dois testes JavaScript executados passaram.
- Resultados de documentos antigos não devem ser apresentados como estado atual sem reconciliação com o código.
- Não invente quantidade de registros, usuários, livros, alunos, estatísticas, disponibilidade de produção, correções ou funcionalidades futuras.
- Para qualquer comportamento não demonstrado por código, SQL ou teste reproduzível, escreva: **Não foi possível confirmar esta informação no estado atual do projeto.**
