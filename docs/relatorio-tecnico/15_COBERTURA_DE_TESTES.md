# 15 — Cobertura de testes

Não há relatório de cobertura mensurado nesta auditoria.

- Percentual de linhas: **não medido**.
- Percentual de funções: **não medido**.
- Percentual de branches: **não medido**.
- `pytest-cov`/coverage não foi executado; não foi instalado tooling novo.
- Número de testes escritos não foi inferido do número de funções. Os resultados
  efetivamente executados foram 192 casos Python e 7 testes Node, detalhados em
  [13 — Resultados](13_RESULTADOS_DOS_TESTES.md).

Testes unitários não comprovam que todas as rotas, integrações, permissões ou
interfaces funcionam. Faltam cobertura real de banco/RLS, navegador, provedores
externos, operação concorrente e deploy.
