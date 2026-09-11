# Relatório técnico de modificações e estado atual

**Projeto:** Gerenciamento de empréstimo de livros de biblioteca
**Data da análise:** 2026-09-05
**Branch analisada:** `fix/login-error-message`
**Escopo:** código, banco, documentação, testes, histórico Git e alterações locais presentes no workspace.

> Este documento descreve somente o que foi encontrado no repositório e o que foi comprovado durante a análise. Credenciais e valores do arquivo `backend/.env` não são reproduzidos.

## 1. Resumo executivo

O sistema é uma aplicação Flask que serve um frontend SPA em JavaScript vanilla. O backend possui blueprints para autenticação, livros, alunos, empréstimos, salas, gêneros, relatórios e QR Code. A persistência principal é Supabase/PostgreSQL, com fallback para arquivos JSON locais quando a conexão falha.

O núcleo funcional existe: login, navegação, cadastro e consulta de livros, cadastro de alunos, gêneros, salas, empréstimos, devoluções, renovações, relatórios, QR Codes e leitura por câmera estão implementados. O health check foi observado respondendo `HTTP 200` com o banco conectado, e a API de livros respondeu `HTTP 200` sem cookies de login.

O sistema **não está pronto para produção**. O maior risco é de segurança: o frontend controla a sessão e o papel do usuário, mas as APIs não possuem middleware de autenticação/autorização por requisição. O SQL também habilita RLS com políticas amplamente permissivas. Há ainda credenciais padrão, senha inicial em texto no SQL, possível exposição de chave privilegiada no endpoint de configuração e ausência de reconciliação entre Supabase e JSON offline.

**Estimativa de conclusão funcional:** aproximadamente **75%**, considerando que o fluxo básico está amplo, mas segurança de produção, testes E2E, sincronização offline/online, robustez das integrações e alguns ajustes de qualidade ainda estão pendentes. A estimativa é aproximada e não representa cobertura de testes.

## 2. Histórico das modificações

### 2.1 Autenticação e mensagens de login

**Status:** IMPLEMENTADO e funcionando em cenários locais testados; segurança de sessão ainda é PENDENTE.

- **Alteração:** o backend passou a buscar usuários no Supabase, aceitar fallback local e normalizar os aliases `bibliotecario` e `bibliotecaria` para `biblioteca`.
- **Local:** [backend/api/auth.py](backend/api/auth.py), testes em [backend/tests/test_auth_librarian_login.py](backend/tests/test_auth_librarian_login.py).
- **Necessidade anterior:** falhas de login, mensagens inconsistentes e variações do nome do usuário bibliotecário.
- **Solução:** busca exata e tolerante a maiúsculas/minúsculas, fallback local, verificação com `passlib`, `bcrypt` e `crypt`, além de mensagens HTTP de erro mais consistentes.
- **Impacto:** login de `admin`, `biblioteca` e alias de bibliotecário funciona no fluxo local testado.
- **Pendências:** ainda há aceitação de senha legada em texto puro; não há token, sessão assinada ou autorização no backend.

### 2.2 Dependências de senha

**Status:** IMPLEMENTADO; precisa de endurecimento de segurança.

- **Alteração:** inclusão de `passlib` e `bcrypt` nas dependências e suporte a múltiplos formatos de hash.
- **Local:** [backend/api/auth.py](backend/api/auth.py) e [backend/requirements.txt](backend/requirements.txt).
- **Impacto:** hashes bcrypt e formatos legados podem ser verificados; senhas legadas podem ser re-hashadas após login.
- **Pendência:** [database.sql](database.sql) ainda insere `narceu2026` em texto puro. A migração de todas as contas para hashes e a troca das credenciais padrão ainda precisam ser feitas.

### 2.3 Sessão e expiração por inatividade

**Status:** PARCIALMENTE FUNCIONANDO.

- **Alteração:** sessão visual no frontend com cookie, restauração de estado e expiração após 30 minutos sem atividade.
- **Local:** [frontend/assets/js/app.js](frontend/assets/js/app.js).
- **Necessidade anterior:** manter o usuário conectado e encerrar sessões ociosas.
- **Impacto:** a interface esconde o login após autenticação e executa logout por inatividade.
- **Pendência crítica:** o cookie é legível e editável pelo cliente, não é `HttpOnly`, não é assinado e não é validado nas rotas Flask. Portanto, isso é controle de interface, não autenticação confiável.

### 2.4 IDs próprios, exemplares e QR Codes

**Status:** IMPLEMENTADO; concorrência e migração de registros antigos precisam de testes adicionais.

