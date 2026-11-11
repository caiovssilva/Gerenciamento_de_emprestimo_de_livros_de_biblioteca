# Auditoria técnica e bateria de testes

## 1. Identificação

**Projeto:** Sistema de Gerenciamento de Empréstimos da Biblioteca Narceu de Paiva Filho  
**Tipo:** protótipo escolar de TCC desenvolvido individualmente  
**Data da auditoria:** 02/11/2026  
**Branch analisada:** `fix/login-error-message`  
**Objetivo:** verificar o estado real do protótipo por meio de inspeção, testes automatizados, verificações locais e análise defensiva de segurança.

Este relatório registra apenas o que foi observado no repositório e executado no ambiente disponível. A existência de uma rota, tela ou função não foi tratada como prova de funcionamento. Testes com mocks foram separados de testes que dependeriam do Supabase, do navegador, da câmera ou de serviços externos.

### Regras observadas durante a auditoria

- Nenhum arquivo de código foi alterado.
- Nenhum banco remoto foi modificado.
- Nenhum registro foi criado, alterado ou apagado em serviço externo.
- Nenhum segredo foi impresso ou incluído neste relatório.
- Nenhum deploy foi realizado.
- Não foram executados testes de carga contra produção.
- O arquivo `apresentacao.md`, que já estava como alteração não rastreada, foi preservado.
- O único arquivo criado nesta etapa foi este relatório `testes.md`.

## 2. Resumo executivo

O repositório contém uma aplicação web com frontend estático em HTML, CSS e JavaScript, backend Flask em Python e integração planejada com Supabase/PostgreSQL. O núcleo do MVP está representado por alunos, livros, exemplares, empréstimos, devoluções e consultas.

Foram coletados **192 testes Python** e **7 testes JavaScript**, totalizando **199 casos automatizados**. A execução atual apresentou:

- **191 PASSOU**: 184 testes Python e 7 testes JavaScript;
- **8 FALHOU**: todos na suíte Python, com respostas `503` de Supabase indisponível;
- **1 comando BLOQUEADO**: `npm test`, porque não existe `package.json` com script de teste;
- **validações PARCIAIS ou BLOQUEADAS**: banco remoto, autorização dinâmica, câmera física, navegador real, RLS efetivo, integrações externas e desempenho de produção.

O backend inicia e registra 71 regras de rota. O endpoint `/api/health` passou e retorna `200`. O endpoint `/api/ready` retornou `503`, confirmando que a aplicação não conseguiu validar a disponibilidade do banco. As APIs de negócio também retornaram `503` devido ao guard de banco.

O estado atual não permite concluir que o MVP esteja funcionando integralmente. A maior parte dos testes unitários e de lógica isolada passa, mas os fluxos que dependem do Supabase não puderam ser validados com o banco real. Também foram confirmados riscos importantes de segurança: fallback de chave de serviço em rota pública, segredo padrão de sessão, CORS amplo, ausência de uma camada geral de autorização, senha impressa em cartão administrativo, RLS permissivo e comandos destrutivos no SQL.

## 3. Tabela geral de resultados

### 3.1 Casos automatizados

Esta tabela conta somente os casos de teste realmente coletados e executados pelas suítes existentes. O total é `192 + 7 = 199`.

| Classificação | Quantidade | Escopo | Evidência |
|---|---:|---|---|
| PASSOU | 191 | 184 Python + 7 JavaScript | Saída do `pytest` e `node --test` |
| FALHOU | 8 | 8 testes Python | Assertions esperavam `200` ou `201`, receberam `503` |
| BLOQUEADO | 0 | Casos automatizados | Os casos foram executados; os que não passaram foram classificados como FALHOU |
| PARCIAL | 0 | Casos automatizados | A classificação parcial foi usada nas validações fora das suítes |
| NÃO EXECUTADO | 0 | Casos coletados | Todos os 199 casos coletados foram chamados |
| **TOTAL** | **199** | **Suites existentes** | **192 Python + 7 JavaScript** |

### 3.2 Validações fora das suítes

| Classificação | Verificações |
|---|---|
| PASSOU | Sintaxe de 31 arquivos Python; sintaxe de 20 arquivos JavaScript; `/api/health`; página inicial; 14 assets declarados no HTML; compatibilidade nominal das tabelas backend/SQL; importação das bibliotecas instaladas |
| FALHOU | `npm test`; 8 casos Python; readiness do banco |
| BLOQUEADO | Banco remoto; fluxos de escrita; teste dinâmico completo de autorização; câmera física; navegador real; chamadas reais para ISBN, Groq ou OpenAI |
| PARCIAL | Inicialização Flask; carregamento pelo test client; sondagem de rotas sem sessão, interrompida pelo `503` de banco; configuração pública do Supabase |
| NÃO EXECUTADO | Teste de carga; medição de cobertura; teste em dispositivos móveis; inspeção do Supabase remoto; execução contra produção |

