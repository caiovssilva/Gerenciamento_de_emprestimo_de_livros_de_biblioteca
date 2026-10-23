# Auditoria da Documentação do Projeto

**Data da auditoria:** 2026-09-14  
**Escopo:** documentação do repositório, código atual, SQL, configurações declaradas e testes existentes.  
**Regra de leitura:** o código atual tem prioridade sobre relatórios antigos.

## 1. Resultado executivo

O projeto é uma aplicação Flask que serve um frontend HTML/CSS/JavaScript e APIs para autenticação, livros, alunos, salas, gêneros, empréstimos, relatórios e QR Code. O acesso principal aos dados é feito por Supabase; há caminhos de arquivo JSON em vários módulos, mas o `backend/app.py` bloqueia APIs de negócio quando não consegue confirmar a conexão com a tabela `livros`.

Foram encontrados **27 documentos de projeto na raiz**, **1 README de apoio em `backend/`**, **2 arquivos de dependências** (`requirements.txt` e `backend/requirements.txt`) e **nenhum PDF** no repositório. Os arquivos de dependências foram inventariados separadamente porque descrevem o ambiente, mas não são relatórios. Desses 27 documentos da raiz, 25 já existiam antes desta auditoria e 2 foram criados agora.

A documentação contém materiais de épocas diferentes. O relatório mais confiável para o estado do sistema é [`relatorio_atual_2026.md`](relatorio_atual_2026.md), complementado por este documento e pelo [`GUIA_LEITURA_RELATORIOS.md`](GUIA_LEITURA_RELATORIOS.md).

## 2. Funcionalidades confirmadas no código

- Flask serve o frontend e registra blueprints para `/api/auth`, `/api/books`, `/api/students`, `/api/loans`, `/api/reports`, `/api/rooms`, `/api/genres` e `/api/qr`.
- O frontend usa JavaScript sem framework, com `api.js`, `store.js`, `app.js`, páginas por recurso e `qr-scanner.js`.
- Livros possuem UUID interno, ISBN opcional, exemplares e QR Code derivado do ID interno ou do exemplar.
- O cadastro de livro consulta o Groq primeiro e Google Books, ISBNsearch e Open Library em paralelo para confirmação e complementação.
- A consulta de ISBN atualmente normaliza e valida ISBN-10/ISBN-13, usa retry limitado, combina dados, preserva dados parciais do Groq e armazena somente resultados completos no cache com TTL e limite de tamanho.
- O scanner de navegador usa `getUserMedia`, `jsQR` e `BarcodeDetector`; `/api/qr/decode` é um caminho de decodificação de imagem no backend.
- O backend possui login por credenciais e resolução de QR, mas não foi encontrada sessão server-side, cookie seguro, token ou middleware de autorização nas rotas de negócio.
- O SQL define tabelas, índices, FKs, JSONB, views e políticas RLS. As políticas observadas usam `USING (true)`/`WITH CHECK (true)` para várias tabelas.
- Existem testes Python e um teste Node do scanner; não existe uma suíte E2E completa confirmada.

## 3. Limitações confirmadas

- O login devolve uma classificação de acesso para o frontend, mas as rotas de negócio não verificam sessão, token ou papel.
- O endpoint de configuração Supabase seleciona `SUPABASE_SERVICE_KEY` como fallback de chave; isso precisa ser tratado como risco de segurança, não como proteção garantida.
- O fallback em JSON não possui reconciliação bidirecional confirmada.
- O scanner real de câmera não possui teste físico automatizado.
- O ISBN depende de serviços externos. ISBNsearch é HTML, não uma API JSON estruturada confirmada no projeto.
- A disponibilidade de uma API externa pode variar por ISBN, rede, timeout, HTTP 404/429 ou limite do serviço.
- A aplicação não deve ser descrita como “production-ready” apenas com base nos relatórios antigos.

## 4. Inventário documental

Classificação: **Atual** = pode servir como referência após conferir código; **Histórico** = registra uma versão ou análise anterior; **Temático** = útil para um assunto, mas não é fonte geral; **Desatualizado** = contém afirmações atuais contrariadas pelo código; **Apoio** = README/dependência, não relatório.

