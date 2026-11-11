# 08 — Testes de autenticação e autorização

## Resultado observado

A suíte Python completa passou por 180 casos e falhou em 12; os dois testes de
busca de carteirinha em `test_self_service_auth.py` foram reprovados com resposta
503. Os outros testes de autenticação não foram isolados no output, então não
afirmo aprovação individual além dos casos efetivamente identificados.

## Análise estática

- Login de staff consulta tabela `usuarios` e verifica senha via Passlib/bcrypt/
  `crypt`, com fallback de senha legada.
- Sessão usa `access_scope`; alguns caminhos de autoatendimento conferem token,
  validade, aluno e propriedade.
- `PUT /api/controle/autoatendimento` exige `staff_admin`.
- Não foi localizado gate universal de autenticação/RBAC em CRUD, exportações e
  operações QR.
- A rota de acesso de bibliotecário altera `is_librarian` sem checagem de admin
  visível no handler; QR desse aluno cria sessão `staff_librarian`.
- A rota pública de configuração Supabase pode selecionar key do ambiente e
  serializá-la ao cliente.

Essas são conclusões estáticas; não houve teste de invasão ou alteração de
conta.

## Não executado

Login válido/inválido isolado contra fixtures independentes; expiração temporal
em relógio controlado; reuso/forja de cookie; autorização negativa por papel;
logout e invalidação em navegador; rate limit; RLS. Não foram usadas contas reais.