As categorias desta segunda tabela são qualitativas e não são somadas ao total de 199 casos automatizados.

## 4. Estrutura técnica identificada

### 4.1 Componentes

| Componente | Localização | Tecnologia | Estado observado |
|---|---|---|---|
| Aplicação Flask | [backend/app.py](backend/app.py) | Python/Flask | Importa e registra rotas |
| Blueprints de API | [backend/api](backend/api) | Python/Flask | Rotas registradas |
| Scanner e QR | [backend/scanner](backend/scanner) | Pillow, qrcode, OpenCV, Pyzbar | Código e testes presentes |
| Cliente de banco | [backend/utils/supabase_client.py](backend/utils/supabase_client.py) | Supabase/PostgREST | Cliente criado, readiness indisponível |
| Dados locais | [backend/data](backend/data) | JSON | Fallback existente, mas bloqueado pelas regras atuais de API |
| Frontend | [frontend/index.html](frontend/index.html) e `frontend/assets` | HTML/CSS/JavaScript | Página e assets servidos pelo Flask |
| Testes Python | [backend/tests](backend/tests) | pytest | 192 casos coletados |
| Testes JavaScript | [frontend/tests](frontend/tests) | Node test runner | 7 casos executados |
| Banco | [database.sql](database.sql) | PostgreSQL/Supabase | Schema analisado estaticamente |

### 4.2 Rotas e módulos

Foram registradas **71 regras de rota**, incluindo:

- autenticação e autoatendimento;
- livros, ISBN e exemplares;
- alunos e acesso de bibliotecário;
- empréstimos, devoluções e renovações;
- salas e gêneros;
- relatórios e exportações;
- QR Codes;
- configuração do Supabase;
- health check e readiness;
- entrega do frontend.

Entre os módulos principais estão:

- [backend/api/auth.py](backend/api/auth.py): login, sessão, autoatendimento e configuração pública;
- [backend/api/books.py](backend/api/books.py): livros, ISBN e visão;
- [backend/api/students.py](backend/api/students.py): alunos, carteirinhas e perfil de bibliotecário;
- [backend/api/loans.py](backend/api/loans.py): empréstimos, renovações e devoluções;
- [backend/api/reports.py](backend/api/reports.py): relatórios e CSV;
- [backend/scanner/routes.py](backend/scanner/routes.py): QR Codes e cartões;
- [frontend/assets/js/api.js](frontend/assets/js/api.js): chamadas HTTP do frontend.

## 5. Ambiente e versões

| Item | Resultado |
|---|---|
| Sistema | Ubuntu 24.04.5 LTS, conforme ambiente informado |
| Python global | 3.14.2 |
| Python usado nos testes | 3.12.3 em `.venv312` |
| Node.js | v24.22.2 |
| npm | 11.19.1 |
| pytest | 9.1.1 instalado no ambiente virtual |
| Flask | 3.0.3 |
| Flask-CORS | 4.0.1 |
| Supabase | 2.31.0 |
| Pillow | 12.3.0 |
| OpenCV | 4.10.0.84 |
| Pyzbar | 0.1.9 |
| qrcode | 7.4.2 |
| NumPy | 2.5.3 |
| Gunicorn | 22.0.0 |
| passlib | 1.7.4 |
| bcrypt | 5.0.0 |
| Groq | 1.7.0 |
| OpenAI | 3.19.0 |

O arquivo [backend/requirements.txt](backend/requirements.txt) declara as principais dependências, mas não declara `pytest`. `groq` e `openai` também não possuem versão fixa nesse arquivo. O ambiente local possui esses pacotes instalados, mas isso não garante que uma instalação limpa reproduza o mesmo resultado.

Não foi localizado `package.json` na raiz. Existe `package-lock.json`, porém o comando padrão `npm test` não pôde ser executado por falta do manifesto do projeto.

## 6. Comandos executados

Os comandos principais desta auditoria foram:

