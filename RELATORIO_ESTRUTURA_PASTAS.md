# Relatório 1 - Estrutura de Pastas e Funções do Projeto

## Visão Geral
Este relatório descreve todas as pastas e os principais arquivos do projeto, explicando sua função para você estudar e entender a arquitetura do sistema.

---

## Raiz do projeto

### `README.md`
- Descreve o projeto, a stack, pré-requisitos, instalação e execução.
- Serve como documentação inicial para usuários e desenvolvedores.

### `COMO_USAR.md`
- Guia passo a passo para rodar o projeto.
- Contém instruções de instalação, rodar o backend, login e testes.

### `ANALISE_PROBLEMAS.md`
- Documento de análise de problemas do projeto.
- Provavelmente lista falhas, vulnerabilidades e sugestões.

### `RELATORIO_COMPLETO.md`
- Relatório geral de correções, mudanças e melhorias no projeto.
- Pode incluir o histórico do processo de desenvolvimento.

### `RESUMO_FINAL.txt`
- Sumário executivo do projeto.
- Normalmente apresenta o estado final do software e conclusões.

### `TESTES_EXECUTADOS.md`
- Relatório dos testes executados no projeto.
- Inclui endpoints testados, resultados e possíveis falhas.

### `database.sql`
- Script SQL com a estrutura de banco de dados.
- Pode ser usado para criar tabelas ou popular o banco local.

### `package-lock.json`
- Lockfile do npm usado pelo frontend.
- Garante versões fixas de dependências JavaScript.

---

## Pasta `backend/`

Esta pasta contém o servidor Flask, a API e o suporte ao modo offline.

### `backend/app.py`
- Inicia o servidor Flask.
- Registra blueprints da API e do scanner de QR.
- Configura CORS para rotas `/api/*`.
- Aplica cabeçalhos de segurança CSP.
- Trata erros HTTP e genéricos.
- Implementa health check em `/api/health`.
- Serve o frontend SPA através de `index.html`.

### `backend/.env.example`
- Modelo de variáveis de ambiente.
- Exemplo de configuração para Supabase e chaves secretas.

### `backend/README.md`
- Documentação dedicada ao backend.
- Contém instruções específicas para rodar o servidor Python.

---

## Pasta `backend/api/`

Contém os módulos de API do backend, separados por recurso.

### `backend/api/__init__.py`
- Inicializa o pacote `backend/api`.
- Normalmente vazio, mas permite importações relativas.

### `backend/api/_helpers.py`
- Funções comuns de leitura e escrita de JSON.
- Verifica se tabelas Supabase existem e se colunas suportam soft delete.
- Detecta erros de modo offline.
- Recomendado para entender o fallback do banco.

### `backend/api/auth.py`
- Autenticação de usuário com `POST /api/auth/login`.
- Funções `hash_password` e `verify_password` usando SHA-256 + salt.
- Define usuários padrão `admin` e `biblioteca`.
- Endpoints de configuração Supabase para o frontend.

### `backend/api/books.py`
- CRUD de livros:
  - `GET /api/books/` lista livros.
  - `GET /api/books/<id>` busca livro por ID ou ISBN.
  - `POST /api/books/` cria livro e gera QR Code.
  - `PUT /api/books/<id>` atualiza livro.
  - `DELETE /api/books/<id>` exclui livro, validando empréstimos ativos.
- Implementa fallback local em `backend/data/livros.json`.
- Também busca por gênero e monta metadados de gênero para cada livro.

### `backend/api/students.py`
- CRUD de alunos:
  - `GET /api/students/` lista alunos.
  - `GET /api/students/<id>` busca aluno por ID ou carteirinha.
  - `POST /api/students/` cria aluno com validações.
  - `PUT /api/students/<id>` atualiza aluno.
  - `DELETE /api/students/<id>` exclui aluno, impedindo exclusão com empréstimos ativos.
