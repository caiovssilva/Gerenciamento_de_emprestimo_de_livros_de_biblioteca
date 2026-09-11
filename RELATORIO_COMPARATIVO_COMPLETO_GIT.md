# Relatorio comparativo completo do historico Git

## 1. Escopo e criterio

Este documento compara a evolucao do repositorio desde o commit inicial ate o estado observado em 11/09/2026. A analise considera os 53 commits visiveis nas referencias locais, os arquivos versionados do produto e as alteracoes ainda nao commitadas no working tree.

Arquivos de ambiente (`.venv312`), caches (`__pycache__`, `.pytest_cache`) e arquivos compilados nao sao tratados como evolucao do produto. Eles sao artefatos locais.

Estado no momento da analise:

- Branch: `fix/login-error-message`.
- Commit HEAD: `cccbd24`.
- Alteracoes locais: `backend/api/books.py`, `backend/scanner/routes.py` e `frontend/assets/js/pages/books.js`.
- As alteracoes locais nao foram incluidas em nenhum commit.

## 2. Linha do tempo dos commits

### Fundacao, login e banco

- `0713d66` — commit inicial.
- `a8cbaf5` — inclusao dos arquivos do projeto.
- `95ff403` — correcao do botao de login e mensagem de erro.
- `34a3783` — fallback de clique do login.
- `cba9160` — ajustes gerais do banco.
- `969b0b6` — endurecimento de seguranca e qualidade.
- `d754ccb` — correcao de hash de senha de desenvolvimento.
- `a566cb0` — suporte ao Passlib.
- `e2019a6` — suporte ao bcrypt.
- `9acf26d` — verificacao de senha e recuperacao de usuarios.
- `a2844fb` — alias de bibliotecario e testes de autenticacao.

### Documentacao e interface

- `f17e24d` — relatorio de revisao e seguranca.
- `7acca78` — resumo final de seguranca.
- `6fdd724` — relatorio de testes de endpoints.
- `e968b13` — guia de uso.
- `9e2ce63` — mensagens de login e favicon.
- `606b0da` — mensagem de login e usabilidade do tema.
- `71260bd` — interface e responsividade.
- `3e9dff5` — paleta e variaveis CSS.
- `0a52f66` — logo, avatar e tipografia da barra lateral.
- `d12460c` — reformulacao da tela de login.
- `44c5c42` — relatorio amplo para o TCC.
- `b31a118` — relatorio de estudo do projeto.

### Deploy, IDs e QR codes

- `3eca1ea` — preparacao do backend para Render.
- `103a0bb` — mecanismo para manter o Render ativo.
- `e853fd0`, `f27ad3e` — ajustes de deploy e nomenclatura.
- `40136aa` — correcao geral de IDs.
- `1e05717` — QR codes unicos para exemplares.
- `2792bbb` — ajustes intermediarios do fluxo de QR.
- `978485c` — ajustes em `book.js` para QR codes.
- `f64d934` — suporte a `exemplar_id` e busca de livros por QR.
- `bac57a1` — branding e melhoria do scanner QR.
- `274ee8a` — mensagens de login e troca de camera.
- `ad4ff99` — implementacao inicial de leitor de codigo de barras.
- `fcf8098` — correcao de foco da camera.

### Desempenho, dados e relatorios

- `08884f3` — melhorias funcionais e de desempenho.
- `5edede6` — gerenciamento de sessao e performance.
- `0a36135` — correcao de textos no relatorio de status.
- `ae0b988` — atualizacao de `livros.json`.
- `a692683` — remocao de codificacao e arquivos sem uso.
- `f212e99` — relatorio de estrutura e avaliacao.
- `ba40882` — relatorio de estado atual e ajustes de ignore.
- `6a5e78c` — atualizacao do Python.
- `dd1de24` — atualizacoes intermediarias.

### ISBN, autenticacao recente e conexao

- `3922445` — melhorias de login, OpenLibrary, normalizacao de categorias e dependencias.
- `c946b81` — correcao da chave da Google Books API.
- `bc76ea4` — atualizacao do Python.
- `82a47cb` — mensagem de login e mostrar/ocultar senha.
- `aa4b050` — login e geracao de carteirinha administrativa com senha.
- `cccbd24` — mensagens de erro e tela de espera para conexao com o banco.

## 3. Evolucao funcional comparada

O sistema saiu de uma base de cadastro e emprestimos para uma SPA de biblioteca com seis areas de API, controle de acesso, QR codes por exemplar, leitor de codigo de barras, consulta externa de ISBN, relatorios e fallback local.

A evolucao mais importante foi a separacao progressiva de responsabilidades:

1. O banco passou a ser acessado por helpers e cliente Supabase.
2. As entidades foram divididas em blueprints (`auth`, `books`, `students`, `loans`, `rooms`, `genres`, `reports`, `qr`).
3. O frontend passou a centralizar chamadas em `api.js`, estado em `store.js` e telas em arquivos por pagina.
4. O scanner ganhou leitura local no navegador e fallback no backend.
5. A autenticacao passou a verificar senha, diferenciar administrador e bibliotecario e validar a carteirinha administrativa.
6. O sistema recebeu verificacoes de saude e bloqueio de APIs quando o banco esta indisponivel.

## 4. Arquivos do produto e papel atual

### Backend