```bash
git status --short --branch
python --version
.venv312/bin/python --version
node --version
npm --version
find frontend/tests backend/tests -maxdepth 2 -type f -print
.venv312/bin/python -m pytest backend/tests -q
node --test frontend/tests/*.test.js
.venv312/bin/python -m pytest backend/tests --collect-only -q
node --test frontend/tests/*.test.js --test-reporter=dot
npm test
```

Também foram executados scripts locais e não destrutivos para:

- importar a aplicação Flask;
- listar as 71 rotas registradas;
- consultar `/api/health`, `/api/ready` e `/`;
- verificar o status de `/api/config/supabase`;
- verificar presença de variáveis de ambiente sem imprimir valores;
- analisar a sintaxe de 31 arquivos Python com `ast.parse`;
- analisar a sintaxe de 20 arquivos JavaScript com `node --check`;
- testar os 14 assets declarados pelo HTML;
- comparar tabelas referenciadas pelo backend com tabelas do SQL;
- importar bibliotecas instaladas;
- sondar rotas sem sessão, sem executar operações de banco;
- verificar o fallback de chave usando somente um valor fictício.

## 7. Testes existentes executados

### 7.1 Backend

Comando:

```bash
.venv312/bin/python -m pytest backend/tests -q
```

Resultado real:

```text
192 testes coletados
184 passed
8 failed
3 warnings
tempo aproximado: 6,58 s
exit code: 1
```

Os oito testes falhos foram:

| Teste | Arquivo | Resultado observado |
|---|---|---|
| `test_get_book_and_student_by_id` | `backend/tests/test_qr_id_resolution.py` | Esperava `201`; recebeu `503` |
| `test_qr_decode_resolves_student_by_id` | `backend/tests/test_qr_id_resolution.py` | Esperava `201`; recebeu `503` |
| `test_report_data_and_csv_remove_duplicate_records` | `backend/tests/test_reports_data.py` | Esperava `200`; recebeu `503` |
| `test_student_directory_export_includes_students_without_loans_and_room_details` | `backend/tests/test_reports_data.py` | Esperava `200`; recebeu `503` |
| `test_student_status_export_includes_borrowed_owing_and_returned` | `backend/tests/test_reports_student_status.py` | Esperava `200`; recebeu `503` |
| `test_self_service_card_lookup_normalizes_input_and_false_librarian_flag` | `backend/tests/test_self_service_auth.py` | Esperava `200`; recebeu `503` |
| `test_self_service_card_lookup_tolerates_card_formatting` | `backend/tests/test_self_service_auth.py` | Esperava `200`; recebeu `503` |
| `test_create_book_generates_distinct_ids_and_qr_codes_for_same_title` | `backend/tests/test_unique_identifiers.py` | Esperava `201`; recebeu `503` |

O padrão comum nos oito casos foi:

```text
API bloqueada: Supabase indisponível
DATABASE_UNAVAILABLE
```

Isso indica dependência do guard de banco introduzido em [backend/app.py](backend/app.py). Os testes tentam usar dados simulados ou fallback local, mas o `before_request` exige uma consulta ao Supabase antes de permitir que a lógica testada seja alcançada. A causa imediata da falha é a indisponibilidade do banco no ambiente; o resultado ainda deve ser registrado como **FALHOU**, e não como passou.

Avisos registrados:

- depreciação de `crypt` usada por `passlib`;
- parâmetros `timeout` e `verify` depreciados no cliente Supabase/PostgREST.

### 7.2 Frontend

Comando:

```bash
node --test frontend/tests/*.test.js
```

Resultado real:

```text
7 testes
7 pass
0 fail
0 cancelados
0 skipped
exit code: 0
```

Arquivos executados:

- `frontend/tests/api-retry.test.js`;
- `frontend/tests/books-isbn.test.js`;
- `frontend/tests/catalog-crud.test.js`;
- `frontend/tests/modal-interaction.test.js`;
- `frontend/tests/navigation.test.js`;
- `frontend/tests/qr-scanner.test.js`;
- `frontend/tests/reports.test.js`.

Os resultados demonstram comportamento JavaScript isolado nos cenários cobertos. Não comprovam câmera real, compatibilidade visual, navegação em navegador real ou persistência no Supabase.

### 7.3 Sintaxe

Resultado da análise por AST e `node --check`:

- **31 arquivos Python:** 0 erros de sintaxe;
- **20 arquivos JavaScript:** 0 erros de sintaxe.

Essa verificação foi somente sintática. Não substitui testes de execução dos módulos e não mede cobertura.

## 8. Inicialização, rotas e endpoints básicos

### 8.1 Inicialização

