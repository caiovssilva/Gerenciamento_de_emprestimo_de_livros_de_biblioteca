# Guia para entender o backend

Este guia explica como a pasta `backend/` está organizada e como uma requisição
percorre o sistema. A ideia é ajudar você a ler o código e descobrir onde uma
regra está implementada, não substituir a leitura dos arquivos.

## 1. Visão geral

O backend é um servidor Flask. Ele serve a interface web, recebe chamadas da
API, conversa principalmente com o Supabase e devolve respostas HTTP:

```text
Navegador
   │  GET /api/books/
   ▼
backend/app.py
   │  verificações globais e encaminhamento da rota
   ▼
backend/api/books.py
   │  consulta dados
   ▼
Supabase
   │  resultado
   ▼
Resposta JSON para o navegador
```

O ponto de entrada é [`app.py`](./app.py). O arquivo
[`api/__init__.py`](./api/__init__.py) contém apenas uma docstring: ele marca a
pasta `api` como um pacote Python. Não inicia o servidor nem registra rotas.

## 2. Mapa das pastas e arquivos

| Caminho | Responsabilidade |
|---|---|
| [`app.py`](./app.py) | Cria a aplicação Flask, carrega ambiente, registra rotas, aplica verificações globais e serve o frontend. |
| [`api/`](./api/) | Rotas e regras da API, separadas por assunto. |
| [`api/_helpers.py`](./api/_helpers.py) | Funções comuns para JSON local e verificações de tabelas/colunas. |
| [`utils/supabase_client.py`](./utils/supabase_client.py) | Cria e reutiliza a conexão com Supabase e executa consultas. |
| [`utils/helpers.py`](./utils/helpers.py) | Geração de IDs, cálculos de datas e status de empréstimos. |
| [`scanner/routes.py`](./scanner/routes.py) | Leitura e resolução de QR Codes e geração de cartões. |
| [`sync_hub.py`](./sync_hub.py) | Distribui eventos em tempo real dentro do processo Python. |
| [`data/`](./data/) | Arquivos JSON locais de dados e configurações. |
| [`tests/`](./tests/) | Testes automatizados do backend. |
| [`requirements.txt`](./requirements.txt) | Dependências Python do projeto. |
| [`.env.example`](./.env.example) | Modelo de variáveis de ambiente; não deve conter segredos reais. |

## 3. Como o servidor começa

Ao iniciar, `app.py` carrega as variáveis de `backend/.env`, importa os
blueprints e os registra com seus prefixos. Um blueprint é um grupo de rotas:

| Blueprint | Prefixo | Arquivo |
|---|---|---|
| Autenticação | `/api/auth` | [`api/auth.py`](./api/auth.py) |
| Controle | `/api/controle` | [`api/controle.py`](./api/controle.py) |
| Livros | `/api/books` | [`api/books.py`](./api/books.py) |
| Alunos | `/api/students` | [`api/students.py`](./api/students.py) |
| Empréstimos | `/api/loans` | [`api/loans.py`](./api/loans.py) |
| Relatórios | `/api/reports` | [`api/reports.py`](./api/reports.py) |
| Salas | `/api/rooms` | [`api/rooms.py`](./api/rooms.py) |
| Gêneros | `/api/genres` | [`api/genres.py`](./api/genres.py) |
| QR Codes | `/api/qr` | [`scanner/routes.py`](./scanner/routes.py) |

Por exemplo, a rota que lista livros tem método `GET` e endereço `/` dentro do
blueprint `books`. Com o prefixo `/api/books`, o endereço completo é
`GET /api/books/`.

## 4. A vida de uma requisição

Ao investigar uma chamada, siga esta ordem:

1. **Método e endereço:** procure `@...route(...)` no módulo responsável.
2. **Entrada:** veja se os dados vêm da URL (`request.args`), do corpo JSON
   (`request.get_json`) ou de um arquivo (`request.files`).
3. **Regras:** confira validações, permissões e condições de erro.
4. **Persistência:** procure `get_client()` e `sb_exec()` para chamadas ao
   Supabase.
5. **Resposta:** procure `jsonify(...)`, `Response(...)` e o status HTTP.

