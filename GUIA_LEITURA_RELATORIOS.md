# Guia de Leitura dos Relatórios

## Resumo executivo

Este projeto é um sistema web de gerenciamento de biblioteca escolar. Ele organiza livros, exemplares, alunos, salas, gêneros, empréstimos, devoluções, renovações, relatórios e leitura de QR Code/códigos de barras.

A aplicação usa Python/Flask no backend, HTML/CSS/JavaScript no frontend e Supabase/PostgreSQL como caminho principal de persistência. Há código de fallback em arquivos JSON, mas o estado atual do servidor bloqueia APIs de negócio quando não consegue confirmar a conexão com o banco.

O projeto possui consulta bibliográfica por ISBN, com Google Books, ISBNsearch e Open Library. O ISBN não substitui o UUID interno do livro e não substitui o QR Code usado pelo sistema.

O estado atual é funcional para desenvolvimento e uso controlado, mas não deve ser descrito como pronto para produção. Ainda existem limitações de autorização server-side, segurança de chaves e credenciais, RLS permissivo, reconciliação offline/online, concorrência de exemplares e cobertura E2E.

O relatório-base desta análise é [`RELATORIO_ANALISE_COMPLETA_ESTADO_ATUAL.md`](RELATORIO_ANALISE_COMPLETA_ESTADO_ATUAL.md). Ele é a referência consolidada para responder perguntas sobre o projeto. Os demais documentos continuam úteis como explicação, tema específico ou histórico, mas não substituem a conferência do código atual.

## ORDEM RECOMENDADA PARA LER A DOCUMENTAÇÃO

1. [`RELATORIO_ANALISE_COMPLETA_ESTADO_ATUAL.md`](RELATORIO_ANALISE_COMPLETA_ESTADO_ATUAL.md): leia primeiro; é o relatório-base factual, com arquitetura, módulos, campos, endpoints, banco, segurança, testes, limitações e informações não confirmadas.
2. [`auditoria-documentacao.md`](auditoria-documentacao.md): consulte para classificar documentos atuais, históricos, desatualizados ou temáticos.
3. [`relatorio_atual_2026.md`](relatorio_atual_2026.md): visão técnica anterior/consolidada; use como apoio e confronte com o relatório-base e o código.
4. [`RELATORIO_ESTRUTURA_PASTAS.md`](RELATORIO_ESTRUTURA_PASTAS.md): localização dos módulos e responsabilidades das pastas; confira os caminhos contra a árvore atual.
5. [`RELATORIO_ESTUDO_PROJETO.md`](RELATORIO_ESTUDO_PROJETO.md): explicação geral para iniciantes, com a arquitetura e os principais arquivos.
6. [`RELATORIO_LOGICA_COMPLETA_SISTEMA.md`](RELATORIO_LOGICA_COMPLETA_SISTEMA.md): fluxos de login, acervo, empréstimos, scanner e relatórios.
7. [`RELATORIO_CONSULTA_ISBN.md`](RELATORIO_CONSULTA_ISBN.md): fluxo detalhado do ISBN, fontes externas, validação, fallback e formulário.
8. [`RELATORIO_SCANNER.md`](RELATORIO_SCANNER.md): leitura de câmera e diferença entre teste mock e câmera física.
9. [`MELHORIAS_EXEMPLARES_QR.md`](MELHORIAS_EXEMPLARES_QR.md): exemplares e QR Code; leia como documento temático/histórico.
10. [`relatorio-modificacoes.md`](relatorio-modificacoes.md): evolução e riscos; confira as marcações de histórico.
11. [`RELATORIO_STATUS_ATUAL.md`](RELATORIO_STATUS_ATUAL.md): resumo factual do estado atual, subordinado ao relatório-base.
12. [`TESTES_EXECUTADOS.md`](TESTES_EXECUTADOS.md): resultados de uma execução específica; não substitui uma nova execução.
13. [`RELATORIO_TCC_SISTEMA.md`](RELATORIO_TCC_SISTEMA.md): material acadêmico mais amplo, útil depois que a arquitetura estiver clara.
14. [`CURSO_LEITURA_DE_CODIGO.md`](CURSO_LEITURA_DE_CODIGO.md): material de estudo para conceitos de leitura de código.
15. [`COMO_USAR.md`](COMO_USAR.md) e [`backend/README.md`](backend/README.md): instruções de uso e execução, conferindo os comandos com o ambiente instalado.
16. [`RELATORIO_COMPARATIVO_COMPLETO_GIT.md`](RELATORIO_COMPARATIVO_COMPLETO_GIT.md) e [`RELATORIO_3_COMPARATIVO_GIT.md`](RELATORIO_3_COMPARATIVO_GIT.md): evolução histórica pelo Git.
17. Os demais relatórios numerados, pitch, execução inicial, otimizações e resumo final: consulte como histórico, conforme a classificação da auditoria.

## Mapa da documentação