- **Alteração:** criação de UUID próprio com `new_id()`, geração de IDs de exemplares e QR Codes derivados do identificador do sistema.
- **Local:** [backend/utils/helpers.py](backend/utils/helpers.py), [backend/api/books.py](backend/api/books.py), [backend/scanner/routes.py](backend/scanner/routes.py), [backend/api/loans.py](backend/api/loans.py).
- **Regra preservada:** o ISBN não substitui o ID principal. O payload do livro usa o UUID gerado pelo backend; o QR usa esse ID ou o identificador do exemplar.
- **Impacto:** exemplares do mesmo livro podem ser distinguidos e empréstimos registram `exemplar` e `exemplar_id`.
- **Pendências:** a seleção do exemplar ocorre antes da inserção e não está protegida por transação; duas requisições concorrentes ainda podem disputar o mesmo exemplar. Registros antigos sem `exemplares_meta` usam fallback de identificação.

### 2.5 Otimização de scanner e carteirinhas

**Status:** IMPLEMENTADO em código; cobertura de câmera real é limitada.

- **Alteração:** carregamento sob demanda de OpenCV/PyZbar, cache de fontes e ajustes na geração de cartões/QR.
- **Local:** [backend/scanner/routes.py](backend/scanner/routes.py) e [frontend/assets/js/app.js](frontend/assets/js/app.js).
- **Impacto:** menor custo de inicialização e geração de imagens mais eficiente.
- **Pendências:** dependências nativas, permissões de câmera, navegadores e dispositivos reais ainda precisam de matriz de testes.

### 2.6 Scanner de QR e código de barras

**Status:** PARCIALMENTE FUNCIONANDO, com teste automatizado do callback aprovado.

- **Alteração:** o scanner frontend usa `jsQR`, `BarcodeDetector` quando disponível e fallback para `/api/qr/decode`.
- **Local:** [frontend/assets/js/qr-scanner.js](frontend/assets/js/qr-scanner.js), [backend/scanner/routes.py](backend/scanner/routes.py), [frontend/tests/qr-scanner.test.js](frontend/tests/qr-scanner.test.js).
- **Aprimoramentos locais:** resolução ideal de câmera, foco contínuo quando suportado, ampliação, grayscale, threshold, contraste local e nitidez para imagens de baixa qualidade.
- **Impacto:** QR e EAN/ISBN podem ser processados pelo navegador ou por OpenCV/PyZbar.
- **Pendências:** não há teste automatizado com câmera física nem amostras reais de códigos desfocados. `HTTP 200` em `/api/qr/decode` confirma processamento da imagem, não necessariamente que um código foi reconhecido.

### 2.7 Cadastro automático de livros por ISBN

**Status:** IMPLEMENTADO LOCALMENTE, ainda PARCIAL por depender de serviço externo e estar em alterações não commitadas.

- **Alteração:** rota `GET /api/books/isbn-lookup`, cliente API, botão de leitura e pesquisa no modal de cadastro.
- **Local:** [backend/api/books.py](backend/api/books.py), [frontend/assets/js/api.js](frontend/assets/js/api.js), [frontend/assets/js/pages/books.js](frontend/assets/js/pages/books.js), [frontend/index.html](frontend/index.html).
- **Fluxo implementado:** ler código, normalizar ISBN, consultar Google Books, preencher ISBN/título/autor e tentar associar categorias a gêneros locais.
- **Regra preservada:** o cadastro continua chamando a rota existente de criação; `new_id()`, exemplares, QR e carteirinha não foram substituídos pelo ISBN.
- **Pendências:** Google Books respondeu `HTTP 429` durante a verificação; não há cache, quota própria, retry progressivo ou provedor alternativo. Também não há validação do dígito verificador do ISBN nem teste automatizado da API externa.

### 2.8 Tema, interface e acessibilidade

**Status:** IMPLEMENTADO em boa parte; precisa de revisão de produção.

- **Alteração:** tema claro/escuro, contraste, navegação lateral responsiva, mensagens toast, estados de carregamento e associação automática de labels a controles.
- **Local:** [frontend/assets/css/main.css](frontend/assets/css/main.css), [frontend/assets/js/app.js](frontend/assets/js/app.js), [frontend/index.html](frontend/index.html).
- **Impacto:** melhora de legibilidade e navegação em desktop e dispositivos menores.
- **Pendências:** ainda é necessário validar contraste, teclado, leitores de tela, foco de modais e responsividade em dispositivos reais.

## 3. Estado atual por funcionalidade