A aplicação Flask foi importada com `PYTHONPATH=backend` e registrou 71 regras. A primeira tentativa sem esse caminho falhou com `ModuleNotFoundError: No module named 'app'`; isso foi um problema do comando executado a partir da raiz, não uma falha da aplicação, pois o layout coloca o módulo em `backend/app.py`.

### 8.2 Health check e readiness

| Endpoint | Status | Resultado |
|---|---:|---|
| `GET /api/health` | 200 | PASSOU; Flask respondeu com status `ok` |
| `GET /api/ready` | 503 | FALHOU/PARCIAL; banco não disponível |
| `GET /` | 200 | PASSOU; HTML inicial foi servido |
| `GET /api/config/supabase` | 200 | PASSOU funcionalmente, mas possui risco de configuração descrito na segurança |

O `health` prova apenas que o processo Flask responde. O `ready` falhou porque a consulta ao Supabase não foi concluída.

### 8.3 Assets

Foram extraídos do HTML e testados **14 assets**:

- 1 arquivo CSS;
- 13 arquivos JavaScript, incluindo API, store, páginas, scanner, gráficos e configuração.

Todos retornaram `200` pelo cliente de teste Flask. Isso comprova disponibilidade HTTP local, não execução sem erros no navegador.

### 8.4 Métodos HTTP e parâmetros

As rotas foram enumeradas, mas não foi possível validar integralmente os métodos de negócio contra banco real. As sondagens sem sessão para livros, alunos, empréstimos, relatórios e criação de registros retornaram `503` antes da validação de payload.

Consequentemente, os seguintes comportamentos ficam **BLOQUEADOS/PARCIAIS** neste ambiente:

- respostas `400` para dados ausentes em rotas protegidas pelo guard de banco;
- respostas `404` para registros inexistentes quando a rota exige banco;
- respostas `409` para duplicidade ou indisponibilidade de exemplar;
- respostas `401` e `403` de autorização administrativa;
- escrita e leitura persistente no Supabase.

## 9. Testes do núcleo do MVP

### 9.1 Alunos

**Código identificado:** [backend/api/students.py](backend/api/students.py).

Há rotas para listar, consultar, criar, editar, excluir, importar CSV e alternar o acesso de bibliotecário. Há validação de nome e turma, normalização de turma, tentativa de tratamento de carteirinha duplicada e fallback para JSON.

**Resultado da auditoria:**

- validações internas e utilitários foram parcialmente cobertos pelos testes;
- fluxos de criação e consulta por QR falharam com `503` nos testes integrados;
- persistência real não foi validada;
- edição, exclusão e importação em banco remoto não foram validadas;
- duplicidade no banco remoto não foi executada;
- autorização administrativa da rota `/api/students/<student_id>/access` não foi comprovada e não há decorator geral evidente no módulo.

**Classificação:** PARCIAL.

### 9.2 Livros e exemplares

**Código identificado:** [backend/api/books.py](backend/api/books.py).

Há rotas para catálogo, cadastro, alteração, exclusão, exemplares, ISBN e visão. A aplicação possui lógica de normalização de ISBN e testes de fallback e integrações simuladas.

**Resultado da auditoria:**

- testes unitários de ISBN e fallback foram executados dentro da suíte;
- testes de identificadores únicos falharam com `503` antes da asserção principal;
- disponibilidade foi analisada no código de empréstimos, mas não validada com concorrência;
- QR Code foi exercitado em cenários simulados, não em câmera física;
- cadastro e atualização persistentes no Supabase ficaram bloqueados.

**Classificação:** PARCIAL.

### 9.3 Empréstimos

**Código identificado:** [backend/api/loans.py](backend/api/loans.py).

O código verifica livro, aluno, disponibilidade e seleciona exemplar. Há constraint parcial no SQL para evitar mais de um empréstimo ativo por par livro/exemplar. Entretanto, a escolha da disponibilidade e a inserção do empréstimo ocorrem em etapas separadas na aplicação.

**Resultado da auditoria:**

- validações de função e QR aparecem na suíte;
- registro com banco indisponível não foi completado;
- concorrência real não foi executada;
- não foi comprovado o comportamento com dois pedidos simultâneos;
- não há teste de carga contra banco isolado;
- prazos são calculados pela função existente, mas persistência e consulta não foram confirmadas.

**Classificação:** PARCIAL.

### 9.4 Devoluções e renovações

O código rejeita devolução já concluída e exige QR do exemplar para a devolução comum. A renovação rejeita empréstimo devolvido e exige QR, exceto em fluxo confiável de autoatendimento.