| Ordem | Documento | Objetivo | Nível | Pré-requisito |
|---:|---|---|---|---|
| 1 | `RELATORIO_ANALISE_COMPLETA_ESTADO_ATUAL.md` | Fonte factual consolidada do estado atual | Básico/intermediário | Nenhum |
| 2 | `auditoria-documentacao.md` | Classificação documental e conflitos | Básico | Ordem 1 |
| 3 | `relatorio_atual_2026.md` | Estado técnico anterior/consolidado | Intermediário | Ordens 1-2 |
| 4 | `RELATORIO_ESTRUTURA_PASTAS.md` | Onde cada parte está | Básico | Ordens 1-2 |
| 5 | `RELATORIO_ESTUDO_PROJETO.md` | Arquitetura explicada | Básico | Ordens 1-4 |
| 6 | `RELATORIO_LOGICA_COMPLETA_SISTEMA.md` | Fluxos de negócio | Intermediário | Ordem 5 |
| 7 | `RELATORIO_CONSULTA_ISBN.md` | Consulta bibliográfica e fontes | Intermediário | Ordens 1 e 5 |
| 8 | `RELATORIO_SCANNER.md` | Câmera, QR e código de barras | Intermediário | Ordens 5 e 7 |
| 9 | `MELHORIAS_EXEMPLARES_QR.md` | Identificação de exemplares | Intermediário | Ordens 6 e 8 |
| 10 | `relatorio-modificacoes.md` | Mudanças e riscos | Intermediário | Ordem 1 |
| 11 | `RELATORIO_STATUS_ATUAL.md` | Resumo atual | Básico | Ordens 1-3 |
| 12 | `TESTES_EXECUTADOS.md` | Execuções registradas | Intermediário | Ordem 1 |
| 13 | `RELATORIO_TCC_SISTEMA.md` | Visão acadêmica ampla | Avançado | Ordens 1 e 6-9 |
| 14 | `CURSO_LEITURA_DE_CODIGO.md` | Método de estudo | Básico | Nenhum |
| 15 | `COMO_USAR.md` | Uso da aplicação | Básico | Ordem 1 |
| 16 | `backend/README.md` | Execução do backend | Básico | Ordem 1 |
| 17 | `RELATORIO_COMPARATIVO_COMPLETO_GIT.md` | Evolução histórica | Avançado | Ordem 1 |

Os documentos restantes estão no inventário de [`auditoria-documentacao.md`](auditoria-documentacao.md). Eles devem ser lidos como históricos ou temáticos quando essa classificação estiver indicada.

## COMO LER O CÓDIGO DESTE PROJETO

### 1. Comece pela entrada do servidor

Abra [`backend/app.py`](backend/app.py). Procure:

- `Flask(__name__)`, que cria a aplicação;
- `register_blueprint`, que conecta grupos de rotas;
- `@app.route`, que define endpoints diretamente no arquivo;
- `before_request`, que executa uma verificação antes das APIs de negócio;
- `serve_frontend`, que entrega o `index.html`.

### 2. Descubra a rota

Para localizar uma função HTTP, procure `@...route`. Por exemplo, `backend/api/books.py` possui `@books_bp.route("/isbn-lookup", methods=["GET"])`. Como `app.py` registra esse blueprint com `/api/books`, a URL final é `/api/books/isbn-lookup`.

### 3. Siga uma chamada do frontend

Para o ISBN, a ordem é:

```text
frontend/index.html
  -> lookupBookIsbn() em pages/books.js
  -> API.books.lookupIsbn() em api.js
  -> GET /api/books/isbn-lookup?isbn=...
  -> lookup_isbn() em backend/api/books.py
  -> _lookup_isbn()
  -> provedores externos
  -> jsonify(...)
  -> preenchimento do formulário
```

### 4. Descubra de onde vêm os dados

Em `books.py`, procure `get_client()`, `sb_exec()` e `read_json()`. Eles mostram se o módulo tenta Supabase ou lê arquivo JSON. Em `database.sql`, procure `CREATE TABLE` para confirmar tabelas, campos e relações.

### 5. Descubra para onde os dados vão

No cadastro de livros, `saveBook()` monta o payload e chama `API.books.create()` ou `API.books.update()`. No backend, `create_book()` monta o registro, gera o ID com `new_id()` e persiste o livro.

### 6. Leia uma função por entrada, processamento e saída

Para cada função, pergunte:

1. Qual parâmetro entra?
2. Qual transformação acontece?
3. Qual valor retorna?
4. Quem chama a função?
5. Qual função é chamada depois?

### 7. Consulte os testes sem tratá-los como prova total

Os testes mostram regras que foram escolhidas para verificação, mas não comprovam todos os fluxos reais. Não há confirmação de cobertura E2E completa, câmera física, segurança por requisição ou execução de produção.

## Fluxos principais

### Consulta de ISBN

