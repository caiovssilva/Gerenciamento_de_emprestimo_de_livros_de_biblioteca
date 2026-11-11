# 03 — Auditoria dos relatórios anteriores

## Critério

Conferência da estrutura e de afirmações representativas contra código,
configuração e saída de testes disponível. Classificações:

- **VALIDADO:** afirmação delimitada, conferida e sustentada.
- **PARCIALMENTE VALIDADO:** parte foi conferida; partes históricas, ampla
  cobertura ou integração não foram verificadas.
- **INCORRETO:** há afirmação apresentada como estado atual contradita pelo
  código/artefato observado.
- **NÃO VALIDÁVEL:** requer histórico, execução ou ambiente que não está
  disponível nesta verificação.

Não foi editado nenhum relatório antigo. Esta tabela registra divergências sem
reescrever silenciosamente documentos que preservam snapshots.

## Relatórios da auditoria anterior (`docs/relatorio-tecnico/`)

| Documento | Afirmações verificadas | Problemas/limites encontrados | Classificação |
|---|---|---|---|
| `00_INDICE_GERAL.md` | Links e nomes dos 21 documentos | Links relativos existem; não valida conteúdo de cada link | VALIDADO |
| `01_INVENTARIO_DO_PROJETO.md` | Componentes listados contra árvore e registro de scripts/blueprints | Seleciona arquivos principais; não é inventário arquivo-a-arquivo completo | PARCIALMENTE VALIDADO |
| `02_ARQUITETURA_DO_SISTEMA.md` | Flask, frontend, Supabase SDK, JSON, middleware e rotas | Diagrama representa integração estática, não operação real; claims externos não testados | PARCIALMENTE VALIDADO |
| `03_LOGICA_DE_PROGRAMACAO.md` | Login, empréstimo, ISBN, cache e cliente | Resumo técnico; não percorre toda função nem testa efeitos | PARCIALMENTE VALIDADO |
| `04_FLUXOS_DO_SISTEMA.md` | Sequências login/emprestimo/QR/relatórios | Fluxos projetados a partir do código, não E2E; alinhamento de cache/token foi corrigido sem alterar o doc antigo | PARCIALMENTE VALIDADO |
| `05_APIS_E_INTEGRACOES.md` | Nomes de blueprints, provedores e endpoints principais | Chama lista de “principais”; não valida cada endpoint/HTTP remoto | PARCIALMENTE VALIDADO |
| `06_BIBLIOTECAS_E_TECNOLOGIAS.md` | Manifests, usos/imports e URLs CDN | Ambiente versionado não fixa todos os transitivos; pesquisa não valida CVEs | PARCIALMENTE VALIDADO |
| `07_BANCO_DE_DADOS.md` | DDL, tabelas, relações, policies/views | Confere script local, não o schema remoto | PARCIALMENTE VALIDADO |
| `08_CONFIGURACAO_E_DEPLOY.md` | Comandos em README, workflow Render e env path | Nenhum deploy foi executado; exemplo na raiz não é carregado pelo app | PARCIALMENTE VALIDADO |
| `09_VARIAVEIS_DE_AMBIENTE.md` | Referências ao código/workflows | `.env` protegido e não lido; exemplos não provam runtime | PARCIALMENTE VALIDADO |
| `10_RELATORIO_DE_FALHAS.md` | Evidências estáticas de segurança, SQL, HTML e fluxo | “Impacto” é análise, não teste exploratório; gravidade não é resultado de exploit | PARCIALMENTE VALIDADO |
| `11_AUDITORIA_DE_SEGURANCA.md` | Achados estáticos prioritários | Sem teste dinâmico; riscos qualificados no texto | PARCIALMENTE VALIDADO |
| `12_PLANO_E_MATRIZ_DE_TESTES.md` | Status dos cenários versus saídas pytest/Node | T08 não tinha chave fictícia apesar de rótulo anterior; T10 confundia risco com teste falho; T18 podia sugerir teste visual. Corrigido no documento. | INCORRETO antes da correção; agora PARCIALMENTE VALIDADO |
| `13_RESULTADOS_DOS_TESTES.md` | Contagens e nomes dos 12 casos falhos | Reexecução repetiu números; causas de falhas de rota são inferidas pelo middleware, não confirmadas após isolamento | PARCIALMENTE VALIDADO |
| `14_EVIDENCIAS_DOS_TESTES.md` | Comandos e saídas do runner | Ajustado para registrar duas execuções e não sugerir status de Git pós-teste sem checagem atual | PARCIALMENTE VALIDADO |
| `15_COBERTURA_DE_TESTES.md` | Ausência de cobertura calculada | Coverage não executado; percentuais não declarados | PARCIALMENTE VALIDADO |
| `16_RESULTADO_GERAL_DA_VALIDACAO.md` | Resumo alinhado às execuções | Parcial por não validar produção, rotas ou cada função | PARCIALMENTE VALIDADO |
| `17_MANUAL_DE_APRENDIZAGEM.md` | Chamadas e arquivos centrais | Material educativo seletivo, não documentação exaustiva | PARCIALMENTE VALIDADO |
| `18_GLOSSARIO_TECNICO.md` | Termos comparados a código/configuração | Glossário simplificado, não contrato técnico completo | PARCIALMENTE VALIDADO |
| `19_FONTES_E_REFERENCIAS.md` | URLs consultadas e falha 403 ISBNdb | Página online pode evoluir; ISBNdb não foi verificado por documentação | PARCIALMENTE VALIDADO |
| `RELATORIO_COMPLETO.md` | Números e riscos principais | Sumário, não auditoria independente; repete limitações anteriores | PARCIALMENTE VALIDADO |