Foram observados os seguintes limites:

- `renovacoes` é incrementado, mas não há limite máximo explícito em [backend/api/loans.py](backend/api/loans.py);
- não há evidência de multa ou bloqueio por atraso;
- o retorno de uma atualização concorrente não foi testado;
- atualização de disponibilidade não foi validada no banco real;
- histórico completo não foi validado após uma sequência real de empréstimo e devolução.

**Classificação:** PARCIAL.

## 10. Banco de dados

### 10.1 Estrutura encontrada

O [database.sql](database.sql) declara:

- 7 tabelas: `usuarios`, `salas`, `generos`, `livros`, `alunos`, `emprestimos` e `relatorios_mensais`;
- 2 views: `vw_emprestimos_ativos` e `vw_livros_ranking`;
- 4 referências de chave estrangeira;
- 7 chaves primárias;
- 3 índices únicos;
- índice parcial `idx_exemplar_ativo` para empréstimo ativo;
- índice para `exemplar_id`;
- 7 políticas RLS;
- 9 comandos `DROP TABLE` ou `DROP VIEW`.

### 10.2 Compatibilidade backend/SQL

Foi feita comparação textual das tabelas usadas pelo backend com o SQL. Resultado:

```text
Tabelas referenciadas pelo backend sem correspondência no SQL: nenhuma.
Tabelas do SQL sem referência direta encontrada: nenhuma.
```

Isso indica compatibilidade nominal entre os nomes encontrados. Não prova compatibilidade de tipos, permissões, views materializadas, schema remoto ou dados reais.

### 10.3 Banco remoto

O banco remoto não foi inspecionado diretamente e o endpoint `/api/ready` retornou `503`. Portanto, ficaram **BLOQUEADOS**:

- existência real das tabelas no projeto Supabase configurado;
- execução real das constraints;
- comportamento efetivo das políticas RLS;
- compatibilidade das views no banco remoto;
- leitura e escrita de dados;
- concorrência e transações;
- desempenho das consultas.

### 10.4 Riscos identificados no SQL

- O script apaga tabelas e views com `CASCADE` antes de recriar o schema.
- `usuarios` recebe credenciais padrão em texto claro.
- `emprestimos.livro_id` e `emprestimos.aluno_id` usam `ON DELETE CASCADE`, podendo apagar histórico.
- As políticas de seis tabelas permitem `USING (true)` e `WITH CHECK (true)`.
- `usuarios` possui política de seleção ampla.
- Os exemplares são armazenados em JSONB, sem constraint estrutural completa para a lista.
- Datas e timestamps usam tipos sem timezone.
- `criado_por` e `gerado_por` são texto livre.

O SQL não foi executado, justamente para evitar comandos destrutivos ou alterações no banco.

## 11. Bibliotecas e integrações

### 11.1 Bibliotecas importadas

As bibliotecas abaixo estavam instaladas e foram importadas com sucesso no ambiente virtual:

| Biblioteca | Responsabilidade | Importação |
|---|---|---|
| Flask | API e servidor | PASSOU |
| Flask-CORS | CORS | PASSOU |
| python-dotenv | Variáveis de ambiente | PASSOU |
| qrcode | Geração de QR | PASSOU |
| Pillow | Imagens e cartões | PASSOU |
| OpenCV | Processamento de imagem | PASSOU |
| Pyzbar | Leitura de códigos | PASSOU |
| NumPy | Matrizes de imagem | PASSOU |
| Supabase | Cliente do banco | PASSOU |
| Groq | Consulta de visão/IA | PASSOU |
| OpenAI | Cliente alternativo de visão | PASSOU |
| Gunicorn | Servidor de produção | PASSOU |
| passlib/bcrypt | Senhas | PASSOU |
| pytest | Testes Python | PASSOU, mas não declarado no requirements |

Importar uma biblioteca não significa que o serviço externo ou o fluxo de câmera tenha sido executado.

### 11.2 ISBN

Há testes com mocks para Google Books, ISBNsearch, Open Library, Groq e visão. Esses testes validam normalização, fallback, combinação de fontes e tratamento de respostas simuladas.

Não foram feitas requisições reais às fontes de ISBN durante esta auditoria. Chaves e quotas não foram verificadas. O resultado real de rede é, portanto, **BLOQUEADO/NÃO EXECUTADO**.

### 11.3 Groq e OpenAI