| Funcionalidade | Status | Evidência e motivo |
|---|---|---|
| Inicialização Flask | Funcionando | [backend/app.py](backend/app.py) registra os blueprints e serve o frontend. |
| Frontend servido pelo backend | Funcionando | A rota `/` e arquivos estáticos são servidos pelo Flask; foi observado HTTP 200. |
| Login por usuário/senha | Funcionando em desenvolvimento | Há rota, fallback local e testes de autenticação; a segurança de sessão é parcial. |
| Login por QR/carteirinha | Parcialmente funcionando | Há scanner, resolução e roles; cartão estático e autorização backend ainda são riscos. |
| Expiração de sessão | Parcialmente funcionando | O frontend expira cookie após 30 minutos, mas o backend não valida sessão. |
| CRUD de livros | Funcionando/parcial | Rotas GET/POST/PUT/DELETE existem e usam Supabase ou JSON; autorização não existe. |
| Cadastro automático por ISBN | Parcialmente funcionando | Implementado localmente, mas depende da Google Books e sofreu HTTP 429. |
| CRUD de alunos | Funcionando/parcial | Há CRUD, importação CSV e soft delete; autorização e validações profundas faltam. |
| Permissão de bibliotecário | Parcialmente funcionando | UI oculta opções e endpoint altera `is_librarian`, mas qualquer cliente pode chamar a rota. |
| Salas | Funcionando/parcial | CRUD e relação com alunos existem; testes E2E não foram executados. |
| Gêneros | Funcionando/parcial | CRUD e filtro de livros existem; associação automática por categoria é textual. |
| Empréstimos | Funcionando/parcial | Criação, disponibilidade e prazo existem; há risco de concorrência e ausência de autorização. |
| Devoluções | Funcionando/parcial | Valida aluno quando informado e registra data; falta teste integrado amplo. |
| Renovações | Funcionando/parcial | Rota existe e incrementa contador; não há limite de renovações configurado. |
| Dashboard | Funcionando/parcial | Métricas e devoluções pendentes são renderizadas; depende de APIs e dados consistentes. |
| Relatórios | Funcionando/parcial | Gráficos, geração mensal e CSV existem; algumas views SQL não são usadas pelo backend. |
| QR de livros/exemplares | Funcionando/parcial | Geração e resolução existem; registros antigos possuem fallback. |
| Carteirinhas | Funcionando/parcial | Geração PNG/cartão existe; expiração e revogação de QR administrativo não existem. |
| Fallback JSON | Funcionando/parcial | Permite operação offline local; não há fila nem reconciliação posterior. |
| Reconexão Supabase | Funcionando/parcial | Cliente tenta novamente após 60 segundos; falhas de schema podem ser mascaradas. |
| Google Books | Parcialmente funcionando | Consulta externa está implementada, mas está sujeita a quota/429 e sem cache. |

## 4. Lógica atual do sistema

### 4.1 Inicialização

1. [backend/app.py](backend/app.py) carrega `backend/.env` com `python-dotenv`.
2. O Flask registra blueprints de autenticação, livros, alunos, empréstimos, relatórios, salas, gêneros e QR.
3. O Flask serve o conteúdo de `frontend/`.
4. O cliente Supabase é criado sob demanda em [backend/utils/supabase_client.py](backend/utils/supabase_client.py).

### 4.2 Usuário e sessão

1. O usuário informa login e senha no frontend.
2. `POST /api/auth/login` consulta `usuarios` ou o fallback local.
3. O backend devolve o papel `admin` ou `librarian`.
4. O frontend armazena um cookie de sessão e oculta/mostra páginas conforme o papel.
5. Após 30 minutos sem atividade, o frontend executa logout.

O papel não é uma autorização criptograficamente confiável: as rotas não exigem token nem verificam o cookie.

### 4.3 Cadastro de livro

1. O administrador abre o Acervo e o modal de cadastro.
2. Pode digitar ISBN ou ler o código de barras.
3. O backend de scanner tenta ler a imagem usando PyZbar/OpenCV quando necessário.
4. O frontend consulta a Google Books pelo ISBN.
5. Título, autor, ISBN e categoria são preenchidos quando disponíveis.
6. O usuário confere e confirma o cadastro.
7. `create_book()` gera UUID próprio com `new_id()`, cria metadados dos exemplares e grava no Supabase ou JSON.
8. O QR gerado usa o ID próprio do sistema; o ISBN fica apenas como dado bibliográfico.

### 4.4 Empréstimo