- `backend/app.py`: cria o Flask, carrega ambiente, registra blueprints, serve o frontend, aplica CORS, CSP, health check e bloqueio de APIs sem banco.
- `backend/api/_helpers.py`: leitura/escrita JSON, deteccao de tabela, flags de coluna, datas e tratamento de erros.
- `backend/api/auth.py`: login, usuarios, senha e configuracao do Supabase.
- `backend/api/books.py`: CRUD de livros, exemplares, consulta de ISBN e geracao de QR de livro.
- `backend/api/students.py`: CRUD, busca, importacao CSV e permissao de bibliotecario.
- `backend/api/loans.py`: criacao, devolucao, renovacao e listagem de emprestimos.
- `backend/api/reports.py`: indicadores, relatorios mensais e exportacoes CSV.
- `backend/api/rooms.py`: CRUD de salas e vinculo com alunos.
- `backend/api/genres.py`: CRUD de generos.
- `backend/scanner/routes.py`: camera, decodificacao, resolucao de QR e cartoes PNG.
- `backend/utils/supabase_client.py`: criacao/reconexao do cliente Supabase.
- `backend/utils/helpers.py`: funcoes auxiliares compartilhadas.
- `backend/requirements.txt` e `requirements.txt`: dependencias Python.
- `backend/data/*.json`: dados locais de fallback/demonstracao.

### Frontend

- `frontend/index.html`: shell da SPA, paginas, modais e formularios.
- `frontend/assets/css/main.css`: tema, layout, responsividade, tabelas, modais e scanner.
- `frontend/assets/js/app.js`: navegacao, login, sessao, permissoes e acoes globais.
- `frontend/assets/js/api.js`: cliente HTTP e mapa de endpoints.
- `frontend/assets/js/store.js`: estado local sincronizado com a API.
- `frontend/assets/js/utils.js`: DOM, datas, mensagens e utilitarios.
- `frontend/assets/js/pages/books.js`: acervo, cadastro, ISBN, generos, exemplares e QR.
- `frontend/assets/js/pages/students.js`: alunos, importacao e historico.
- `frontend/assets/js/pages/loans.js`: emprestimos e devolucoes.
- `frontend/assets/js/pages/rooms.js` e `genres.js`: cadastros correspondentes.
- `frontend/assets/js/charts.js`: graficos e atualizacao dos relatorios.
- `frontend/assets/js/qr-scanner.js`: camera, QR, EAN e comunicacao com `/api/qr/decode`.
- `frontend/assets/js/lib/supabase-config.js`: configuracao publica usada pelo cliente web.

### Dados, operacao e qualidade

- `database.sql`: esquema Supabase, tabelas, indices, views e dados iniciais.
- `.github/workflows/*.yml`: manutencao automatica do servico hospedado.
- `backend/tests/*.py` e `frontend/tests/*.js`: autenticacao, fallback, IDs, QR, reconexao, desempenho e scanner.
- `backend/README.md` e documentos existentes: instalacao, uso, testes, riscos, estrutura e TCC.

## 5. Alteracoes locais ainda nao commitadas

### `backend/api/books.py`

- Adicionado `unicodedata` para normalizar acentos.
- Criado `_match_genre()`, que consulta generos no Supabase e usa `generos.json` offline.
- Categorias externas como `Science Fiction`, `History` e `Biography` podem ser associadas a generos locais.
- `_lookup_isbn()` passou a devolver `area`, `genero_id` e `genero_nome`, alem dos campos existentes.
- O parser `_IsbnSearchParser` agora aceita `Author:` e `Authors:`.

### `frontend/assets/js/pages/books.js`

- O retorno do ISBN preenche autor e area somente quando os campos estao vazios.
- O genero usa `genero_id` retornado pelo backend.
- Escolhas manuais nao sao sobrescritas.

### `backend/scanner/routes.py`

- A carteirinha administrativa e ampliada para `900x390`.
- Carteirinhas de alunos e cartoes de livros permanecem em `600x260`.

## 6. Validacoes observadas

- `backend/api/books.py` compila.
- `frontend/assets/js/pages/books.js` e `qr-scanner.js` passam em `node --check`.
- O teste de fallback de livros passou.
- Os testes de resolucao QR passaram.
- A geracao dos cartoes confirmou admin `900x390` e aluno `600x260`.
- A biblioteca nativa `libzbar0t64` foi instalada no ambiente para o `pyzbar` ler EAN/ISBN.

## 7. Riscos e pontos de atencao

- O working tree esta sujo; as tres alteracoes locais precisam ser revisadas antes de commit.
- O sistema depende de `libzbar` no ambiente para o fallback de codigo de barras.
- A Google Books API pode responder `429` por cota; OpenLibrary pode responder `200` sem cadastro do ISBN.
- O endpoint `/api/livros/isbn-lookup` nao existe; a rota correta e `/api/books/isbn-lookup`.
- O arquivo `backend/.env` nao deve ser versionado. Chaves expostas devem ser revogadas.
- Algumas consultas de compatibilidade aparecem como `400` quando colunas opcionais, como `deleted_at`, nao existem; os fallbacks atuais evitam interrupcao, mas o diagnostico merece limpeza futura.

## Conclusao

A historia Git mostra uma evolucao incremental, com foco em corrigir login, robustecer persistencia, ampliar identificacao por QR/codigo de barras e transformar o cadastro em um fluxo assistido por ISBN. O estado atual e funcional, mas possui mudancas locais importantes ainda sem commit e depende de configuracao correta de ambiente, quota da Google Books e biblioteca nativa ZBar.
