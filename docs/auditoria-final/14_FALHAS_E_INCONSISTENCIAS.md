# 14 — Falhas e inconsistências

## Falhas observadas nos testes

1. Quatro testes de ISBN Vision falham antes do mock porque não definem uma
   variável de chave fictícia.
2. Oito testes de rota recebem HTTP 503; middleware verifica Supabase antes de
   chegar à rota. Os resultados de negócio permanecem não testados nesses casos.
3. A suíte reprovou em ambas as execuções com a mesma lista de 12 testes.

Esses são resultados dos testes. Não foram usados como prova de defeito em
serviços reais.

## Inconsistências na documentação anterior

- A matriz anterior misturava “risco estático” com status `FALHOU` no caso de
  concessão de bibliotecário. Corrigido para `NÃO EXECUTADO` e risco separado.
- Um caso de Groq era descrito como se a chave fictícia tivesse sido definida;
  os testes não a definem. A descrição foi corrigida.
- Testes Node eram por vezes sumarizados com linguagem que poderia sugerir
  inspeção visual; não houve browser/E2E.
- Alguns relatórios antigos afirmam que todos os problemas de segurança foram
  resolvidos ou descrevem os endpoints como plenamente operacionais. Isso
  contradiz arquivos atuais e não é sustentado pelas execuções desta etapa.
- Relatórios antigos registram contagens diferentes de testes e APIs; são
  snapshots datados, não resultados atuais reproduzidos.
- `auditoria-documentacao.md` contém contagem de documentos da raiz relativa a
  uma data antiga; o inventário atual é maior.
- `RELATORIO_ESTRUTURA_PASTAS.md` e `RESUMO_FINAL.txt` citam arquivos ou estados
  não confirmados na árvore atual; não devem ser tratados como fonte de verdade.

## Limitações de prova

Não se conferiu linha por linha os documentos históricos extensos; a tabela em
03 declara classificação parcial/não validável. Nenhuma correção foi feita nos
documentos históricos.