1. O usuário procura o livro por ID, ISBN, QR ou texto.
2. O backend verifica o livro e calcula exemplares ativos.
3. O usuário identifica o aluno por nome, ID, carteirinha ou QR.
4. O backend calcula a data prevista e escolhe um exemplar disponível.
5. O empréstimo é inserido com `livro_id`, `aluno_id`, `exemplar`, `exemplar_id` e datas.
6. Disponibilidade futura é calculada a partir de empréstimos não devolvidos.

### 4.5 Devolução e renovação

- Devolução verifica se o empréstimo existe e ainda está ativo. Se uma referência de aluno for enviada, valida o aluno correspondente.
- Renovação verifica se o empréstimo não foi devolvido, soma dias e incrementa `renovacoes` quando o campo existe.
- Não há política de limite de renovações no backend.

### 4.6 Persistência e modo offline

- Operações tentam Supabase primeiro.
- Falhas classificadas como offline usam JSON local.
- Não existe fila, merge, controle de versão ou sincronização automática posterior.
- Uma mesma instalação pode ficar com dados divergentes entre Supabase e arquivos JSON.

## 5. Problemas encontrados

| Prioridade | Problema | Local/causa | Impacto | Solução recomendada |
|---|---|---|---|---|
| Crítica | APIs sem autenticação por requisição | Blueprints Flask não possuem middleware/decorator | Qualquer cliente pode chamar CRUD, empréstimos, relatórios e alteração de acesso | Criar sessão server-side ou JWT assinado, middleware e autorização por papel. |
| Crítica | RLS permissivo | [database.sql](database.sql) usa `USING (true)` e `WITH CHECK (true)` | Dados podem ficar legíveis/editáveis por clientes não autorizados | Revisar policies, separar anon/authenticated e usar backend com chave restrita. |
| Crítica | Possível exposição de chave de serviço | [backend/api/auth.py](backend/api/auth.py) usa `SUPABASE_SERVICE_KEY` como fallback retornável | Chave privilegiada pode chegar ao navegador | Endpoint deve devolver somente chave pública; service key nunca pode ser resposta. |
| Crítica | Segredo real em ambiente local exposto durante desenvolvimento | `backend/.env` é ignorado, mas foi compartilhado no contexto | Necessidade de rotação das chaves | Revogar/rotacionar chaves e usar Codespaces Secrets. |
| Alta | Credenciais padrão e senha em texto no SQL | `database.sql` e `DEFAULT_LOCAL_USERS` | Acesso previsível em ambientes implantados | Remover seeds reais, exigir configuração e armazenar somente hashes. |
| Alta | Cookie de sessão editável | [frontend/assets/js/app.js](frontend/assets/js/app.js) | Usuário pode forjar papel localmente; backend não valida | Sessão assinada/HttpOnly/Secure/SameSite e validação server-side. |
| Alta | Exclusão física pode apagar histórico | Foreign keys usam `ON DELETE CASCADE` e livros podem ser deletados | Empréstimos históricos podem desaparecer | Preferir soft delete e bloquear exclusão com histórico. |
| Alta | Concorrência na escolha de exemplar | disponibilidade é calculada antes do insert | Duas requisições podem escolher o mesmo exemplar | Transação, constraint e tratamento de conflito/retry. |
| Alta | Quota da Google Books | serviço externo respondeu HTTP 429 | Cadastro automático pode não preencher dados | Cache por ISBN, limite local, retry com backoff, API key própria e fallback. |
| Média | Falta de validação completa de ISBN | somente comprimento 10/13 é verificado | ISBN inválido pode ser consultado/armazenado | Validar dígitos verificadores e normalizar EAN-13/ISBN-10. |
| Média | Fallback JSON sem reconciliação | cliente Supabase alterna para arquivos | Dados podem divergir silenciosamente | Criar fila de operações e processo de reconciliação. |
| Média | Tratamento amplo de exceções | vários `except:` nos blueprints | Erros de schema/permissão parecem offline | Capturar exceções específicas, registrar contexto e retornar códigos corretos. |
| Média | Testes Python não executáveis no ambiente atual | `pytest` não está instalado nem em `backend/requirements.txt` | Falhas podem passar sem detecção | Adicionar pytest às dependências e executar CI. |
| Média | Scanner real não possui E2E físico | teste atual usa mocks | Compatibilidade de câmera permanece incerta | Testar navegadores, iluminação, EAN e imagens reais. |
| Baixa | CSP/CORS amplos | CORS `*`, `unsafe-inline` e scripts HTTPS | Superfície de ataque maior | Restringir origens, scripts e remover inline gradualmente. |
| Baixa | Documentação histórica divergente | vários relatórios antigos | Pode induzir decisões incorretas | Manter este relatório como referência e marcar documentos históricos. |