| Arquivo | Assunto principal | Classificação | Verificação necessária |
|---|---|---|---|
| `ANALISE_PROBLEMAS.md` | Problemas e propostas de segurança | Histórico/desatualizado em alguns pontos | Separar propostas de funcionalidades existentes |
| `COMO_USAR.md` | Guia de uso e endpoints | Histórico | Conferir modo offline, rotas e telas |
| `CURSO_LEITURA_DE_CODIGO.md` | Material introdutório | Temático | Usar exemplos do código atual |
| `MELHORIAS_EXEMPLARES_QR.md` | Exemplares e QR único | Temático | Confirmar formatos atuais de QR |
| `RELATORIO_1_IMPLEMENTACAO.md` | Implementações de uma etapa anterior | Histórico | Não usar como estado atual |
| `RELATORIO_2_MELHORIAS_E_RISCOS.md` | Melhorias e riscos | Histórico | Comparar riscos com código atual |
| `RELATORIO_3_COMPARATIVO_GIT.md` | Comparação com Git | Histórico | Confirmar branch/commits se necessário |
| `RELATORIO_COMPARATIVO_COMPLETO_GIT.md` | Evolução pelo histórico Git | Histórico | Válido para evolução, não para comportamento atual |
| `RELATORIO_COMPLETO.md` | Mudanças gerais | Histórico | Conferir afirmações de conclusão |
| `RELATORIO_CONSULTA_ISBN.md` | Fluxo de ISBN | Temático, atualizado nesta auditoria | Corrigir validação/cache/fallback conforme código atual |
| `RELATORIO_ESTRUTURA_PASTAS.md` | Estrutura de pastas | Temático/histórico | Remover referências a arquivos inexistentes |
| `RELATORIO_ESTUDO_PROJETO.md` | Estudo geral | Temático, precisa atualização | Explicar bloqueio real de API e limites do fallback |
| `RELATORIO_EXECUCAO_INICIAL_09092026.md` | Execução inicial | Histórico | Resultados valem somente para aquela execução |
| `RELATORIO_LOGICA_COMPLETA_SISTEMA.md` | Lógica geral | Temático | Atualizar ISBN, autenticação e persistência |
| `RELATORIO_PITCH_PROJETO.md` | Apresentação/pitch | Histórico/promocional | Não tratar alegações como prova técnica |
| `RELATORIO_SCANNER.md` | Scanner | Temático | Distinguir teste mock de câmera real |
| `RELATORIO_STATUS_ATUAL.md` | Estado e pitch | Desatualizado | Atualizar modo offline, sessão e segurança |
| `RELATORIO_TCC_SISTEMA.md` | Explicação acadêmica | Temático/histórico | Manter contexto, marcar limites atuais |
| `RESUMO_FINAL.txt` | Resumo de conclusão | Desatualizado | Afirma funcionalidades/arquivos não confirmados |
| `TESTES_EXECUTADOS.md` | Resultados de testes | Histórico de execução | Reexecutar antes de tratar como atual |
| `relatorio-estudo.md` | Estudo didático | Temático/histórico | Atualizar dependências e status de autorização |
| `relatorio-explicacao-logica.md` | Explicação de lógica | Temático | Conferir fluxos atuais |
| `relatorio-modificacoes.md` | Mudanças e riscos | Desatualizado em ISBN/sessão | Atualizar alterações realmente presentes |
| `relatorio_atual_2026.md` | Auditoria técnica geral | Atual, com ajustes de data | É a referência geral principal |
| `relatorio_otimizacoes.md` | Otimizações | Histórico/temático | Confirmar quais otimizações permanecem |
| `backend/README.md` | Execução e funcionamento do backend | Apoio/histórico | Conferir comandos e modo offline |
| `requirements.txt` | Dependências gerais | Apoio/configuração | Não é relatório; comparar com ambiente |
| `backend/requirements.txt` | Dependências do backend | Apoio/configuração | Fonte declarativa de pacotes Python |

## 5. Conflitos importantes encontrados