Antes da função da rota, o Flask também executa funções globais
`before_request`. No projeto, [`restrict_self_service_api`](./app.py) aplica
regras para sessões de Autoatendimento e algumas operações de bibliotecários.
[`require_database_for_api`](./app.py) verifica a conexão com o banco na
maioria das rotas de API. Depois da resposta, `after_request` pode publicar um
evento de alteração.

### Exemplo: listar livros

1. O frontend chama `GET /api/books/`.
2. Flask encontra `list_books()` em [`api/books.py`](./api/books.py).
3. A função lê filtros como `q` e `genre`.
4. Consulta a tabela `livros` pelo cliente Supabase.
5. Completa informações de gênero e retorna a lista com `jsonify`.

### Exemplo: criar um empréstimo

1. O frontend envia `POST /api/loans/` com os dados do livro e do aluno.
2. As verificações globais avaliam o escopo da sessão e a conexão ao banco.
3. [`api/loans.py`](./api/loans.py) verifica aluno, livro e exemplar disponível.
4. O backend calcula o prazo e grava o novo empréstimo.
5. Uma criação bem-sucedida responde com status `201`.
6. O servidor pode publicar um evento para atualizar outras telas.

## 5. O que cada módulo da API faz

### Autenticação — `api/auth.py`

Cuida do login de equipe, do Autoatendimento e de operações associadas ao
aluno autenticado, como consulta do histórico. O login de equipe define um
escopo de sessão; o Autoatendimento também associa a sessão a um aluno. Leia
este módulo junto com as verificações globais de `app.py`.

### Livros — `api/books.py`

Cuida do catálogo, de exemplares e da busca de ISBN. A busca pode consultar
serviços externos; a leitura de ISBN por imagem pode usar provedores de visão.
As chaves desses serviços devem ficar no ambiente do backend, nunca no
JavaScript do navegador.

### Alunos — `api/students.py`

Cuida do cadastro de alunos, da associação com salas, da importação CSV e da
marcação de alunos que podem entrar como bibliotecários.

### Empréstimos — `api/loans.py`

Cuida de criar, listar, devolver e renovar empréstimos. Também calcula a
disponibilidade de exemplares e valida códigos QR relacionados ao exemplar.
É um dos melhores módulos para estudar depois de entender um CRUD simples.

### Salas e gêneros — `api/rooms.py` e `api/genres.py`

São cadastros auxiliares com operações de listar, criar, atualizar e remover.
São bons exemplos para aprender o formato comum das rotas.

### Relatórios — `api/reports.py`

Busca livros, alunos e empréstimos para calcular totais, rankings e dados por
turma. Também monta relatórios mensais e respostas CSV.

### Controle — `api/controle.py`

Lê e grava as opções do Autoatendimento em
[`data/self_service_settings.json`](./data/self_service_settings.json).
`enabled` liga o Autoatendimento; `allow_borrow`, `allow_return` e
`allow_renew` controlam ações. `renewal_days` define o prazo em dias.

**Atenção à diferença:** as verificações do Autoatendimento exigem que
`enabled` esteja ligado e, quando aplicável, que a operação esteja permitida.
A verificação usada para bibliotecários consulta a permissão individual
`allow_*`; ela não usa `enabled` como interruptor geral.

## 6. Banco de dados, cliente e JSON local

[`utils/supabase_client.py`](./utils/supabase_client.py) contém `get_client()`,
que lê as variáveis `SUPABASE_URL` e `SUPABASE_SERVICE_KEY` (ou `SUPABASE_KEY`)
e reutiliza o cliente enquanto o processo está ativo. `sb_exec()` executa uma
consulta e devolve os dados. Falhas de conexão são tratadas como
indisponibilidade do Supabase.

[`utils/helpers.py`](./utils/helpers.py) reúne funções sem responsabilidade
por rotas: criar IDs, obter a data atual, somar dias e classificar empréstimos
como ativos, atrasados ou devolvidos.

[`api/_helpers.py`](./api/_helpers.py) contém leitura e gravação JSON, além de
verificações de tabelas e da coluna `deleted_at`.