## 6. Melhorias já realizadas

- Login local e Supabase com fallback, aliases e mensagens mais claras.
- Suporte a bcrypt/passlib e re-hash de senhas legadas após autenticação.
- Sessão visual com expiração por inatividade.
- IDs UUID próprios para livros, alunos, empréstimos e exemplares.
- QR Code de entidades e exemplares.
- Scanner com leitura local, BarcodeDetector e fallback Pyzbar/OpenCV.
- Pré-processamento de imagens de baixa qualidade com grayscale, escala, nitidez, CLAHE e threshold.
- Cache/lazy loading de dependências do scanner e otimização de geração de carteirinhas.
- Tema claro/escuro, navegação responsiva e feedback visual.
- Cadastro ISBN/Google Books integrado ao formulário existente sem trocar o ID próprio.
- Fallback para JSON quando o Supabase está indisponível.

## 7. Melhorias necessárias

### Segurança

1. Implementar autenticação de API por sessão assinada ou JWT.
2. Aplicar autorização por papel em cada rota mutável e em relatórios.
3. Corrigir o endpoint de configuração para nunca retornar service key.
4. Trocar credenciais padrão e migrar todo o SQL para hashes.
5. Corrigir RLS e restringir CORS/CSP.
6. Proteger endpoints de QR e evitar QR administrativo permanente.

### Backend e dados

1. Substituir `except:` amplo por tratamento específico.
2. Fazer transação/controle de concorrência na seleção de exemplares.
3. Adotar soft delete consistente para livros e alunos.
4. Criar reconciliação offline/online.
5. Validar payloads, limites, datas, ISBN, CSV e parâmetros de relatório.
6. Usar views SQL ou queries agregadas quando isso reduzir custo e inconsistência.

### Frontend e usabilidade

1. Exibir estado de quota/indisponibilidade da Google Books com mensagem específica.
2. Evitar requisições repetidas do scanner sem resultado e permitir parada clara.
3. Adicionar estados de carregamento e retry em todas as operações críticas.
4. Revisar foco de modais, teclado, leitor de tela e contraste real.
5. Validar responsividade em celulares e câmeras de baixa capacidade.

### Operação

1. Adicionar `pytest` às dependências e configurar CI.
2. Criar comando de desenvolvimento e produção documentados.
3. Separar claramente configuração local, staging e produção.
4. Rotacionar segredos e usar Secrets do Codespaces/CI.

## 8. Funcionalidades que precisam ser criadas

| Funcionalidade | Objetivo | Local | Dependências | Prioridade | Status |
|---|---|---|---|---|---|
| Sessão server-side/JWT | Proteger cada requisição | `backend/app.py`, middleware e `api/` | Secret seguro, política de expiração | Crítica | Não implementada |
| Autorização RBAC no backend | Diferenciar admin e bibliotecário de verdade | Todas as rotas mutáveis | Sessão confiável | Crítica | Não implementada |
| Policies RLS restritas | Proteger acesso direto ao Supabase | `database.sql`/Supabase | Modelo de roles | Crítica | Não implementada |
| Fila de sincronização offline | Reconciliar JSON com Supabase | `backend/utils/` | Identidade de operação e conflitos | Alta | Não implementada |
| Cache de ISBN | Reduzir HTTP 429 | `backend/api/books.py` | Armazenamento local/Redis/DB | Alta | Não implementada |
| Fallback de provedor bibliográfico | Manter cadastro quando Google Books falhar | `backend/api/books.py` | Open Library ou fonte equivalente | Média | Não implementada |
| Limite de renovações | Aplicar regra de negócio | `backend/api/loans.py` e banco | Campo/configuração | Média | Não implementada |
| Suíte E2E | Validar fluxos reais | `backend/tests`, frontend | pytest, navegador/Playwright | Alta | Não implementada |

## 9. Funcionalidades que precisam ser modificadas

### Autenticação

- **Atual:** login valida usuário no backend, mas depois o frontend controla a sessão.
- **Problema:** cookie pode ser forjado e rotas não verificam identidade.
- **Necessário:** criar sessão confiável, validar papel em cada endpoint e invalidar sessão no logout.
- **Prioridade:** Crítica.

### Configuração Supabase

