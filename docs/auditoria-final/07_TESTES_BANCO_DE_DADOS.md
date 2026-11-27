# 07 — Testes de banco de dados

## Resultado

**BLOQUEADO:** nenhum Supabase/PostgreSQL de teste foi configurado ou acessado
durante esta auditoria. Nenhuma consulta de produção, escrita, exclusão, migração
ou operação destrutiva foi realizada.

## Evidência estática

- DDL e políticas estão em `database.sql`.
- O cliente Python está em `backend/utils/supabase_client.py`.
- O gate de API em `backend/app.py` executa uma consulta a `livros` para a maioria
  das chamadas de negócio.
- Testes unitários substituem cliente/queries em alguns cenários; isso não testa
  roles, permissões, constraints ou RLS reais.

## Não confirmado

Conexão remota; esquema efetivamente implantado; versão do schema; consistência
entre tabela e script; grants; comportamento de anon/authenticated/service role;
políticas RLS reais; transações/concorrência; dados reais; backups e restore.

Não usar o script `database.sql` como teste: ele inclui `DROP ... CASCADE` e não
foi executado.