Há rotas com caminhos de fallback para arquivos em `data/`, mas isso **não
significa que o sistema inteiro funcione offline**. O middleware de
`app.py` exige banco para a maioria das APIs de negócio antes de chamar a rota.
Consulte também a seção “Dependência do banco” do
[README do backend](./README.md).

## 7. QR Codes e eventos

[`scanner/routes.py`](./scanner/routes.py) concentra endpoints de QR. A
decodificação pode usar Pillow, OpenCV, NumPy e `pyzbar`; a resolução do código
procura relacionar o valor lido a um livro, exemplar, aluno ou cartão
administrativo. O módulo também gera QR Codes e imagens de carteirinhas.

[`sync_hub.py`](./sync_hub.py) mantém assinantes e filas em memória e alimenta
o endpoint `/api/events` com eventos enviados pelo próprio servidor. Não é um
banco nem um serviço de mensagens externo: seu estado pertence ao processo
Python em execução.

## 8. Sessões e permissões: o cuidado mais importante

**Login e autorização são coisas diferentes.** O login identifica um perfil;
cada operação ainda precisa verificar se aquele perfil pode executá-la.

O middleware global restringe sessões de Autoatendimento e algumas operações
de bibliotecário, mas isso não significa que todas as rotas CRUD tenham uma
verificação administrativa universal. Ao estudar uma rota, confira o próprio
handler e os `before_request` em `app.py`. Uma opção escondida na tela do
frontend não substitui a checagem no servidor.

## 9. Como entender os testes

Os testes ficam em [`tests/`](./tests/). Os nomes indicam o comportamento que
cada grupo exercita:

- `test_auth_librarian_login.py` e `test_self_service_auth.py`: login e limites
  dos perfis.
- `test_loans_return_qr.py`: criação, devolução, renovação e QR de exemplares.
- `test_exemplar_management.py`: manutenção de exemplares.
- `test_isbn_lookup.py`: ISBN, provedores e leitura por visão.
- `test_reports_data.py` e `test_reports_student_status.py`: relatórios.
- `test_supabase_reconnect.py` e `test_health_endpoints.py`: conexão e saúde.

Muitos testes substituem o Supabase por objetos falsos (*mocks*) para testar
as regras sem alterar o banco real. Por isso, passar nos testes não equivale a
testar todas as rotas contra uma instância real do Supabase.

Na raiz do repositório, rode:

```bash
python -m pytest backend/tests
```

## 10. Ordem de leitura recomendada

1. [`app.py`](./app.py): entrada, registro de rotas e verificações globais.
2. [`utils/helpers.py`](./utils/helpers.py): IDs, datas e status.
3. [`utils/supabase_client.py`](./utils/supabase_client.py): conexão e
   execução de consultas.
4. [`api/_helpers.py`](./api/_helpers.py): ferramentas compartilhadas.
5. [`api/genres.py`](./api/genres.py): CRUD pequeno para praticar.
6. [`api/students.py`](./api/students.py) e [`api/books.py`](./api/books.py):
   cadastros mais completos.
7. [`api/loans.py`](./api/loans.py) e [`api/auth.py`](./api/auth.py):
   fluxos centrais e sessões.
8. [`api/reports.py`](./api/reports.py), [`api/controle.py`](./api/controle.py)
   e [`scanner/routes.py`](./scanner/routes.py): recursos especializados.
9. Os testes correspondentes: compare cada regra com o caso que a verifica.

## 11. Glossário rápido

- **Endpoint/rota:** combinação de método HTTP e URL atendida pelo Flask.
- **Blueprint:** conjunto de rotas que recebe um prefixo comum.
- **Payload/body:** dados enviados no corpo da requisição, normalmente JSON.
- **`request.args`:** parâmetros que vêm na URL, como `?q=harry`.
- **`jsonify`:** transforma objetos Python numa resposta JSON.
- **Sessão:** dados associados ao usuário entre requisições.
- **Fallback:** caminho alternativo quando uma operação principal falha.
- **Mock:** objeto falso usado para testar sem chamar um serviço real.

Quando ficar perdido, escolha uma rota e siga o caminho completo:
**URL → função → validação → banco → resposta → teste**. Isso transforma a
pasta inteira em fluxos menores que dá para entender um por vez.
