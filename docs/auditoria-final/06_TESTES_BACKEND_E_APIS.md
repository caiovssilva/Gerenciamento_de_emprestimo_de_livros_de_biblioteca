# 06 — Testes de backend e APIs

## Inventário estático de rotas

Prefixos de blueprint registrados em `backend/app.py`; rotas observadas por
decoradores:

| Prefixo | Métodos/caminhos reconhecidos no código |
|---|---|
| Raiz Flask | `GET /api/config/supabase`, `GET /api/supabase-config`, `GET /api/health`, `GET /api/ready`, `GET /`, `GET /<path>`, `GET /favicon.ico` |
| `/api/auth` | `POST /login`, `POST /self-service/login`, `POST /self-service/logout`, `POST /self-service/verify-return-card`, `GET /self-service/history`, `GET /self-service/books`, `POST /self-service/loans`, `POST /self-service/loans/<id>/renew`, `POST /self-service/loans/<id>/return`, `GET /config/supabase`, `GET /supabase-config` |
| `/api/books` | `GET/POST /`, `GET /isbn-lookup`, `POST /isbn-vision`, `GET/PUT/DELETE /<id>`, `DELETE /<id>/exemplars/<code>` |
| `/api/students` | `GET/POST /`, `GET/PUT/DELETE /<id>`, `PATCH/POST /<id>/access`, `POST /import/csv` |
| `/api/loans` | `GET/POST /`, `GET /<id>`, `POST /<id>/renew`, `POST /<id>/return` |
| `/api/reports` | `GET /chart-summary`, `/top-books`, `/by-class`, `/monthly`, `/data`; `POST /monthly/generate`; GET `/export/overdue`, `/all`, `/books`, `/by-class`, `/student-status`, `/students` |
| `/api/rooms` | `GET/POST /`, `GET/PUT/DELETE /<id>` |
| `/api/genres` | `GET/POST /`, `PUT/DELETE /<id>` |
| `/api/controle` | `GET/PUT /autoatendimento` |
| `/api/qr` | `POST /start`, `/stop`, `/decode`, `/login`, `/card/admin/<login>`, `/generate`; `GET /result`, `/status`, `/card/book/<id>`, `/card/student/<id>` |

Há rotas compatíveis/aliases e catch-all frontend; esta é enumeração estática,
não `url_map` capturado em runtime.

## Evidência automatizada

No conjunto Python (192 casos), 180 passaram e 12 falharam. Oito testes de rotas
receberam 503; os quatro demais eram casos Groq sem chave fictícia configurada.
Os 180 restantes passaram, mas a saída resumida não identifica individualmente
cada caso aprovado.

## Não testado

Não houve chamada HTTP a servidor em execução nesta segunda etapa, nem ensaio
exaustivo de método/headers/body/status por endpoint. Os testes usam Flask
test-client e mocks; não provam integração Supabase. Inspeção estática encontrou
validações específicas, mas não schema geral de entrada em todas as rotas.