- **Atual:** endpoint retorna `SUPABASE_KEY` ou, na ausência, `SUPABASE_SERVICE_KEY`.
- **Problema:** fallback pode expor credencial privilegiada.
- **Necessário:** retornar somente URL e chave pública, ou eliminar a necessidade do frontend acessar Supabase diretamente.
- **Prioridade:** Crítica.

### Cadastro ISBN

- **Atual:** scanner e rota Google Books preenchem campos do modal.
- **Problema:** quota externa, sem cache, validação incompleta e sem teste de integração.
- **Necessário:** cache, backoff, chave própria, fallback, status 429 específico e validação de ISBN.
- **Prioridade:** Alta.

### Scanner

- **Atual:** tenta navegador e backend, com pré-processamento para baixa qualidade.
- **Problema:** falta comprovação com câmeras reais e o endpoint pode ser chamado repetidamente.
- **Necessário:** limitar chamadas, testar EAN/QR reais, exibir diagnóstico de câmera e manter fallback manual.
- **Prioridade:** Média.

### Empréstimos

- **Atual:** escolhe exemplar disponível e grava empréstimo.
- **Problema:** seleção e insert não são atômicos; renovação não tem limite.
- **Necessário:** transação/constraint com retry e regra explícita de renovação.
- **Prioridade:** Alta.

### Exclusão e histórico

- **Atual:** livros podem sofrer delete físico dependendo do schema.
- **Problema:** foreign key em cascade pode remover histórico.
- **Necessário:** soft delete e bloqueio de exclusão destrutiva.
- **Prioridade:** Alta.

## 10. Segurança e integridade

### Proteções existentes

- Senhas não ficam no frontend.
- Há tentativa de verificação com hashes bcrypt/passlib.
- O `.env` está ignorado pelo Git.
- Há timeout de inatividade no frontend.
- O backend não reproduz os segredos nos relatórios ou respostas normais.
- Há chaves estrangeiras, índices, unicidade de carteirinhas e constraint de exemplar ativo no SQL.
- Entradas básicas de login, livros e alunos possuem validações de campos obrigatórios.

### Riscos atuais

- APIs sem autenticação e autorização server-side.
- Cookie de sessão não assinado e editável.
- RLS que permite acesso amplo.
- Possível retorno de service key.
- Senhas padrão e seed em texto puro.
- CORS e CSP excessivamente permissivos.
- Endpoint de QR pode ser usado sem sessão.
- Campos JSON, CSV, datas, limites e parâmetros recebem validação insuficiente.

**Conclusão de segurança:** adequado apenas para desenvolvimento controlado. Não publicar em produção antes de corrigir os itens críticos.

## 11. Banco de dados

### Estrutura existente

- `usuarios`: login e senha.
- `salas`: salas, códigos, descrição e capacidade.
- `generos`: nome, ícone e cor.
- `livros`: ISBN, título, autor, área, gênero, exemplares, QR e metadados JSONB.
- `alunos`: turma, carteirinha, sala, QR, papel de bibliotecário e soft delete.
- `emprestimos`: relações de livro/aluno, exemplar, datas, observação, autor e renovações.
- `relatorios_mensais`: agregados mensais e rankings JSONB.

### Relações e regras

- Livro pertence opcionalmente a gênero.
- Aluno pertence opcionalmente a sala.
- Empréstimo referencia livro e aluno.
- Exemplar ativo é único por livro/código enquanto não devolvido.
- Carteirinha e QR de aluno possuem índices únicos parciais.
- IDs principais são UUID no banco; o backend também gera UUID explicitamente.
- Views SQL existem para empréstimos ativos e ranking de livros.

### Problemas e melhorias

- Policies RLS não restringem operações.
- Senhas iniciais não são hashes.
- `ON DELETE CASCADE` ameaça histórico.
- O backend nem sempre usa views e calcula agregações em memória.
- O modelo não possui fila de sincronização offline.
- O campo ISBN existe e está indexado; não é necessário criar outro identificador principal.
- Seria útil adicionar auditoria, `updated_at`, usuário autenticado da operação e política de soft delete para livros.

## 12. Frontend e interface

### Existente

- Tela de login por senha e QR.
- Dashboard com métricas e devoluções pendentes.
- Empréstimos com busca de livro/aluno, prazo, confirmação, devolução e renovação.
- Acervo com filtro, gêneros, exemplares, QR, cartão, edição e exclusão.
- Cadastro de ISBN com scanner e pesquisa automática.
- Cadastro/importação de alunos, salas e gêneros.
- Relatórios, gráficos e exportações.
- Tema claro/escuro, sidebar móvel, toasts, modais e estados de vazio.

### Pontos positivos

