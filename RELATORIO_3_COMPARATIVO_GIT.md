# Relatório 3 — Comparativo com o estado anterior do Git

## 1. Comparação geral
Em relação ao estado anterior do repositório, o projeto passou por uma mudança significativa na forma como empréstimos, exemplares e QR são tratados.

## 2. Diferenças principais

### Antes
- O fluxo de QR era mais simples e muitas vezes identificado apenas pelo ID geral do livro ou do aluno.
- A devolução não tinha um controle forte para impedir que outro aluno devolvesse um exemplar que estava com outra pessoa.
- O sistema não possuía um relatório específico para status de alunos por empréstimo.
- A identidade visual da biblioteca estava parcialmente inconsistente.

### Depois
- O sistema passou a gerar QR e identificadores únicos por registro e por exemplar.
- O fluxo de devolução ficou travado para o aluno responsável.
- O painel agora mostra claramente o nome do aluno responsável por um exemplar emprestado.
- O relatório de status de alunos foi adicionado.
- A marca da biblioteca foi padronizada na tela principal e nos cartões gerados.

## 3. Impacto técnico
- O modelo de negócio ficou mais consistente porque o exemplar passou a ser tratado como item individual.
- O backend ficou mais preparado para rastrear operações com menos ambiguidade.
- O frontend passou a responder melhor ao fluxo de QR do mundo real.

## 4. Diferença de segurança e usabilidade
- Segurança operacional: melhorada.
- Clareza para o usuário: melhorada.
- Risco de erro por identificação duplicada: reduzido.
- Facilidade de auditoria: aumentada, embora ainda necessite de refinamento.

## 5. Conclusão do comparativo
O estado atual do projeto está bem mais robusto que o anterior, especialmente em relação a QR, identidade do exemplar, devolução e relatórios. Ainda há espaço para evolução, mas o ganho funcional foi claro e direto.
