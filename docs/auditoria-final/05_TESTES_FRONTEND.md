# 05 — Testes de frontend

## Runner executado

Comando: `node --test frontend/tests/*.test.js`

| Arquivo | Escopo sugerido pelo nome/comportamento do teste | Resultado |
|---|---|---|
| `api-retry.test.js` | Retry do cliente HTTP | PASSOU |
| `books-isbn.test.js` | Formulário de ISBN | PASSOU |
| `catalog-crud.test.js` | Atualização visual/local de livros e alunos | PASSOU |
| `modal-interaction.test.js` | Interações, foco, teclado e modais | PASSOU |
| `navigation.test.js` | Navegação/fluxos JS simulados | PASSOU |
| `qr-scanner.test.js` | Callback do scanner simulado | PASSOU |
| `reports.test.js` | Deduplicação/CSV no cliente | PASSOU |

Resumo do runner: 7 executados, 7 aprovados, 0 falhas, 0 ignorados; repetição
terminou em aproximadamente 1,22 s.

## Limites

São testes JavaScript em Node, alguns com DOM/fetch/câmera mockados. Não foi
iniciada automação de navegador, não houve inspeção visual e não foram conferidos
CDNs, permissões reais de câmera, responsividade, navegação assistiva ou
comunicação real com backend. “PASSOU” não significa que todas as telas foram
abertas num browser.
