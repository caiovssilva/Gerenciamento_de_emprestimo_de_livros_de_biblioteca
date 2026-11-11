# 17 — Manual de aprendizagem

## 1. Comece pela inicialização

Abra `backend/app.py`: ele instancia `Flask`, registra blueprints e aplica
middleware. Um blueprint agrupa rotas por domínio; por exemplo, `books_bp` recebe
prefixo `/api/books`. A página estática é entregue pelo mesmo processo.

## 2. Entenda uma chamada HTTP

No navegador, `API.books.list()` em `frontend/assets/js/api.js` chama `apiFetch`,
que constrói a URL, executa `fetch`, interpreta JSON e lança erro para status não
2xx. O endpoint Flask lê parâmetros/body, consulta banco e responde com
`jsonify`.

## 3. Entenda as camadas

```text
HTML/CSS/JS -> fetch -> Flask route -> helpers/client -> Supabase
                                      \-> JSON local em alguns fallbacks
```

O frontend é uma SPA sem framework identificado: `app.js` cuida da navegação e
estado de sessão; `Store` mantém arrays; `pages/*.js` desenha as telas e usa a
API. O backend separa rotas por blueprint. `supabase_client.py` centraliza acesso
à persistência.

## 4. Operação de empréstimo, do início ao fim

1. Operador escolhe aluno e exemplar na tela.
2. A página chama `API.loans.create(body)`.
3. `apiFetch` manda `POST /api/loans/`.
4. `loans.create_loan()` chama `_create_loan_record`.
5. O backend consulta livro, empréstimos ativos e aluno.
6. `_available_copies_from_rows` calcula códigos que não estão ativos.
7. A rota cria datas e payload, insere em `emprestimos` e retorna 201.
8. `app.js`/página atualiza Store e interface.

Esse caminho não é transacional entre leitura e inserção. O índice parcial SQL
protege unicidade de exemplar ativo, mas conflito precisa ser tratado pelo
endpoint.

## 5. Operação de ISBN

O frontend envia ISBN a `/api/books/isbn-lookup`. O backend valida dígito
verificador, consulta várias fontes com `ThreadPoolExecutor`, combina resultados
e aplica cache. A resposta preenche o formulário; só depois o operador envia o
cadastro do livro. Uma falha de provedor não é equivalente a ausência de livro.

## 6. Dados e datas

O schema SQL define UUIDs e FKs; datas de empréstimo/vencimento são `DATE`. O
frontend mantém cópias de listas em `localStorage`, mas o banco é a persistência
principal. Os JSON em `backend/data/` participam de fallbacks e de configuração
local; middleware pode bloquear chamadas sem banco antes do fallback.

## 7. Condições, loops e exceções

- Condições `if` aplicam validações e ramificam erros.
- Loops constroem listas filtradas e agregados.
- `try/except` pode transformar indisponibilidade em fallback, resposta HTTP ou
  log.
- Erro desconhecido chega ao handler de 500 em `app.py`.

Ao ler cada bloco, pergunte: qual entrada chega aqui, qual dado é confiável, qual
consulta é feita e qual resposta sai? Existem `except` amplos que podem ocultar
falhas de schema; isso merece atenção ao depurar.

## 8. Segurança e qualidade

Autenticação identifica usuário; autorização decide ação permitida. A interface
esconder um botão não protege endpoint. Um cookie de sessão Flask é assinado;
um token assinado é verificável, mas não substitui controle de papel no servidor.
Teste mockado demonstra lógica isolada, não conexão ou RLS reais.

## Acompanhando uma operação do início ao fim

Para estudar, percorra em sequência:

- Empréstimo: `frontend/assets/js/pages/students.js` ou `loans.js` →
  `frontend/assets/js/api.js` → `backend/api/loans.py` →
  `backend/utils/supabase_client.py` → tabela `emprestimos`.
- ISBN: `frontend/assets/js/pages/books.js` → `api.js` →
  `backend/api/books.py` → provedor externo → preenchimento do formulário.
- Autoatendimento: `frontend/assets/js/app.js` → `backend/api/auth.py` →
  `backend/api/controle.py` e `backend/api/loans.py`.
- QR: `frontend/assets/js/qr-scanner.js` → `backend/scanner/routes.py` →
  resolução de IDs ou exemplares.

Comece pelas funções chamadas diretamente pela rota; depois siga helper por
helper. Para confirmar efeitos reais, use ambiente de teste isolado e mocks
explícitos, nunca produção.
