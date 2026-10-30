# 12 — Plano e matriz de testes

Os cenários abaixo derivam de rotas e telas encontradas. PASSOU/FALHOU só se
aplicam a execuções documentadas em 13; caso contrário, NÃO EXECUTADO ou
BLOQUEADO.

| ID | Funcionalidade / cenário | Verificação e resultado esperado | Status nesta auditoria |
|---|---|---|---|
| T01 | Health sem banco | GET `/api/health` retorna 200/status ok | PASSOU (teste automatizado) |
| T02 | Readiness sem banco | GET `/api/ready` retorna 503 | PASSOU (mock) |
| T03 | Readiness com banco fake | GET `/api/ready` retorna 200 | PASSOU (mock) |
| T04 | Login válido/inválido | status, sessão e mensagem | PARCIAL: casos unitários existem; suite completa listada em 13 |
| T05 | Token self-service expirado/escopo inválido | rejeição 401 | PARCIAL: coberto por testes existentes; não testado contra banco real |
| T06 | CRUD de livro | resposta e geração de IDs/QR | FALHOU em caso listado; banco não disponível no gate |
| T07 | Busca ISBN checksum válido/inválido | 200/400, metadados ou erro | PARCIAL: unit tests; fontes reais bloqueadas |
| T08 | Visão Groq com imagem nos unit tests | Os testes devem configurar chave fictícia antes de chegar ao mock do SDK | FALHOU: quatro casos pararam com “Groq Vision não configurado”; a chave fictícia não foi definida |
| T09 | CRUD de aluno e CSV | validação, duplicatas e importação | PARCIAL: teste automatizado, operação real não executada |
| T10 | Concessão de bibliotecário | Requisição não autenticada deve ser negada | NÃO EXECUTADO como teste HTTP; análise estática identificou ausência de gate de papel, registrada separadamente |
| T11 | Empréstimo sem aluno/livro | erro 400 | PARCIAL: unit tests existentes |
| T12 | Empréstimo de exemplar ocupado | conflito 409 | PARCIAL: sem teste de concorrência real |
| T13 | Devolução/renovação por QR | validação e estado resultante | PARCIAL: testes unitários, sem DB real |
| T14 | Relatórios e export CSV | linhas sem duplicação, status e CSV | FALHOU nos três requests bloqueados por gate de DB |
| T15 | QR resolve aluno/livro por ID | tipo e registro esperados | FALHOU nos requests bloqueados por gate de DB |
| T16 | Salas e gêneros | CRUD e validação | NÃO EXECUTADO isoladamente nesta auditoria |
| T17 | Frontend API retry | retry HTTP 502/503/504 | PASSOU |
| T18 | Navegação, modais, CRUD simulado, scanner e relatórios JS | testes de comportamento Node, sem navegador visual | PASSOU nos 7 arquivos executados; não equivale a teste visual/E2E |
| T19 | RLS e permissões PostgreSQL | negar anon e permitir papel autorizado | BLOQUEADO: sem banco de teste |
| T20 | Fluxo navegador frontend+backend | página, câmera, sessão e persistência | BLOQUEADO: sem automação de navegador configurada |
| T21 | Integrações reais Google/OpenLibrary/Groq/OpenAI/ISBNdb | resposta e rate limits | BLOQUEADO: sem credenciais/validação remota autorizada |
| T22 | Segurança dinâmica e carga | CSRF, XSS, rate, concorrência isolada | NÃO EXECUTADO: exigiria ambiente isolado adequado |

## Abordagem

Foram usados os testes já presentes (`pytest` e `node --test`). A suíte Python foi
iniciada por harness que bloqueou somente a tentativa de carregar o caminho real
`backend/.env`; o teste de dotenv com arquivo temporário permaneceu funcional.
Não se instalaram ferramentas novas nem se alterou código de produção.