O código contém caminhos para visão com Groq e OpenAI. Os testes usam clientes ou respostas simuladas. A variável `OPENAI_API_KEY` não foi considerada necessária para os testes locais e nenhuma chamada externa foi realizada.

**Classificação:** testes unitários PARCIAIS; integração real NÃO EXECUTADA.

### 11.4 QR, Pillow, OpenCV e Pyzbar

Os módulos importaram e os testes de geração/processamento foram executados em parte. A câmera física, permissões do navegador, iluminação, foco e compatibilidade de dispositivo não foram testados.

**Classificação:** PARCIAL.

### 11.5 Supabase/PostgreSQL

O cliente está configurado no ambiente, mas a consulta de readiness falhou e as APIs retornaram `503`. Não houve acesso validado ao banco real.

**Classificação:** BLOQUEADO.

## 12. Análise de segurança

Esta seção é defensiva e baseada em inspeção local, testes com cliente Flask e configuração fictícia. Não foram feitos ataques, tentativas contra contas reais ou chamadas destrutivas.

### 12.1 Exposição potencial de chave privilegiada

Em [backend/api/auth.py](backend/api/auth.py), a configuração pública usa a lógica equivalente a:

```python
key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_KEY") or ""
```

O teste controlado removeu `SUPABASE_KEY` e forneceu apenas `dummy-service-key-for-audit` como `SUPABASE_SERVICE_KEY`. As rotas:

- `/api/auth/config/supabase`;
- `/api/config/supabase`;

retornaram `200` contendo o valor fictício. Isso confirma o fallback em comportamento local sem expor o segredo real do ambiente.

**Classificação:** FALHA DE SEGURANÇA CONFIRMADA ESTATICAMENTE E POR TESTE CONTROLADO.

### 12.2 Segredo padrão de sessão

Em [backend/app.py](backend/app.py), existe fallback para:

```python
os.getenv("SECRET_KEY", "narceu-biblioteca-2026-dev-only")
```

Se a variável não for definida, sessões podem usar um segredo previsível.

**Classificação:** RISCO ALTO CONFIRMADO POR INSPEÇÃO.

### 12.3 Autenticação e autorização

O backend possui lógica de sessão e regras específicas de autoatendimento. Porém, os módulos CRUD exibem rotas diretamente decoradas com métodos HTTP, sem uma camada geral de `login_required` ou `require_role` visível em cada operação.

O `before_request` restringe especialmente sessões `self_service`, mas a ausência de banco impediu validar respostas de autorização dos demais escopos. Portanto:

- controle do autoatendimento: parcialmente implementado e não validado ponta a ponta;
- autorização de todas as rotas administrativas: NÃO COMPROVADA;
- isolamento real por papel: BLOQUEADO para teste dinâmico.

### 12.4 CORS e CSP

O código configura:

```python
CORS(app, resources={r"/api/*": {"origins": "*"}})
```

O CSP permite `'unsafe-inline'` em scripts e estilos para compatibilidade com o frontend atual.

**Riscos:** origens amplas e política de script menos restritiva aumentam a superfície de ataque.

### 12.5 Carteirinha administrativa

Em [backend/scanner/routes.py](backend/scanner/routes.py), o cartão administrativo é montado com:

```python
field2 = f"Senha: {password}"
```

Isso coloca uma credencial reutilizável em uma imagem que pode ser impressa, baixada ou compartilhada.

**Classificação:** RISCO ALTO CONFIRMADO POR INSPEÇÃO.

### 12.6 QR e elevação de privilégio

O fluxo de QR concede escopo de bibliotecário quando o registro do aluno possui `is_librarian`. A rota que alterna esse campo aceita `PATCH` e `POST` e recebe `is_librarian` do corpo da requisição.

O teste dinâmico foi bloqueado pela indisponibilidade do banco, mas a necessidade de autorização administrativa não é visível no módulo analisado.

**Classificação:** RISCO ALTO; comportamento dinâmico NÃO COMPROVADO.

### 12.7 Sessão no frontend

O frontend grava um JSON com login, papel, nome, estudante e atividade em cookie próprio. O cookie usa `SameSite=Lax`, mas o código visível não define `Secure` nem `HttpOnly`, e o conteúdo é controlável pelo navegador.

**Classificação:** RISCO MÉDIO/ALTO, confirmado por inspeção.

### 12.8 XSS e validação de entrada

Foram localizados usos de `innerHTML` em código frontend que precisam ser avaliados conforme a origem dos dados. Não foi realizado teste de payload XSS no navegador, pois não havia ambiente de navegador real disponível.

