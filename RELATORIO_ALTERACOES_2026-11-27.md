# Relatório das alterações — 27/11/2026

Este relatório resume as alterações e verificações realizadas no projeto em 27 de novembro de 2026.

## 1. Leitura de QR Code

- Reduzido o intervalo de captura de quadros de 700 ms para 300 ms.
- Priorizado o `BarcodeDetector` nativo do navegador; a cópia de pixels para o JavaScript ocorre somente no fallback.
- A leitura começa sem aguardar a enumeração das câmeras.
- Adicionado um viewfinder com moldura central, cantos, área externa escurecida e linha animada, respeitando `prefers-reduced-motion`.

Arquivos: [qr-scanner.js](frontend/assets/js/qr-scanner.js), [main.css](frontend/assets/css/main.css), [qr-scanner.test.js](frontend/tests/qr-scanner.test.js).

## 2. Uso exclusivo do banco para dados da biblioteca

- Impedido o uso de dados antigos do navegador para livros, alunos, empréstimos, salas e gêneros.
- Bloqueados fallbacks para arquivos JSON locais durante requisições da API quando o Supabase falha.
- Após falha de sincronização, os dados correspondentes em memória são limpos, em vez de permanecerem aparentando estar atualizados.
- Geração de cartões de livros e carteirinhas de alunos passou a consultar os registros e relações no Supabase.
- Atualizados os testes relacionados a fallback e relatórios.

Arquivos principais: [store.js](frontend/assets/js/store.js), [app.js](frontend/assets/js/app.js), [_helpers.py](backend/api/_helpers.py), [books.py](backend/api/books.py), [students.py](backend/api/students.py), [routes.py](backend/scanner/routes.py), [test_books_fallback.py](backend/tests/test_books_fallback.py), [test_reports_data.py](backend/tests/test_reports_data.py), [database-only-store.test.js](frontend/tests/database-only-store.test.js).

## 3. Retentativas para falhas transitórias

- No cliente frontend, leituras `GET`/`HEAD` podem tentar novamente até duas vezes após `503` ou erro de rede, com esperas curtas.
- Erros de gateway `502`, `503` e `504` também podem ser repetidos nos fluxos que habilitam essa opção.
- No cliente Supabase, leituras `GET`/`HEAD` são repetidas após desconexões transitórias.
- Incluídos na detecção os erros observados nos logs: conexão HTTP/2 fechada (`ConnectionInputs.RECV_DATA` / `ConnectionState.CLOSED`) e `Resource temporarily unavailable`.
- Gravações não são repetidas automaticamente, para evitar operações duplicadas.

Arquivos: [api.js](frontend/assets/js/api.js), [supabase_client.py](backend/utils/supabase_client.py), [api-retry.test.js](frontend/tests/api-retry.test.js), [test_supabase_reconnect.py](backend/tests/test_supabase_reconnect.py).

## 4. Documentação

- Criado um guia sobre a arquitetura do backend, fluxo de requisições, rotas, banco e testes.
- Atualizados os READMEs para referenciar o guia e explicar a dependência do banco.

Arquivos: [GUIA_ENTENDENDO_BACKEND.md](backend/GUIA_ENTENDENDO_BACKEND.md), [README.md](README.md), [README.md](backend/README.md).

## 5. Configuração alterada

Em [self_service_settings.json](backend/data/self_service_settings.json), a opção `enabled` mudou de `true` para `false`. Isso desativa o Autoatendimento nessa configuração; deve ser reativado caso o recurso deva ficar disponível.

## 6. Diagnóstico e verificações

- Os logs do Flask mostraram falhas transitórias nas consultas ao Supabase antes de alguns `503`; o serviço voltou a responder depois.
- Após as correções, `/api/ready`, `/api/loans/` e `/api/students/` responderam `200` no backend local.
- Foram feitas 100 rodadas concorrentes das rotas de empréstimos e alunos: 200 consultas no total, todas com resposta `200` e nenhuma falha.
  - Empréstimos: média de 0,66 s; máximo de 1,51 s.
  - Alunos: média de 0,83 s; máximo de 1,66 s.
- Os testes direcionados de reconexão, saúde e prevenção de fallback passaram: 13 aprovados na última execução. Testes focados anteriores de scanner, fallback e reconexão também passaram.
- A suíte completa do backend não foi executada como parte dessas verificações.
- O aviso `Unsafe attempt` foi identificado como um problema de autenticação do túnel do Codespaces dentro de um frame. A recomendação é abrir a porta 5000 em uma nova aba, mantendo-a privada.
- As verificações foram feitas no backend local do Codespaces; não foi feito deploy manual no Render.

## 7. Commits de hoje

- `fc269ec` — guia de arquitetura do backend e atualização do README.
- `440d206` — proteção contra uso de dados locais quando o Supabase está indisponível e atualizações relacionadas ao scanner/viewfinder.
- `0f0a3c0` — retentativas no cliente da API e testes.
- `a9e8e73` — cobertura de retentativa para conexão HTTP/2 fechada e recurso temporariamente indisponível.