- Navegação por páginas sem projeto frontend paralelo.
- Componentes reaproveitam o Store e o cliente API.
- O scanner tem fallback local/backend.
- O ID exibido no QR continua sendo o ID próprio.
- Há esforço de acessibilidade automática para labels e aria-labels.

### Pontos a melhorar

- Papel e navegação são protegidos apenas por CSS/JavaScript.
- Algumas mensagens de erro são genéricas.
- Falta estado de erro específico para Google Books 429, câmera sem permissão e dependência nativa indisponível.
- Falta confirmação automatizada de responsividade e acessibilidade.
- Há dependência de CDNs externos para ícones, Chart.js e jsQR.
- Requisições do fallback do scanner podem ser frequentes enquanto nenhum código é encontrado.

## 13. Backend e APIs

### Rotas existentes

- `/api/auth`: login e configuração compatível do Supabase.
- `/api/books`: listar, consultar, criar, atualizar, excluir e buscar ISBN.
- `/api/students`: listar, consultar, criar, atualizar, excluir, importar CSV e alternar acesso de bibliotecário.
- `/api/loans`: listar, consultar, criar, renovar e devolver.
- `/api/rooms`: CRUD de salas.
- `/api/genres`: CRUD de gêneros.
- `/api/reports`: gráficos, rankings, mensal e exportações CSV.
- `/api/qr`: gerar, decodificar, iniciar/parar câmera, resolver login e gerar cartões.
- `/api/health`: verifica disponibilidade do banco `livros`.

### Organização

- Blueprints separam módulos.
- Helpers centralizam JSON, IDs, datas e estados.
- Cliente Supabase centraliza fallback/offline.
- O scanner carrega dependências pesadas sob demanda.

### Problemas

- Ausência de autenticação por rota.
- Exceções genéricas e fallback que mascara erros não relacionados à rede.
- Falta de schemas/DTOs e validação uniforme.
- Operações críticas sem transação.
- Serviço externo sem cache ou circuit breaker.
- Logs de desenvolvimento e debug não são adequados para produção.

## 14. Testes e evidências

### Testes existentes

Há oito arquivos Python em [backend/tests](backend/tests), cobrindo autenticação de bibliotecário, fallback de livros, performance de cartões, carregamento de ambiente, resolução de QR, status de relatórios, reconexão Supabase e IDs únicos. Há um teste JavaScript em [frontend/tests/qr-scanner.test.js](frontend/tests/qr-scanner.test.js).

### Executado nesta análise

- `node --test frontend/tests/qr-scanner.test.js`: **PASS**, 1 teste aprovado.
- `node --check` dos scripts alterados: **PASS**.
- `py_compile` dos módulos alterados: **PASS** em validações anteriores.
- `python -m pytest -q backend/tests`: **NÃO EXECUTADO**, pois `pytest` não está instalado no ambiente e não consta em `backend/requirements.txt`.
- Health check observado: **HTTP 200**, `status=ok`, `database=conectado`.
- Consulta anônima de `/api/books/`: **HTTP 200**, sem cookie de login.
- Consulta Supabase REST à tabela `livros`: **HTTP 200**.
- Google Books: a chamada direta respondeu **HTTP 429** durante a verificação.

### Testes ainda necessários

- suíte Python completa em ambiente reproduzível;
- autenticação e autorização com e sem sessão;
- RLS no Supabase usando anon/authenticated/service;
- CRUD de cada módulo;
- empréstimos concorrentes e exemplares múltiplos;
- devolução e renovação com regras inválidas;
- fluxo completo scanner -> ISBN -> Google Books -> cadastro;
- testes com câmera real, EAN-13, ISBN-10, QR e baixa iluminação;
- testes E2E desktop/mobile;
- falhas de rede, quota, timeout, JSON inválido e fallback;
- segurança de cookies, headers, CORS e CSP.

## 15. Pendências consolidadas