Também há endpoints que recebem JSON sem schema formal. A análise estática indica necessidade de lista de campos permitidos, validação de tipo, limite de tamanho e rejeição de propriedades arbitrárias.

**Classificação:** risco confirmado por inspeção; exploração dinâmica NÃO EXECUTADA.

### 12.9 Uploads e integrações

O scanner aceita imagens em base64 e há integrações externas que recebem imagens. Não foram realizados testes de tamanho, MIME, quota ou abuso, para evitar chamadas externas e carga indevida.

**Classificação:** BLOQUEADO/NÃO EXECUTADO; risco de validação permanece.

## 13. Desempenho e compatibilidade

### Executado

- O módulo de geração de cartões possui teste de desempenho na suíte Python.
- A suíte Python completa terminou em aproximadamente 6,58 segundos.
- A suíte JavaScript terminou em aproximadamente 1 segundo na execução principal.
- O Flask serviu a página inicial e 14 assets com `200`.

### Não executado

- teste de carga;
- concorrência real de empréstimos;
- uso de memória e CPU sob carga;
- tempo de resposta do Supabase;
- desempenho do Render;
- teste em navegador móvel;
- teste em câmera física;
- compatibilidade com múltiplos navegadores;
- medição de cobertura de linhas, funções e branches.

### Compatibilidade observada

Python 3.12 foi usado nos testes e atende ao requisito documentado de Python 3.11 ou superior. Python global 3.14 está disponível, mas não foi usado para validar a suíte completa. O aviso de `crypt` depreciado em `passlib` indica possível problema de compatibilidade futura com versões mais novas do Python.

## 14. Lista consolidada de falhas e riscos

### Falhas observadas na execução

1. Oito testes Python falharam com `503` por Supabase indisponível.
2. `npm test` falhou porque não existe `package.json`.
3. `/api/ready` retornou `503`.
4. As APIs de negócio ficaram indisponíveis no ambiente sem banco pronto.

### Riscos técnicos confirmados por inspeção

1. Fallback de `SUPABASE_SERVICE_KEY` em rota pública.
2. Segredo padrão previsível para sessão.
3. CORS configurado para todas as origens.
4. CSP permitindo `unsafe-inline`.
5. Ausência de camada geral evidente para autenticação e papel nos CRUDs.
6. Senha administrativa incorporada no cartão impresso.
7. Políticas RLS permissivas.
8. SQL destrutivo com `DROP ... CASCADE`.
9. Cascata de exclusão no histórico de empréstimos.
10. Ausência de limite máximo de renovações no código observado.
11. Possível concorrência entre seleção de disponibilidade e inserção do empréstimo.
12. Cookie de identidade do frontend não assinado e sem flags de proteção completas.
13. Possível XSS por inserção de dados em `innerHTML`.
14. Dependências sem todas as versões fixadas.
15. `pytest` não declarado em `backend/requirements.txt`.

## 15. Funcionalidades não testadas ou parcialmente testadas

As seguintes funcionalidades não podem ser declaradas concluídas com base nesta auditoria:

- conexão e persistência no Supabase remoto;
- funcionamento efetivo do RLS;
- autorização completa de administrador e bibliotecário;
- login real contra dados remotos;
- cadastro, edição e exclusão persistentes;
- empréstimo concorrente;
- atualização real de disponibilidade;
- histórico após operações reais;
- câmera física;
- leitura de QR em dispositivo real;
- leitura de ISBN pela câmera;
- consultas reais a Google Books, ISBNsearch, Open Library, Groq e OpenAI;
- execução em navegador real;
- responsividade visual;
- console JavaScript no navegador;
- carga e estabilidade em produção;
- cobertura de código.

O autoatendimento foi tratado como funcionalidade complementar, não como requisito obrigatório do núcleo do MVP. Os testes existentes cobrem parte dele, mas a dependência de configuração, banco e câmera impede uma aprovação integral.

## 16. Comparação com a documentação