```text
usuário digita ou lê ISBN
  -> normalização no frontend
  -> API interna Flask
  -> validação ISBN no backend
  -> Google Books
  -> ISBNsearch, se necessário
  -> Open Library, se necessário
  -> combinação de dados
  -> gênero local, quando há correspondência
  -> JSON
  -> título/autor/ISBN/área/gênero no formulário
```

### Cadastro de livro

```text
formulário
  -> saveBook()
  -> POST /api/books/
  -> create_book()
  -> new_id() e exemplares
  -> Supabase ou caminho JSON do módulo
  -> QR com ID interno
```

### Empréstimo

```text
lookupBook() consulta Store local
  -> lookupStudent() ou scanner
  -> confirmLoan()
  -> POST /api/loans/
  -> create_loan()
  -> verifica livro, aluno e exemplar
  -> grava empréstimo
```

### QR Code

```text
câmera do navegador
  -> jsQR/BarcodeDetector
  -> texto do QR
  -> resolução local ou API /api/qr/decode
  -> livro, exemplar, aluno ou admin
```

O QR não muda o ISBN em ID principal. Livros usam o UUID interno; exemplares usam um código derivado do livro e do exemplar.

## Como interpretar autenticação e testes

O frontend grava um cookie JavaScript para controlar atividade e expiração visual, mas esse cookie não é `HttpOnly`, não é validado pelo backend e não protege as chamadas posteriores às APIs. A ocultação de telas conforme o papel também é apenas frontend; não deve ser descrita como autorização server-side.

Os testes existentes comprovam somente cenários específicos. Na execução registrada no relatório-base, 13 testes Python passaram e 9 falharam; os 2 testes JavaScript executados passaram. Esses resultados não comprovam produção, integração real com Supabase, câmera física ou cobertura E2E completa.

Para qualquer informação não comprovada pelo código atual, pelo SQL ou por um teste reproduzível, use exatamente:

> Não foi possível confirmar esta informação no estado atual do projeto.

## Glossário

| Termo | Significado simples | Onde aparece | Por que importa |
|---|---|---|---|
| API | Interface para trocar dados entre programas | `api.js`, blueprints Flask | Liga frontend e backend |
| Endpoint | URL que executa uma operação | `/api/books/isbn-lookup` | É o endereço de uma função HTTP |
| ISBN | Número bibliográfico da publicação | campo `livros.isbn`, consulta externa | Ajuda a identificar e pesquisar a obra |
| UUID | Identificador textual gerado para um registro | `new_id()`, coluna `id` | É o ID interno do sistema |
| JSON | Formato de dados estruturados | respostas HTTP e arquivos `data/*.json` | Transporta e armazena registros |
| HTTP | Protocolo de comunicação web | `GET`, `POST`, status 200/404/502 | Define como cliente e servidor conversam |
| GET | Requisição normalmente usada para consultar | `GET /api/books/isbn-lookup` | Consulta sem enviar um corpo JSON |
| POST | Requisição usada para criar ou executar ação | criação de livro/empréstimo/login | Envia dados no corpo da requisição |
| Fallback | Caminho alternativo quando o primeiro falha | provedores ISBN e caminhos JSON | Evita depender de uma única fonte |
| Timeout | Limite de espera por uma resposta | consultas externas de ISBN | Evita espera sem fim |
| Retry | Nova tentativa controlada | `_open_provider()` | Ajuda em falhas temporárias |
| Cache | Resultado guardado temporariamente | `_ISBN_CACHE` | Evita repetir consultas válidas |
| Parser | Código que interpreta uma resposta | `_IsbnSearchParser` | Extrai dados do HTML do ISBNsearch |
| Frontend | Parte executada no navegador | `frontend/` | Mostra telas e coleta ações |
| Backend | Parte executada no servidor | `backend/` | Aplica regras e acessa dados |
| Flask | Framework Python para servidor web | `backend/app.py` | Registra rotas e serve a aplicação |
| Função | Bloco nomeado de código | `lookupBookIsbn`, `_lookup_isbn` | Organiza uma responsabilidade |
| Parâmetro | Dado recebido por uma função | `isbn` | Permite reutilizar a função |
| Retorno | Valor produzido por uma função | `return jsonify(...)` | Leva o resultado ao próximo ponto |
| Exceção | Sinal de erro ou situação especial | `try/except`, `LookupError` | Controla falhas sem continuar cegamente |
| API key | Chave de acesso a um serviço | `GOOGLE_BOOKS_API_KEY` | Deve permanecer no backend/ambiente |
| Supabase | Serviço usado para acessar o banco | `supabase_client.py` | É o caminho principal de persistência |
| PostgreSQL | Banco relacional usado pelo Supabase | `database.sql` | Define tabelas, FKs e índices |
| QR Code | Código visual que carrega texto | scanner e geração de cartões | Encaminha IDs internos e códigos de exemplar |

## Lembrete para o estudante

Quando uma documentação antiga disser que algo está “pronto”, confira a função e a rota atuais. A documentação deste repositório registra evolução, e nem todo relatório antigo representa o estado de 2026-09-14.