## Relatórios e guias históricos na raiz

| Documento | Afirmações verificadas | Problemas encontrados / limite | Classificação |
|---|---|---|---|
| `ANALISE_PROBLEMAS.md` | Afirmações sobre frontend, auth, env e validators | Apresenta como atuais arquivos/códigos que a auditoria anterior marcou como ausentes ou alterados; contém alegações históricas não reproduzidas | PARCIALMENTE VALIDADO |
| `Atualmente_02-10.md` | Registro datado de testes e recursos | `68 passed`/cinco testes JS é snapshot de 17/10, não reproduzido agora; execução atual é 180/12 e sete Node | PARCIALMENTE VALIDADO |
| `auditoria-documentacao.md` | Inventário, riscos e referências históricas | A contagem de documentos da raiz está datada e não corresponde ao inventário atual; alguns detalhes de estado precisam nova prova | PARCIALMENTE VALIDADO |
| `calma.md` | Assunto de ISBN/scanner | Conteúdo por versão; integração externa não foi chamada agora | PARCIALMENTE VALIDADO |
| `chat-gpt.md` | Reconhecimento de arquitetura e limites do modo offline | Relatório declara explicitamente revisão estática; conteúdo integral não foi repetidamente executado | PARCIALMENTE VALIDADO |
| `claude.md` | Tabela de riscos e recomendações | Parte dos achados está no código; severidade/impacto não foram testados dinamicamente | PARCIALMENTE VALIDADO |
| `COMO_USAR.md` | Instruções de execução, endpoints e credenciais | Afirmações de offline/login não devem ser usadas como evidência atual; conteúdo é guia histórico | PARCIALMENTE VALIDADO |
| `CURSO_LEITURA_DE_CODIGO.md` | Explicações pedagógicas | Exemplos podem refletir snapshot anterior; não conferido linha a linha | PARCIALMENTE VALIDADO |
| `GUIA_LEITURA_RELATORIOS.md` | Guia de interpretação do conjunto documental | Inventário e prioridade documental podem estar desatualizados | PARCIALMENTE VALIDADO |
| `MELHORIAS_EXEMPLARES_QR.md` | QR/exemplares e propostas | Parte descritiva é compatível com módulos atuais; implantação de todas propostas não foi provada | PARCIALMENTE VALIDADO |
| `RELATORIO_1_IMPLEMENTACAO.md` | Registra alterações e testes históricos | É snapshot de mudanças; não prova execução no estado atual | NÃO VALIDÁVEL como histórico; PARCIALMENTE VALIDADO contra código atual |
| `RELATORIO_2_MELHORIAS_E_RISCOS.md` | Pontos positivos e recomendações | “Operacional”/“produção intermediária” não são métricas de teste | NÃO VALIDÁVEL |
| `RELATORIO_3_COMPARATIVO_GIT.md` | Compara estado anterior e posterior | Requer revisão do commit-base/escopo do comparativo não feita nesta etapa | NÃO VALIDÁVEL |
| `RELATORIO_ANALISE_COMPLETA_ESTADO_ATUAL.md` | Resumo técnico amplo e problemas | Contém referências históricas a caminhos/recursos; não foi possível validar todas as afirmações em 724 linhas | PARCIALMENTE VALIDADO |
| `RELATORIO_COMPARATIVO_COMPLETO_GIT.md` | Histórico de mudanças entre revisões | Comparação temporal não reexecutada nesta auditoria | NÃO VALIDÁVEL |
| `RELATORIO_COMPLETO.md` | Registra mudanças antigas | Identifica-se como histórico; não descreve o estado atual | PARCIALMENTE VALIDADO |
| `RELATORIO_CONSULTA_ISBN.md` | Fluxo ISBN, provedores e cache | Algumas seções refletem snapshots distintos; consulta real não foi executada. `source` controla Groq conforme código, portanto não generalizar Groq para modo manual | PARCIALMENTE VALIDADO |
| `RELATORIO_ESTRUTURA_PASTAS.md` | Lista de diretórios e módulos | Afirmações de ausência sobre arquivos podem ter ficado obsoletas; código/histórico não permite validar a data de cada afirmação | PARCIALMENTE VALIDADO |
| `RELATORIO_ESTUDO_PROJETO.md` | Arquitetura e sequência didática | Parte geral compatível; modos offline e uso do cliente devem seguir código atual | PARCIALMENTE VALIDADO |
| `RELATORIO_EXECUCAO_INICIAL_09092026.md` | Saída de execução inicial | Não há log externo reproduzido nesta etapa; é registro histórico | NÃO VALIDÁVEL |
| `RELATORIO_LOGICA_COMPLETA_SISTEMA.md` | Fluxos e regras gerais | Não verificado cada função; pode descrever código de snapshot | PARCIALMENTE VALIDADO |
| `RELATORIO_PITCH_PROJETO.md` | Apresentação e avaliação | Alegações promocionais não são prova operacional | NÃO VALIDÁVEL |
| `RELATORIO_SCANNER.md` | Foco/câmera e teste simulado | Documento distingue mock de câmera física; teste atual Node passou, mas hardware não foi exercitado | PARCIALMENTE VALIDADO |
| `RELATORIO_STATUS_ATUAL.md` | Status e resumo do projeto | Atualização 22/09 é histórica; declarações amplas de funcionamento não reproduzidas | PARCIALMENTE VALIDADO |
| `RELATORIO_TCC_SISTEMA.md` | Material acadêmico de sistema | Documento extenso; não validado linha a linha ou academicamente nesta etapa | PARCIALMENTE VALIDADO |
| `RESUMO_FINAL.txt` | Alega correções completas e módulos de validação | “100% resolvidos” é contradito por achados de segurança atuais; cita arquivos não encontrados na árvore inspecionada | INCORRETO como estado atual |
| `TESTES_EXECUTADOS.md` | Registros históricos de HTTP/serviço | Os resultados 6/6 e respostas exemplificadas não foram reproduzidos; `/api/health` atual retorna `status: ok`, não mede banco. Não usar como evidência atual | INCORRETO como estado atual; histórico NÃO VALIDÁVEL |
| `relatorio-estudo.md` | Manual/estudo da aplicação | Conteúdo de snapshot e abrangência não revalidada função a função | PARCIALMENTE VALIDADO |
| `relatorio-explicacao-logica.md` | Explicação do fluxo e lógica | Seletivo; operações reais não repetidas | PARCIALMENTE VALIDADO |
| `relatorio-modificacoes.md` | Histórico e estado técnico | Afirmações sobre mudanças e execuções dependem de histórico não conferido integralmente | PARCIALMENTE VALIDADO |
| `relatorio_atual_2026.md` | Atualização de 17/10 e snapshots anteriores | O snapshot tem 68 testes backend/5 frontend; não é o resultado atual. O endpoint `health` citado com campo de DB não corresponde à implementação atualmente vista | PARCIALMENTE VALIDADO |
| `relatorio_otimizacoes.md` | Otimizações e medições anteriores | Medições históricas não reproduzidas; não inferir performance atual | NÃO VALIDÁVEL |
| `TCC_valibe.md` | Guia extenso de aprendizagem | 2.628 linhas; não houve validação frase a frase nem de todas as referências/fontes | PARCIALMENTE VALIDADO |
| `backend/README.md` | Execução, arquitetura e deploy recomendado | Comandos e variáveis estão documentados, mas não houve deploy; login/seed e comportamento de conexão exigem cuidado diante do SQL e middleware atual | PARCIALMENTE VALIDADO |

`requirements.txt` não é relatório e foi conferido como manifesto; não recebe
classificação documental. `ANDAMENTO_AUDITORIA.md` é registro de execução
anterior e foi conferido apenas contra as ferramentas/testes reexecutados nesta
etapa; classificação PARCIALMENTE VALIDADO.

## Correções documentais feitas nesta segunda etapa

1. A matriz T10 foi alterada de “FALHOU/risco estático” para “NÃO EXECUTADO”; o
   risco de autorização fica como achado separado.
2. T08 agora informa que a variável de chave fictícia não foi definida; não
   caracteriza a situação como chamada a provedor.
3. T18 foi explicitamente limitado a testes Node simulados, não teste visual.
4. Os relatórios de execução/evidência foram atualizados com a repetição das
   suítes e a ressalva de que a causa das falhas HTTP é inferida pelo gate, não
   confirmada por reexecução dos cenários isolados.

Os documentos antigos foram preservados sem edição.