| Afirmação documentada | Evidência atual | Situação |
|---|---|---|
| Há testes Python e JavaScript | Foram coletados 192 Python e 7 JavaScript | CORRETO |
| A última execução teve 180 aprovados e 12 falhas | A execução atual teve 184 aprovados e 8 falhas | DESATUALIZADO para o estado atual |
| O frontend pode ser testado com `node --test` | `node --test frontend/tests/*.test.js` passou 7/7 | CORRETO |
| O backend depende do Supabase para operações de negócio | `/api/ready` e rotas de negócio retornaram `503` | CORRETO |
| O sistema possui fallback local | Há arquivos JSON e funções de fallback, mas o guard global bloqueia a API antes do fallback em vários fluxos | PARCIAL |
| A câmera e QR fazem parte dos fluxos | Há código e testes simulados | NÃO COMPROVADO em dispositivo real |
| O banco possui sete tabelas principais | O SQL declara sete tabelas | CORRETO |
| O RLS protege os dados | O SQL tem RLS habilitado, mas seis políticas usam condições permissivas `true` | INCORRETO como garantia de segurança |
| A configuração pública usa uma chave segura | Com `SUPABASE_KEY` ausente, o fallback retorna `SUPABASE_SERVICE_KEY` fictícia no teste controlado | INCORRETO/RISCO CONFIRMADO |
| O sistema está pronto para uso | Testes, banco real, navegador e câmera não foram validados integralmente | NÃO COMPROVADO |

O relatório anterior [apresentacao.md](apresentacao.md) também registra limitações semelhantes, mas seus números de testes não representam esta execução atual. Este arquivo deve ser considerado o registro da bateria executada em 02/11/2026.

## 17. Limitações do ambiente de testes

- O Supabase configurado não respondeu com sucesso ao readiness.
- Nenhuma credencial real foi exposta ou usada de forma invasiva.
- O banco remoto não foi alterado nem inspecionado diretamente.
- Não havia `package.json` para o comando `npm test`.
- Não havia ambiente de navegador automatizado disponível para console, responsividade e câmera.
- Não foi possível confirmar permissões de câmera ou leitura física.
- Não foram executadas chamadas reais às APIs externas.
- Não foi feito teste de carga ou concorrência contra ambiente de produção.
- A análise do SQL foi estática; o script não foi executado.
- A análise de segurança não incluiu exploração ofensiva.
- Não foi medida cobertura de código.
- O comando `rg` não estava instalado; buscas textuais foram realizadas com `grep` como fallback.

## 18. Conclusão sobre o estado do protótipo

O protótipo possui uma base técnica real, módulos separados, rotas registradas, testes automatizados e frontend servível. A suíte JavaScript passou integralmente e a maior parte da suíte Python passou em lógica isolada.

Apesar disso, o estado atual é **PARCIALMENTE FUNCIONAL E NÃO VALIDADO PARA PRODUÇÃO**. O banco não estava pronto no ambiente, oito testes falharam por esse motivo, o readiness retornou `503` e os fluxos centrais de persistência não puderam ser confirmados. Os testes aprovados não eliminam essa limitação.

Os problemas mais importantes são:

1. indisponibilidade do Supabase para validar o núcleo do MVP;
2. fallback que pode devolver chave de serviço em endpoint público;
3. segredo padrão de sessão;
4. autorização administrativa não demonstrada de forma uniforme;
5. RLS permissivo;
6. senha em cartão administrativo;
7. riscos de sessão, CORS, CSP e XSS;
8. concorrência e regras de renovação não comprovadas;
9. histórico sujeito a cascata destrutiva no SQL;
10. suíte Python ainda com oito falhas no estado auditado.

Nenhuma funcionalidade nova foi implementada e nenhuma falha foi corrigida durante esta auditoria. O resultado fiel é que o projeto avançou na organização e na cobertura automatizada, mas ainda precisa de validação do banco, correção dos riscos de segurança e execução dos fluxos reais antes de ser considerado confiável.

## 19. Arquivos e evidências principais

- [backend/app.py](backend/app.py): configuração Flask, CORS, sessão, guards de banco, health e readiness.
- [backend/api/auth.py](backend/api/auth.py): autenticação, autoatendimento e configuração pública do Supabase.
- [backend/api/students.py](backend/api/students.py): CRUD de alunos e alternância de bibliotecário.
- [backend/api/loans.py](backend/api/loans.py): criação, renovação e devolução de empréstimos.
- [backend/scanner/routes.py](backend/scanner/routes.py): QR e cartão administrativo.
- [frontend/assets/js/app.js](frontend/assets/js/app.js): cookie e estado de sessão no frontend.
- [database.sql](database.sql): tabelas, constraints, índices, RLS, views e comandos destrutivos.
- [backend/requirements.txt](backend/requirements.txt): dependências do backend.
- [README.md](README.md): comandos documentados e limitações declaradas.
- [apresentacao.md](apresentacao.md): relatório anterior de apresentação técnica.
