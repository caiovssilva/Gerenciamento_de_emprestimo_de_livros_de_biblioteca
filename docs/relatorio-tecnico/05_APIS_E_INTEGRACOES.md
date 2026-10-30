# 05 — APIs e integrações

## API interna Flask

Prefixos de blueprint registrados em `backend/app.py`:

| Prefixo | Rotas principais observadas | Uso |
|---|---|---|
| `/api/auth` | login, self-service login/logout/history/books/loans/verify-return-card, config Supabase | Autenticação e sessão |
| `/api/controle` | `GET/PUT /autoatendimento` | Configuração do self-service |
| `/api/books` | list/get/create/update/delete, exemplars, `isbn-lookup`, `isbn-vision` | Catálogo e integração bibliográfica |
| `/api/students` | CRUD, `/import/csv`, `/<id>/access` | Alunos e acesso bibliotecário |
| `/api/loans` | list/get/create, `/<id>/renew`, `/<id>/return` | Empréstimos |
| `/api/reports` | summaries, monthly, data e exports CSV | Relatórios |
| `/api/rooms`, `/api/genres` | CRUD | Cadastros auxiliares |
| `/api/qr` | decode, generate, cards, login, start/stop/result/status | Scanner e carteirinhas |
| Raiz | `/api/health`, `/api/ready`, `/api/config/supabase` | Saúde/configuração |

`frontend/assets/js/api.js` contém o cliente consumidor. A lista completa de
decoradores de rota está nos módulos indicados; não foi exercitado individualmente
cada endpoint.

## Integrações externas realmente referenciadas

| Serviço | Como e onde | Autenticação/dados | Observação |
|---|---|---|---|
| Supabase/PostgREST | SDK Python em `utils/supabase_client.py`; tabelas e operações do sistema | `SUPABASE_URL`; chave preferida no backend `SUPABASE_SERVICE_KEY`, fallback `SUPABASE_KEY` | Consulta real não executada |
| Google Books API | `GET https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}` em `api/books.py` | API key opcional em query `key`; resposta de volume | Uma fonte de metadados |
| Google Books HTML | Página `books.google.com/books?vid=ISBN...`; parser HTML próprio | Sem chave no código | Scraping, formato não é contrato API |
| ISBNsearch | Página por ISBN e parser HTML próprio em `api/books.py` | Sem autenticação observada | Não há API oficial confirmada; sujeito a mudanças de página |
| Open Library | `/api/books?bibkeys=ISBN...` e `/search.json?isbn=...` | Não há chave no código | Política de uso/rate limits devem ser respeitados |
| ISBNdb | `GET https://api2.isbndb.com/book/{isbn}` | `Authorization: ISBNDB_API_KEY` | Opcional e condicionado a chave |
| Groq | SDK `openai` com `base_url=https://api.groq.com/openai/v1`; chat completions | `GROQ_API_KEY` ou aliases `API_GROQ`/`GROQ_API` | Consulta de metadados e visão |
| OpenAI | SDK `openai`, chat completions com imagem | `OPENAI_API_KEY` | Visão opcional; não chamado nesta auditoria |
| Render | Workflow agendado faz GET a `/api/health` | URL fixa no workflow; sem segredo | Evidência de ping, não prova de deploy ativo |
| GitHub Actions | Job agendado chama endpoint REST do Supabase | Secrets `SUPABASE_URL` e `SUPABASE_ANON_KEY` | Nenhum valor de Secret foi lido |

As requisições de ISBN usam `urllib`, timeout de seis segundos e até duas
tentativas; alguns erros HTTP/rede são repetidos. As consultas iniciais são
paralelas e há cache local em memória. Não há teste contra serviços de terceiros.

## Fluxos e limites

- Em modo `source=scanner`, Groq participa da sugestão; as fontes bibliográficas
  independentes continuam sendo a confirmação.
- ISBNdb entra apenas se `ISBNDB_API_KEY` estiver presente.
- Google Books API aceita key opcional no código.
- ISBNsearch e Google Books HTML são leitura de páginas, não APIs estáveis
  comprovadas.
- O front-end contém módulo legado para carregar config Supabase dinamicamente;
  os endpoints retornam a chave configurada e precisam ser tratados como
  exposição até remoção/segregação de chave pública. O cliente direto não foi
  confirmado como carregado.
- Nenhuma API de autenticação Supabase, RPC ou Edge Function foi identificada em
  uso.

## Referências consultadas

Links oficiais e resultado da consulta constam em [19 — Fontes e referências](19_FONTES_E_REFERENCIAS.md).