- Implementa importação de CSV em `/students/import/csv`.
- Permite conceder ou revogar acesso de bibliotecário via `/students/<id>/access`.
- Usa fallback em `backend/data/alunos.json`.

### `backend/api/loans.py`
- Gerencia empréstimos:
  - `GET /api/loans/` lista empréstimos.
  - `GET /api/loans/<id>` consulta empréstimo.
  - `POST /api/loans/` cria empréstimo.
  - `POST /api/loans/<id>/renew` renova empréstimo.
  - `POST /api/loans/<id>/return` devolve empréstimo.
- Lógica de disponibilidade de exemplares.
- Verifica se aluno e livro existem.
- Classifica status de empréstimo (`active`, `overdue`, `returned`).
- Usa fallback local em `backend/data/emprestimos.json`.

### `backend/api/genres.py`
- CRUD de gêneros:
  - `GET /api/genres/` lista gêneros.
  - `POST /api/genres/` cria gênero.
  - `PUT /api/genres/<id>` atualiza gênero.
  - `DELETE /api/genres/<id>` remove gênero.
- Calcula total de livros por gênero.
- Ao excluir, remove o vínculo `genero_id` de livros.

### `backend/api/rooms.py`
- CRUD de salas:
  - `GET /api/rooms/` lista salas.
  - `GET /api/rooms/<id>` consulta sala e alunos da sala.
  - `POST /api/rooms/` cria sala.
  - `PUT /api/rooms/<id>` atualiza sala.
  - `DELETE /api/rooms/<id>` remove sala e desvincula alunos.
- Mantém contagem de alunos por sala.
- Usa fallback local em `backend/data/salas.json`.

### `backend/api/reports.py`
- Relatórios e exportações:
  - `GET /api/reports/chart-summary` resumo de empréstimos.
  - `GET /api/reports/top-books` livros mais emprestados.
  - `GET /api/reports/by-class` estatísticas por turma.
  - `GET /api/reports/monthly` lista relatórios mensais.
  - `POST /api/reports/monthly/generate` gera relatório mensal.
  - CSV export: `/api/reports/export/overdue`, `/api/reports/export/all`.
- Agrupa dados de livros, alunos e empréstimos.
- Calcula métricas de uso reais.

### `backend/api/validators.py`
- Contém validações reutilizáveis.
- Provavelmente usado para validar entradas de formulários API.

---

## Pasta `backend/scanner/`

Contém o módulo de QR Code e scanner de câmera.

### `backend/scanner/routes.py`
- Implementa scanner de QR pelo servidor Flask.
- Controla estado da câmera com threads.
- Endpoints:
  - `POST /api/qr/start` inicia scanner.
  - `POST /api/qr/stop` para scanner.
  - `GET /api/qr/result` retorna último código detectado.
  - `GET /api/qr/status` informa se scanner está ativo.
  - `POST /api/qr/decode` decodifica imagem base64.
  - `POST /api/qr/login` realiza login via QR.
  - `GET /api/qr/card/book/<id>` gera cartão de livro.
  - `GET /api/qr/card/student/<id>` gera cartão de aluno.
- Resolves QR como `book`, `student`, `admin`.
- Usa OpenCV, PyZbar, PIL e NumPy.

---

## Pasta `backend/data/`

### `backend/data/alunos.json`
- Dados de alunos usados no modo offline.
- Permite que o sistema funcione sem Supabase.

### `backend/data/emprestimos.json`
- Registros de empréstimos locais.
- Suporta consulta, devolução e renovação offline.

### `backend/data/generos.json`
- Categorias de livros.
- Usa IDs, nomes, ícones e cores.

### `backend/data/livros.json`
- Catálogo de livros local.
- Contém título, autor, ISBN, gênero e número de exemplares.

### `backend/data/salas.json`
- Cadastro de salas de aula.
- Usa IDs, nomes, códigos e capacidade.

---

## Pasta `backend/tests/`

