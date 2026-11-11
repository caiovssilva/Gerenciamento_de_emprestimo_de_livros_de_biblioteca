# 04 — Testes funcionais

## O que foi realmente executado

As suítes automatizadas preexistentes foram executadas, não uma sequência manual
por todas as telas. Consulte [13_EVIDENCIAS.md](13_EVIDENCIAS.md) para comandos,
status e saídas.

| Área | Cenário automatizado observado | Status |
|---|---|---|
| Health/readiness | Liveness e readiness com cliente de banco fake online/offline | PASSOU |
| ISBN / Groq Vision | Quatro casos unitários chamaram a função, mas falharam antes do cliente por chave não configurada | FALHOU |
| QR por ID | Dois requests de resolução/decode receberam 503 no gate do banco | FALHOU |
| Relatórios/exportações | Três requests receberam 503 em vez de resposta esperada | FALHOU |
| Autoatendimento por carteirinha | Dois casos receberam 503 | FALHOU |
| Criação de livro | Um caso recebeu 503 | FALHOU |
| Frontend | Testes Node automatizados em sete arquivos | PASSOU |

Esses status classificam os testes executados, não a implementação em produção.
Os oito requests com 503 não alcançaram a lógica principal esperada. Os quatro
testes Groq não realizaram chamada ao provedor nem chegaram ao mock SDK.

## Não executados / bloqueados

- Cenário normal, entradas inválidas, vazias, tipos inesperados e duplicatas para
  todo CRUD (livros, alunos, salas, gêneros).
- Sequências reais de empréstimo → renovação → devolução.
- Fluxo em navegador, estados de loading, câmera física e persistência após reload.
- Integrações reais e resposta a limites de API.
- Escrita/consistência no banco.
- Testes exploratórios de cada rota e método incorreto.

Motivo: ausência de banco isolado/provedor autorizado nesta execução e restrição
de não usar dados reais. Não se inventou uma quantidade de cenários planejados
como se fossem testes efetuados.
