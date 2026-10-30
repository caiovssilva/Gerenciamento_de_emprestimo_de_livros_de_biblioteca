# 10 — Testes de desempenho e confiabilidade

**Não executados:** benchmark, carga, concorrência, consumo de CPU/memória,
latência de integração e indisponibilidade sob tráfego.

Os testes anteriores em `relatorio_atual_2026.md` documentam medições históricas
de endpoints; não foram repetidos, então não representam medida atual.

Limites técnicos vistos no código (análise, não medição):

- ISBN consulta provedores em paralelo e define timeout/retries.
- Empréstimo lê disponibilidade antes do INSERT sem transação explícita.
- O schema cria índice único parcial para livro/exemplar ativo; comportamento
  sob conflito não foi testado.
- O servidor de câmera usa thread e lock; não foi executado.

Recomendação: medir em ambiente de staging com banco isolado e carga limitada,
registrando versão, dados fictícios, concorrência, percentis e limites de
recursos. Não enviar carga a produção.