### `backend/tests/test_books_fallback.py`
- Testa fallback de livros quando Supabase não está disponível.
- Verifica se a API retorna dados do JSON local.

### `backend/tests/test_supabase_reconnect.py`
- Testa reconexão com Supabase.
- Verifica comportamento quando o servidor Supabase está off.

---

## Pasta `backend/utils/`

### `backend/utils/helpers.py`
- Funções auxiliares de data e IDs:
  - `new_id()` gera UUID.
  - `today_str()` retorna data atual em ISO.
  - `add_days()` adiciona dias a uma data.
  - `days_until()` calcula dias entre datas.
  - `loan_status()` classifica status de empréstimo.

### `backend/utils/supabase_client.py`
- Conexão com Supabase.
- Fallback offline automático quando a conexão falha.
- Classe `SupabaseClient` com wrappers para seletor, inserção, atualização.
- Stub `_OfflineClient` para permitir execução sem banco.
- Detecta vários tipos de erros de rede.

---

## Pasta `frontend/`

Contém a interface web do sistema: HTML, CSS e JavaScript.

### `frontend/index.html`
- Ponto de entrada da interface.
- Carrega os scripts e o estilo principal.
- Define a estrutura básica do SPA.

### `frontend/assets/css/main.css`
- Estilos visuais para a aplicação.
- Layout de páginas, botões, tabelas, modais e responsividade.

### `frontend/assets/js/api.js`
- Wrapper para chamadas de API.
- Centraliza comunicação com `/api/books`, `/api/students`, `/api/loans`, `/api/reports`, `/api/rooms`, `/api/genres`, `/api/qr`.
- Trata erros e parse de JSON.
- Usa `API_BASE` para construir URLs.

### `frontend/assets/js/app.js`
- Controlador principal do frontend.
- Lida com login tradicional e login por QR.
- Mantém estado global do usuário e empréstimos.
- Gerencia navegação entre páginas do SPA.
- Faz sincronização de dados com backend e cache local.
- Aplica permissões para admin e bibliotecário.

### `frontend/assets/js/charts.js`
- Cria gráficos para a área de relatórios.
- Provavelmente usa Chart.js.
- Exibe estatísticas de empréstimos, atrasos e frequência.

### `frontend/assets/js/config/field-mapping.js`
- Contém mapeamento de campos para formulários.
- Facilita o uso de valores dinâmicos no frontend.

### `frontend/assets/js/lib/supabase-config.js`
- Carrega configuração do Supabase no cliente.
- Fornece URL e chave quando disponível.

### `frontend/assets/js/pages/books.js`
- Lógica da página de livros.
- Renderiza lista de livros e ações de cadastro/edição.

### `frontend/assets/js/pages/genres.js`
- Lógica da página de gêneros.
- Renderiza categorias e ações de CRUD.

### `frontend/assets/js/pages/loans.js`
- Lógica da página de empréstimos.
- Renderiza fluxo de empréstimo, devolução e renovação.

### `frontend/assets/js/pages/rooms.js`
- Lógica da página de salas.
- Renderiza salas e contagem de alunos.

### `frontend/assets/js/pages/students.js`
- Lógica da página de alunos.
- Renderiza cadastro, importação CSV e acesso de bibliotecário.

### `frontend/assets/js/qr-scanner.js`
- Interface de scanner QR no navegador.
- Controla câmera e leitura de códigos.
- Integra com o fluxo de empréstimo e histórico.

### `frontend/assets/js/store.js`
- Armazena dados localmente no navegador.
- Garante persistência offline e cache.
- Possivelmente usa `localStorage`.

### `frontend/assets/js/utils.js`
- Utilitários de DOM, data e interface.
- Funções de toast, modal, badge de status e helpers de seleção.
- Utilitários para formatação de datas e cálculo de dias.

---

## Conclusão
Este relatório detalha todas as pastas e arquivos principais do projeto e explica a função de cada um. Ele foi preparado para ajudar no seu estudo e entendimento do funcionamento completo do sistema.