| Prioridade | Módulo | Pendência | Status | Ação necessária |
|---|---|---|---|---|
| Crítica | Segurança | Proteger APIs por sessão/token e papel | Pendente | Implementar middleware e decorators. |
| Crítica | Banco | Corrigir RLS permissivo | Pendente | Redefinir policies por operação e role. |
| Crítica | Supabase | Impedir exposição de service key | Pendente | Nunca usar service key como chave pública. |
| Crítica | Credenciais | Rotacionar segredos expostos e remover padrões | Pendente | Secrets manager e hashes obrigatórios. |
| Alta | Empréstimos | Resolver concorrência na escolha de exemplar | Pendente | Transação, constraint e retry. |
| Alta | Dados | Evitar cascade destrutivo do histórico | Pendente | Soft delete e política de retenção. |
| Alta | ISBN | Cache, quota, backoff e fallback de provedor | Pendente | Implementar no backend. |
| Alta | Testes | Instalar/configurar pytest e CI | Pendente | Dependência, comando e pipeline. |
| Média | Scanner | Validar câmera real e reduzir polling sem código | Pendente | Matriz de dispositivos e throttle. |
| Média | Offline | Reconciliação Supabase/JSON | Pendente | Fila, IDs de operação e conflitos. |
| Média | API | Validação uniforme e exceções específicas | Pendente | Schemas e respostas padronizadas. |
| Média | Frontend | Estados de quota, câmera e rede | Pendente | Mensagens e retry orientados ao usuário. |
| Baixa | Segurança web | Restringir CORS/CSP | Pendente | Remover permissões amplas gradualmente. |
| Baixa | Documentação | Atualizar relatórios antigos e comandos | Em andamento | Usar este documento como referência atual. |

## 16. Roadmap recomendado

### Etapa 1 — Correções críticas

1. Revogar/rotacionar qualquer segredo exposto.
2. Remover credenciais padrão reais e hashes em texto puro.
3. Implementar autenticação server-side e autorização por papel.
4. Impedir retorno de service key.
5. Revisar RLS e testar acesso anon/authenticated/service.

Essa etapa vem primeiro porque falhas de acesso podem expor ou alterar todo o banco, independentemente da qualidade da interface.

### Etapa 2 — Correções e ajustes importantes

1. Proteger concorrência de exemplares.
2. Substituir deletes destrutivos por soft delete.
3. Padronizar validação e tratamento de erros.
4. Definir limites de renovação e regras de negócio.
5. Corrigir inconsistências entre login por senha e cartão QR.

### Etapa 3 — Funcionalidades faltantes

1. Criar fila de sincronização offline/online.
2. Adicionar cache e fallback para ISBN.
3. Implementar auditoria de operações.
4. Adicionar testes E2E e matriz de câmera.

### Etapa 4 — Interface e experiência

1. Melhorar estados de carregamento, quota e permissão de câmera.
2. Validar acessibilidade e navegação por teclado.
3. Testar responsividade real em celular.
4. Reduzir polling do scanner e dar feedback de qualidade da imagem.

### Etapa 5 — Segurança e otimização

1. Restringir CORS e CSP.
2. Adicionar rate limiting às APIs e à busca ISBN.
3. Revisar logs, headers e modo debug.
4. Otimizar relatórios com views/queries quando necessário.

### Etapa 6 — Testes finais e produção

1. Executar pytest e testes frontend em CI.
2. Executar testes de segurança e carga.
3. Validar backup/restauração do Supabase.
4. Configurar servidor WSGI de produção, variáveis seguras e monitoramento.
5. Publicar somente após resolver as prioridades Crítica e Alta.

## 17. Conclusão

### IMPLEMENTADO

- Aplicação Flask com frontend servido pelo backend.
- CRUD dos principais cadastros.
- Empréstimos, devoluções, renovações e relatórios.
- Supabase com fallback JSON.
- IDs próprios, exemplares, QR Codes e cartões.
- Login local/Supabase e expiração visual de sessão.
- Scanner QR/EAN com processamento de imagens.
- Integração de cadastro por ISBN no formulário existente.

### FUNCIONANDO COM EVIDÊNCIA

- Health check e consulta Supabase: HTTP 200 durante a análise.
- API de livros sem login: HTTP 200 durante a análise.
- Teste JavaScript do scanner: aprovado.
- Sintaxe dos módulos alterados: aprovada.

### PARCIAL OU COM LIMITAÇÃO

- Google Books, devido a HTTP 429 e ausência de cache/quota própria.
- Scanner físico, devido à ausência de E2E com dispositivos reais.
- Fallback offline, por não reconciliar dados.
- Sessão e RBAC, por dependerem do frontend.

### NÃO IMPLEMENTADO OU PENDENTE

- Autorização real por requisição.
- RLS seguro.
- Rotação e gestão segura de segredos.
- Reconciliação offline/online.
- Suíte Python executável no ambiente/CI.
- Testes E2E e de segurança.

O próximo passo recomendado é corrigir segurança e integridade de dados antes de ampliar funcionalidades. O cadastro ISBN e o scanner podem continuar sendo aprimorados, mas não devem ser considerados garantia de funcionamento externo enquanto a Google Books estiver limitada e não houver testes reais de câmera.