| Informação em documentação anterior | Código atual | Classificação |
|---|---|---|
| ISBN validado apenas por tamanho | `backend/api/books.py` possui `_validate_isbn()` com checksum ISBN-10/ISBN-13 | Desatualizado |
| Não há cache/retry para ISBN | Há `_ISBN_CACHE`, TTL de 15 minutos, máximo de 128 itens e duas tentativas por provedor | Desatualizado |
| A consulta usa somente Google Books | `_lookup_isbn()` usa Google Books, ISBNsearch e Open Library | Desatualizado |
| Sessão/cookie protege o usuário | `currentUser` fica no frontend; não há autenticação por requisição nas APIs | Desatualizado |
| Modo offline é garantido pelo servidor | O código possui fallback local em módulos, mas `before_request` bloqueia APIs de negócio sem Supabase | Desatualizado/depende do caminho |
| Projeto “production-ready” | Há riscos confirmados de autorização, RLS permissivo, chaves e credenciais padrão | Desatualizado |
| Existe `backend/api/validators.py` | Arquivo não foi encontrado na estrutura atual | Não confirmado; tratado como inexistente no estado atual |
| O scanner sempre usa o backend | O caminho normal tenta decodificação no navegador; `/api/qr/decode` é fallback separado | Desatualizado |

## 6. Arquivos atualizados nesta auditoria

Foram modificados **25 documentos existentes**. Todos receberam pelo menos uma atualização de status, ressalva histórica ou correção factual. Os ajustes de conteúdo mais extensos ocorreram em:

- `RELATORIO_CONSULTA_ISBN.md`: validação atual, retry, cache e códigos de erro.
- `relatorio_atual_2026.md`: referência geral do estado atual.
- `RELATORIO_STATUS_ATUAL.md`: separação entre controle visual e autorização server-side.
- `relatorio-modificacoes.md`: correção de afirmações antigas sobre sessão, ISBN e cache.
- `RELATORIO_ESTUDO_PROJETO.md` e `relatorio-estudo.md`: atualização didática de Supabase, bloqueio de API, ISBN e fallback.
- `RESUMO_FINAL.txt`: reclassificação de arquivos e resultados não confirmados.
- `RELATORIO_LOGICA_COMPLETA_SISTEMA.md`, `RELATORIO_ESTRUTURA_PASTAS.md`, `ANALISE_PROBLEMAS.md`, `TESTES_EXECUTADOS.md` e `RELATORIO_SCANNER.md`: correções de estrutura, ISBN e status de testes.
- Os demais relatórios temáticos, históricos, de pitch, Git, TCC, curso e README receberam avisos explícitos para não serem interpretados como fonte única do estado atual.

O histórico não foi apagado. Quando um documento antigo descreve uma versão anterior, isso agora é indicado no próprio documento ou no inventário.

## 7. Documentos novos

- `auditoria-documentacao.md`: este relatório, com inventário, conflitos e fonte de verdade.
- `GUIA_LEITURA_RELATORIOS.md`: ordem didática para estudar a documentação e o código.

## 8. Partes do sistema analisadas

Foram conferidos: inicialização Flask, blueprints, autenticação, cliente Supabase, helpers JSON, livros/ISBN, alunos, salas, gêneros, empréstimos, devoluções, renovações, relatórios, scanner, frontend, Store, HTML, SQL, dependências e testes.

## 9. Verificação executada nesta auditoria

- Links relativos em `auditoria-documentacao.md` e `GUIA_LEITURA_RELATORIOS.md`: nenhum link ausente encontrado.
- `node --test frontend/tests/qr-scanner.test.js`: **passou**, 1 teste aprovado.
- `PYTHONPATH=backend .venv312/bin/python -m pytest -q backend/tests`: **13 passaram e 9 falharam**.
- As falhas Python não foram corrigidas porque o escopo solicitado era documentação. Elas indicam divergências entre testes e código/ambiente atual, incluindo expectativas antigas sobre `_offline`, fallback local de login, `backend/.env` obrigatório, `books.LookupError` e a ordem de validação da rota.

## 10. Não foi possível confirmar

- Deploy em produção e existência de um processo Gunicorn ativo.
- Execução de câmera física e reconhecimento em dispositivos reais.
- Funcionamento de políticas RLS em um projeto Supabase externo apenas lendo o SQL.
- Cobertura E2E completa do frontend.
- Reconciliação automática entre JSON e Supabase.
- Qualquer arquivo PDF no repositório: nenhum foi encontrado.

## 11. Regra para leituras futuras

Quando um relatório antigo e o código discordarem, use o código atual. Quando uma execução ou API externa não puder ser repetida, escreva que ela não foi confirmada no estado atual, em vez de transformar um resultado histórico em garantia.
