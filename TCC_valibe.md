# Guia técnico e de estudo do projeto de biblioteca

**Arquivo:** `TCC_valibe.md`  
**Data da análise inicial:** 02/10/2026

**Última atualização verificada:** terça-feira, 06/10/2026
**Natureza do documento:** documentação técnica, guia de estudo e preparação para relatório escolar.

> Apesar do nome do arquivo, este documento não afirma que o projeto é um TCC. O repositório apresenta um projeto escolar de gerenciamento de empréstimos de uma biblioteca. Quando uma informação não pôde ser comprovada, este documento usa a frase: **"Não foi possível confirmar esta informação no estado atual do projeto."**

---

## Como este documento foi construído

A análise seguiu esta ordem de confiança:

1. código atual;
2. `database.sql` atual;
3. testes e resultados executados;
4. dependências e configurações presentes;
5. README atual;
6. histórico Git;
7. relatórios antigos somente como contexto.

Quando uma documentação antiga divergia do código, o código atual foi considerado a referência principal. Números, estatísticas, credenciais, tokens e chaves não foram incluídos.

## Atualização verificada em 06/10/2026

Esta atualização registra a exigência de QR do exemplar no processo de devolução e os testes focados executados nessa data.

- `openDevolution()` abre a confirmação com o botão desabilitado. `scanDevolutionQr()` só o habilita quando o QR lido identifica o mesmo livro e o mesmo número de exemplar do empréstimo.
- `POST /api/loans/<loan_id>/return` exige `exemplar_qr` e valida livro, código do exemplar e identificador individual antes de gravar a devolução. QR ausente retorna HTTP 400; QR de outro exemplar retorna HTTP 403.
- A geração de cartões para livros sem `exemplares_meta` agora produz um QR por cópia. Cartões físicos antigos com QR genérico precisam ser gerados/impressos novamente para atender à confirmação por exemplar.
- Os testes focados de devolução, resolução QR e geração de cartões passaram: `7 passed`. Os quatro testes frontend disponíveis também passaram. A suíte backend completa não foi executada nesta atualização; o último resultado completo registrado continua sendo o de 04/10 (`32 passed, 6 failed, 3 warnings`).

## Atualização verificada em 04/10/2026

Este adendo registra a atualização feita em **domingo, 04/10/2026, às 20:59:52 UTC**, no branch `fix/login-error-message`, revisão `71eab32`. A suíte completa, os testes frontend e a chamada Vision sintética foram verificados em 04/10. As consultas reais textual manual/scanner mencionadas abaixo ocorreram em 02/10. Quando divergirem, este adendo e os quadros atualizados prevalecem sobre os snapshots anteriores. Nenhuma chave ou valor de Secret foi registrado.

- O arquivo `backend/.env` não é necessário no Codespace. `load_environment()` usa `override=False`, preservando variáveis injetadas pelo ambiente e deixando `.env` como fallback. O teste correspondente usa arquivo temporário e valores fictícios.
- Os testes backend de ISBN/Vision passaram: `25 passed`. Os dois testes frontend disponíveis passaram: formulário ISBN e callback do scanner.
- A suíte backend completa terminou com `32 passed, 6 failed, 3 warnings`. As seis falhas estão em quatro testes de login e dois de reconexão do Supabase.
- Em consulta real registrada em 02/10, o ISBN `9788532511010` nos modos scanner e manual respondeu HTTP 200 e retornou o mesmo título e autor. No modo scanner a resposta pode combinar Groq e fontes bibliográficas; não é possível atribuir cada campo exclusivamente ao Groq.
- Uma chamada isolada ao Groq Vision, com frame sintético criado em memória, retornou `9788532511010`. Isso confirma uma chamada funcional naquele momento, mas não valida câmera física, foco, iluminação ou leitura contínua no navegador.
- O navegador havia recebido HTTP 502 com mensagem de limite de chamadas do Groq. Uma chamada isolada posterior teve sucesso. O scanner agora consulta Vision a cada 5 segundos e aplica espera crescente após erros; a leitura local permanece disponível.
- Os caminhos `POST /api/qr/decode` e `POST /api/books/isbn-vision` estão registrados no código atual. Antes de iniciar o Flask local, a porta 5000 recusou conexão; depois de iniciá-lo, ambos responderam `400` a payloads deliberadamente inválidos, em vez de `404`. A URL pública do Codespace não foi confirmada: uma sondagem sem sessão recebeu `401`, portanto a origem exata dos `404` vistos no navegador permanece desconhecida.

---

# 1. IDENTIFICAÇÃO DO PROJETO

| Campo | Informação confirmada |
|---|---|
| Nome do projeto | Gerenciamento de empréstimo de livros de biblioteca |
| Nome apresentado pela aplicação | Biblioteca Narceu de Paiva Filho |
| Contexto | Biblioteca escolar, conforme README e código |
| Local citado | Campus Aracruz, conforme README e `database.sql` |
| Escola | O nome institucional completo não foi confirmado além da identificação usada no projeto |
| Governo/secretaria | Não foi possível confirmar esta informação no estado atual do projeto. |
| SRE | Não foi possível confirmar esta informação no estado atual do projeto. |
| Série/turma do estudante | Não foi possível confirmar esta informação no estado atual do projeto. |
| Estudante responsável | Não foi possível confirmar esta informação no estado atual do projeto. |
| Professor orientador | Não foi possível confirmar esta informação no estado atual do projeto. |
| Tipo de sistema | Aplicação web para acervo e circulação de biblioteca |
| Data desta análise | 02/10/2026 |

Este arquivo se chama `TCC_valibe.md` por solicitação do usuário, mas seu propósito é ser um guia técnico e de estudo do projeto. Ele não deve ser usado como prova de que o projeto é um TCC, nem como prova de dados institucionais que não estão confirmados.

---

# 2. RESUMO DO PROJETO

## 2.1 Problema

O contexto informado nos documentos do projeto descreve um controle anterior feito manualmente em papel, com listas de alunos, livros e datas. À medida que a lista cresceu, tornou-se mais difícil registrar, consultar e atualizar empréstimos, devoluções e a localização dos livros.

Não foram encontrados números confiáveis no código atual que permitam informar a quantidade de livros, alunos ou empréstimos do ambiente real.

## 2.2 Solução criada

O projeto criou uma aplicação web composta por:

- frontend em HTML, CSS e JavaScript sem framework;
- backend em Python com Flask;
- APIs HTTP organizadas por blueprints;
- Supabase/PostgreSQL como caminho principal de persistência previsto;
- arquivos JSON locais usados por vários módulos como fallback interno;
- cadastro de livros, alunos, salas e gêneros;
- controle de empréstimos, devoluções e renovações;
- consultas de ISBN;
- QR Codes e scanner;
- relatórios gráficos e exportações CSV;
- login tradicional e login por QR Code.

## 2.3 Usuários

Os perfis observados no código são:

- administrador;
- bibliotecário;
- aluno com `is_librarian`, que pode receber acesso limitado pela interface.

O backend calcula papéis no login, mas não há middleware que obrigue as chamadas posteriores da API a enviarem uma sessão, token ou papel válido. Portanto, o controle de papéis está comprovadamente forte na interface, mas não foi comprovado como autorização server-side para todas as rotas.

## 2.4 Resultados comprovados

- A aplicação Flask inicia e serve o frontend.
- O endpoint `/api/health` respondeu com banco `conectado` durante a análise.
- Os testes específicos de ISBN/Vision passaram na análise inicial: `24 passed`; na atualização de 04/10 foram `25 passed`.
- Os dois testes JavaScript executados passaram:
  - `books ISBN form test passed`;
  - `qr-scanner callback test passed`.
- A suíte completa Python em 04/10 terminou com `32 passed, 6 failed, 3 warnings`; ver a seção 25.2 atualizada.
- Uma chamada isolada real ao Vision reconheceu o ISBN de um frame sintético. A leitura por câmera física continua não confirmada.

## 2.5 Limitações principais

- A suíte completa ainda possui sete falhas de testes antigos ou dependentes do ambiente.
- A câmera física não foi validada neste ambiente.
- A leitura real de um ISBN por câmera não foi comprovada com uma imagem física de código de barras.
- O fallback backend de barcode depende da biblioteca nativa `zbar`, que não estava instalada no ambiente do agente.
- O acesso aos papéis não é aplicado de forma consistente no backend.
- O deploy em produção/Render não foi confirmado.
- Não existe reconciliação automática confirmada entre JSON local e Supabase.
- A conta Groq precisa ter um modelo Vision habilitado para o fluxo Vision funcionar em imagens com ISBN.

## 2.6 Resumo Executivo para o relatório escolar, em até 10 linhas

O projeto é uma aplicação web para organizar o acervo e os empréstimos de uma biblioteca escolar. Antes dele, o controle era feito manualmente em papel, dificultando consultar alunos, livros, datas e devoluções. A solução usa frontend em HTML, CSS e JavaScript, backend em Python/Flask e Supabase/PostgreSQL como banco principal. O sistema possui cadastros de livros, alunos, salas e gêneros, empréstimos, devoluções, renovações, QR Codes, consulta de ISBN e relatórios. O código também possui caminhos JSON locais em vários módulos. Os testes de ISBN e frontend passaram, mas a suíte completa ainda tem falhas de ambiente e testes desatualizados. Não foi possível confirmar deploy de produção nem autorização server-side completa.

---

# 3. PROBLEMA E CONTEXTO

## 3.1 Problema original

O problema inicial documentado é a dependência de uma lista manual em papel. Esse processo pode registrar nomes, livros e datas, mas torna mais trabalhosas as operações repetidas:

- localizar rapidamente um livro;
- descobrir com quem um livro está;
- verificar se houve devolução;
- atualizar uma data;
- separar empréstimos ativos de devolvidos;
- conferir exemplares semelhantes;
- consultar históricos.

A aplicação procura transformar essas operações em registros estruturados, buscas e ações de interface.

## 3.2 Quem é afetado

### Alunos

Os alunos aparecem como pessoas relacionadas aos empréstimos. O sistema guarda nome, turma, carteirinha, sala e identificação interna. Também é possível marcar um aluno como bibliotecário pelo campo `is_librarian`.

### Bibliotecários

O código usa o papel bibliotecário para limitar visualmente a interface a Painel, Empréstimos e Acervo. O bibliotecário participa da identificação de alunos, escolha de livros, registro de empréstimos, devoluções e renovações.

### Administração da biblioteca

O administrador aparece no login, nas telas de cadastro e na configuração. O frontend mostra mais áreas para o administrador, como alunos, salas, gêneros e relatórios.

### Escola

A escola é afetada porque o sistema centraliza informações da circulação do acervo e oferece visualizações de atrasos, turmas e livros. Não foram encontrados indicadores confiáveis de impacto institucional medido.

## 3.3 Consequências do controle manual

Com base no contexto fornecido, as consequências são dificuldades de:

- registrar dados sem repetição;
- consultar uma informação antiga;
- atualizar o estado do empréstimo;
- saber se um exemplar está disponível;
- identificar o aluno responsável;
- controlar prazo e atraso;
- produzir relatórios.

O projeto não fornece uma medição quantitativa dessas consequências. **Não foi possível confirmar esta informação no estado atual do projeto.**

---

# 4. OBJETIVOS

## 4.1 Objetivo geral

Organizar digitalmente o acervo e a circulação de livros de uma biblioteca escolar, permitindo cadastrar livros e alunos, registrar empréstimos, controlar devoluções e consultar a situação dos exemplares.

Esse objetivo é sustentado pelos módulos Flask, pelas telas de cadastro e empréstimo, pelo esquema SQL e pelos endpoints observados.

## 4.2 Objetivos específicos

### Organização dos empréstimos

**Objetivo:** registrar quem pegou qual livro/exemplar e em qual data.

**Como o sistema tenta atender:** `create_loan()` confirma aluno e livro, escolhe um exemplar disponível e calcula a data prevista.

**Funcionalidade relacionada:** `POST /api/loans/`, tela de novo empréstimo e tabela de empréstimos.

**Como demonstrar:** selecionar um livro, selecionar um aluno, escolher o prazo e confirmar a operação.

### Facilidade na realização de empréstimos

**Objetivo:** reduzir a quantidade de digitação no balcão.

**Como o sistema tenta atender:** permite localizar livro por título, autor, ISBN, ID ou QR; permite localizar aluno por nome, ID, carteirinha ou QR.

**Funcionalidade relacionada:** `loans.js`, `app.js`, `qr-scanner.js` e os endpoints de busca.

**Como demonstrar:** localizar o livro, ler a carteirinha, selecionar exemplar e confirmar.

### Melhoria da consulta de empréstimos

**Objetivo:** mostrar registros ativos, atrasados e devolvidos.

**Como o sistema tenta atender:** `loan_status()` calcula `active`, `overdue` e `returned`; a interface possui filtros e painel.

**Funcionalidade relacionada:** `GET /api/loans/`, `renderLoans()` e `renderDashboard()`.

**Como demonstrar:** abrir a lista de empréstimos e filtrar cada status.

### Facilidade de busca de livros

**Objetivo:** encontrar um livro sem depender de uma lista manual.

**Como o sistema tenta atender:** filtro por título, autor, ISBN e início do ID; consulta de ISBN em fontes externas.

**Funcionalidade relacionada:** `renderBooks()`, `lookupBookIsbn()`, `GET /api/books/` e `GET /api/books/isbn-lookup`.

**Como demonstrar:** pesquisar por texto e consultar um ISBN válido.

### Organização de livros e alunos

**Objetivo:** manter informações estruturadas do acervo e dos usuários da biblioteca.

**Como o sistema tenta atender:** CRUD de livros e alunos, salas, gêneros, carteirinhas, UUIDs e importação CSV.

**Funcionalidade relacionada:** `books.py`, `students.py`, `rooms.py`, `genres.py` e as páginas correspondentes.

**Como demonstrar:** cadastrar, editar, consultar e excluir registros respeitando as validações observadas.

---

# 5. METODOLOGIA DE DESENVOLVIMENTO

## 5.1 O que é comprovado

O histórico Git mostra uma sequência de commits de correção e melhoria. Os commits tratam, entre outros assuntos, de ISBN, Groq, scanner, login, QR, relatórios, identificadores e desempenho.

O desenvolvimento aparenta ter sido iterativo: uma parte foi implementada, testada, corrigida e novamente ajustada. Essa conclusão vem do histórico de commits e da presença de testes específicos.

O projeto foi analisado como trabalho individual porque o material fornecido descreve esse contexto. Não foram encontrados arquivos comprovando uma equipe formal ou divisão de integrantes.

## 5.2 Ferramentas observadas

- Python e Flask;
- JavaScript sem framework;
- Supabase/PostgreSQL;
- Git e GitHub, evidenciados pelo repositório e histórico;
- testes Python com pytest;
- testes JavaScript executados com Node;
- editor/ambiente Codespace;
- Copilot/assistência de IA aparece no contexto de desenvolvimento desta análise, mas não há prova de que toda a aplicação tenha sido produzida por IA.

## 5.3 Como os problemas eram identificados

Os problemas eram observados por:

- leitura do código;
- execução de testes;
- chamadas reais às rotas;
- leitura de logs;
- comparação entre código, SQL e documentação;
- commits de correção.

## 5.4 Por que não chamar simplesmente de metodologia ágil?

### Desenvolvimento iterativo

Significa trabalhar em ciclos de alteração, teste e correção. O histórico confirma mudanças incrementais.

### Metodologia ágil formal

Scrum, Kanban ou outra metodologia formal exigiria evidências como papéis, cerimônias, backlog, sprints, quadro ou registros de planejamento. Isso não foi confirmado.

### Desenvolvimento assistido por IA

Pode envolver uso de Copilot para explorar, escrever ou corrigir código. Isso não substitui revisão, testes e responsabilidade do desenvolvedor.

### Trabalho individual

Um projeto individual pode ser iterativo e usar ferramentas de IA sem ser automaticamente Scrum, Kanban ou outra metodologia formal.

A descrição mais honesta é: **desenvolvimento individual e iterativo, apoiado por Git/GitHub, testes e assistência de ferramentas de IA quando documentada, sem metodologia formal confirmada.**

## 5.5 Histórico Git atual

O histórico atual do branch analisado mostra commits relacionados a estas áreas:

| Commit | Mensagem resumida observada |
|---|---|
| `d9d64cf` | estado atual do branch, com observação sobre Groq |
| `89d0610` | ajuste da busca ISBN para diferentes fontes e fallback |
| `5ae289e` | atualização do projeto |
| `9832b8d` | adição de modelos/tipos compartilhados |
| `0812e30` | adição da dependência Groq |
| `099148c` | atualização da integração de ISBN com Groq |
| `d4de83c` | correção do preenchimento de título, autor e área |
| `60f045f` | relatório técnico abrangente do estado do sistema |
| `6824b2f` | atualização de relatórios |
| `d8a6a9f` | validação ISBN, fallback e tratamento de erros |
| `3ccc4a4` | normalização de categorias e preenchimento de cadastro |
| `c3cb933` | ajuste do cartão administrativo |

As mensagens dos commits são evidências do histórico de mudanças, não substituem a leitura do código atual. Não foi possível confirmar pelo histórico sozinho se todas as descrições antigas continuam representando o comportamento atual.

---

# 6. ARQUITETURA DO SISTEMA

## 6.1 Visão geral

```text
NAVEGADOR
   |
   v
FRONTEND
HTML + CSS + JavaScript
   |
   | fetch() / HTTP / JSON
   v
FLASK
app.py + Blueprints
   |
   v
REGRAS DO SISTEMA
livros, alunos, empréstimos, ISBN, QR e relatórios
   |
   +----------------------+
   |                      |
   v                      v
SUPABASE / POSTGRESQL     JSON LOCAL
caminho principal         fallback interno de módulos
```

## 6.2 Frontend

O frontend é a camada que roda no navegador.

### HTML

`frontend/index.html` define login, menu lateral, páginas, tabelas, modais e formulários. A aplicação usa uma estrutura de SPA simples: vários blocos `.page` existem no mesmo documento e `app.js` alterna qual aparece.

### CSS

`frontend/assets/css/main.css` contém estilos, responsividade, temas, tabelas, botões, cards, modais, câmera e estados visuais.

### JavaScript

O JavaScript:

- escuta cliques e eventos de formulário;
- chama `fetch` por meio de `api.js`;
- mantém dados no `Store`;
- renderiza tabelas e cartões;
- controla login e navegação;
- abre a câmera;
- desenha gráficos com Chart.js.

### Páginas

Os arquivos em `frontend/assets/js/pages/` concentram a lógica visual de livros, alunos, empréstimos, salas e gêneros.

## 6.3 Backend

O backend é Python com Flask.

### Flask

`app.py` cria a aplicação, carrega ambiente, registra CORS, registra blueprints, aplica headers e serve o frontend.

### Blueprints

Blueprint é uma forma de dividir rotas por módulo:

- `auth_bp` para autenticação;
- `books_bp` para livros;
- `students_bp` para alunos;
- `loans_bp` para empréstimos;
- `reports_bp` para relatórios;
- `rooms_bp` para salas;
- `genres_bp` para gêneros;
- `qr_bp` para scanner, QR e cartões.

### JSON

As rotas retornam JSON com `jsonify`, exceto exportações que retornam CSV.

### Validação

Existe validação de campos obrigatórios, ISBN, datas calculadas, existência de aluno/livro e disponibilidade de exemplar. Não existe uma camada uniforme de schemas ou validação tipada para todos os payloads.

## 6.4 Banco

O SQL descreve PostgreSQL acessado pelo Supabase. As tabelas usam UUID, foreign keys, índices, constraints e JSONB. O backend Python não abre uma conexão PostgreSQL direta; utiliza o cliente Supabase.

## 6.5 Comunicação

```text
Usuário
  |
  v
Evento no navegador
  |
  v
API.books / API.loans / API.students
  |
  v
apiFetch()
  |
  v
HTTP JSON
  |
  v
Rota Flask
  |
  v
Função do módulo
  |
  v
Supabase ou JSON local
  |
  v
Resposta JSON/CSV
  |
  v
Store + renderização da tela
```

---

# 7. ESTRUTURA DE PASTAS

```text
projeto/
├── backend/
│   ├── app.py
│   ├── README.md
│   ├── requirements.txt
│   ├── .env.example
│   ├── api/
│   │   ├── __init__.py
│   │   ├── _helpers.py
│   │   ├── auth.py
│   │   ├── books.py
│   │   ├── genres.py
│   │   ├── loans.py
│   │   ├── reports.py
│   │   ├── rooms.py
│   │   └── students.py
│   ├── data/
│   │   ├── alunos.json
│   │   ├── emprestimos.json
│   │   ├── generos.json
│   │   ├── livros.json
│   │   └── salas.json
│   ├── scanner/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── tests/
│   └── utils/
│       ├── __init__.py
│       ├── helpers.py
│       └── supabase_client.py
├── frontend/
│   ├── index.html
│   ├── assets/
│   │   ├── css/main.css
│   │   └── js/
│   │       ├── api.js
│   │       ├── app.js
│   │       ├── charts.js
│   │       ├── qr-scanner.js
│   │       ├── store.js
│   │       ├── utils.js
│   │       ├── lib/supabase-config.js
│   │       └── pages/
│   └── tests/
├── database.sql
├── requirements.txt
└── documentação histórica em arquivos Markdown
```

### Função das pastas

- `backend/api`: regras HTTP de cada domínio.
- `backend/scanner`: leitura, resolução e geração de QR/cartões.
- `backend/utils`: cliente Supabase e funções gerais.
- `backend/data`: dados JSON presentes no repositório.
- `backend/tests`: testes Python.
- `frontend/assets/js`: código do navegador.
- `frontend/assets/css`: estilo da aplicação.
- `frontend/tests`: testes JavaScript.
- raiz: SQL, requisitos, documentação e relatórios históricos.

Não há `package.json`, `pyproject.toml`, `Dockerfile`, `Procfile` ou `render.yaml` na árvore atual analisada.

---

# 8. TECNOLOGIAS UTILIZADAS

| Tecnologia | Onde aparece | Função | Usada como planejado? | Evidência |
|---|---|---|---|---|
| Python | `backend/**/*.py` | Backend e testes | Sim, no backend | Imports e execução Flask/pytest |
| Flask | `backend/app.py` | Servidor HTTP e rotas | Sim | `Flask`, blueprints e `app.run` |
| Flask-CORS | `backend/app.py` | CORS para APIs | Sim | `CORS(app, resources=...)` |
| python-dotenv | `backend/app.py` | Carregar `.env` | Parcial | `load_dotenv`; ambiente atual usa Secrets |
| Supabase | `backend/utils/supabase_client.py` | Persistência remota | Sim no caminho principal | Cliente e consultas `.table()` |
| PostgreSQL | `database.sql` | Banco descrito pelo Supabase | Sim no esquema | SQL, UUID, FKs, views e JSONB |
| HTML | `frontend/index.html` | Estrutura visual | Sim | Telas e formulários |
| CSS | `frontend/assets/css/main.css` | Estilos | Sim | Folha carregada pelo HTML |
| JavaScript vanilla | `frontend/assets/js/` | Interface e eventos | Sim | Arquivos sem framework |
| Chart.js | CDN e `charts.js` | Gráficos | Sim | `new Chart(...)` |
| jsQR | CDN e `qr-scanner.js` | Leitura de QR no navegador | Sim quando disponível | `window.jsQR` |
| BarcodeDetector | API nativa | Barcode/QR no navegador | Condicional | `new window.BarcodeDetector` |
| Tabler Icons | CDN no HTML | Ícones | Sim | folha de ícones e classes `ti-*` |
| OpenCV | requirements e scanner | Processamento/QR/barcode | Parcial/condicional | `cv2` em `routes.py`; dependência nativa exigida pelo ambiente |
| PyZbar | requirements e scanner | Decodificação barcode/QR | Parcial/condicional | `_decode_barcode_variants`; requer `libzbar0` |
| Pillow | requirements e scanner | Imagens e cartões | Sim no código | `Image`, `ImageDraw` |
| qrcode | requirements e scanner/books | Geração de QR | Sim | `QRCode(...)` |
| NumPy | requirements e scanner | Matriz de imagem | Sim no scanner | `np.array` |
| Passlib | requirements e auth | Hash/verificação | Condicional | `_pwd_ctx` |
| bcrypt | requirements e auth | Verificação alternativa | Condicional | `bcrypt.checkpw` |
| crypt | Python/passlib/auth | Hash Unix e testes | Condicional | `unix_crypt` |
| OpenAI SDK | `books.py` | Cliente compatível com Groq | Sim | `OpenAI(base_url=...)` |
| Groq | `books.py` e Secrets | Metadados e Vision | Parcial | `_groq_lookup`, `_groq_isbn_from_image` |
| Gunicorn | requirements | Possível servidor produção | Não confirmado | Dependência sem configuração encontrada |
| Node.js | testes JS executados | Runner de testes | Sim nos testes | comandos `node frontend/tests/*.js` |
| Render | documentos antigos | Possível deploy | Não confirmado | sem configuração operacional atual |

---

# 9. BANCO DE DADOS

## 9.1 Tabela `usuarios`

Função: armazenar contas de login.

Campos observados no SQL:

- `id`: UUID e chave primária;
- `nome`;
- `login`: único;
- `senha`;
- `criado_em`.

O backend atual consulta esta tabela em `_get_user_by_login()`. O SQL fornecido possui seeds, mas o estado real do banco remoto não deve ser deduzido apenas pelo arquivo.

## 9.2 Tabela `salas`

Representa salas ou ambientes escolares.

- `id` UUID;
- `nome`;
- `codigo`;
- `descricao`;
- `capacidade`;
- `criado_em`.

Alunos podem apontar para uma sala por `sala_id`. A foreign key usa `ON DELETE SET NULL`.

## 9.3 Tabela `generos`

Representa categorias internas de livros.

- `id` UUID;
- `nome`;
- `icone`;
- `cor`;
- `criado_em`.

Livros apontam para gêneros por `genero_id`.

## 9.4 Tabela `livros`

Representa obras cadastradas.

- `id` UUID;
- `isbn`;
- `titulo`;
- `autor`;
- `area`;
- `genero_id`;
- `exemplares`;
- `qr_id` no SQL;
- `exemplares_ids` JSONB;
- `exemplares_meta` JSONB;
- `criado_em`.

O código atual usa `id`, `isbn`, título, autor, área, gênero e metadados de exemplares. O campo `qr_id` aparece no SQL, mas não é o campo principal usado nas funções de criação de QR observadas.

## 9.5 Tabela `alunos`

Representa usuários que podem participar dos empréstimos.

- `id` UUID;
- `nome`;
- `turma`;
- `carteirinha`;
- `sala_id`;
- `qr_id` no SQL;
- `is_librarian`;
- `deleted_at`;
- `criado_em`.

O backend usa `id` e `carteirinha` para resolver alunos; o QR gerado no cadastro contém o ID.

## 9.6 Tabela `emprestimos`

Relaciona aluno, livro e exemplar.

- `id` UUID;
- `livro_id`;
- `aluno_id`;
- `exemplar`;
- `exemplar_id`;
- `data_emprestimo`;
- `data_devolucao_prevista`;
- `devolvido_em`;
- `observacao`;
- `criado_por`;
- `renovacoes`;
- `criado_em`.

O índice parcial `idx_exemplar_ativo` procura impedir o mesmo livro/exemplar em dois empréstimos ativos.

## 9.7 Tabela `relatorios_mensais`

Guarda resultados mensais agregados:

- mês/ano único;
- totais de empréstimos, devoluções e atrasos;
- rankings em JSONB;
- data e autor da geração.

## 9.8 Chaves, índices e constraints

- Chave primária identifica cada linha.
- UUID reduz dependência de IDs sequenciais.
- Foreign key mantém referências entre entidades.
- `ON DELETE SET NULL` preserva aluno/livro quando sala/gênero é removido.
- `ON DELETE CASCADE` pode remover empréstimos associados quando livro/aluno é apagado, conforme SQL.
- Índices aceleram ISBN, título, área, nome, turma e relacionamentos.
- Unique parcial evita carteirinhas ou QR duplicados quando preenchidos.
- Check constraints controlam quantidade de exemplares e renovações.

## 9.9 RLS e policies

O SQL habilita Row Level Security. O arquivo possui policies amplas para diversas tabelas, inclusive `USING (true)`. Isso permite acesso amplo para o papel que consegue usar a policy, mas a aplicação também utiliza uma chave de serviço no backend.

Não foi possível confirmar a configuração efetiva do banco remoto. O relatório não assume que o SQL atual já foi executado exatamente como está.

## 9.10 Views

`vw_emprestimos_ativos` junta empréstimos, livros, alunos, gêneros e salas, calculando atraso/status.

`vw_livros_ranking` agrupa empréstimos por livro e calcula totais, ativos e disponíveis.

O backend de relatórios atual calcula agregações em Python em vez de depender diretamente dessas views.

---

# 10. CADASTRO DE LIVROS

## 10.1 Fluxo completo

```text
Usuário
  |
  v
Abre Acervo
  |
  v
Clica em Cadastrar livro
  |
  v
Modal de cadastro
  |
  +--> digita ISBN
  |       |
  |       v
  |   consulta manual
  |
  +--> clica em Ler
          |
          v
      câmera/scanner
          |
          v
      ISBN ou código lido
          |
          v
      consulta de metadados
          |
          v
Título, autor, gênero e área preenchidos
  |
  v
Usuário confere os dados
  |
  v
Clica em Salvar
  |
  v
POST /api/books/
  |
  v
backend valida título/autor
  |
  v
new_id() cria UUID do livro
  |
  v
_build_exemplar_meta() cria exemplares
  |
  v
QR do livro é gerado
  |
  v
Supabase ou caminho JSON interno
  |
  v
frontend sincroniza e mostra acervo
```

## 10.2 Frontend

`index.html` contém o modal `modal-book` com:

- `book-isbn`;
- `book-title`;
- `book-author`;
- `book-genre`;
- `book-area`;
- `book-copies`;
- botão `Ler`;
- botão `Pesquisar`;
- botão `Salvar`.

`books.js` contém:

- `openAddBook()` para limpar e abrir o modal;
- `editBook()` para carregar dados existentes;
- `lookupBookIsbn()` para pesquisa manual;
- `scanBookIsbn()` para câmera no cadastro;
- `applyBookLookupResult()` para preencher campos;
- `saveBook()` para criar/editar;
- `showExemplares()` para exibir cópias;
- `showEntityQR()` e `printCard()` para recursos de QR/cartões.

## 10.3 Backend

`create_book()` valida título e autor, cria UUID, monta payload e chama `_build_exemplar_meta()`.

`_build_exemplar_meta()` gera, para cada cópia:

- código legível, como `001`;
- identificador de exemplar;
- `qr_data` interno.

Depois o backend tenta gerar uma imagem QR em base64 e devolve o registro.

## 10.4 Evidência e limite

O código comprova o fluxo de cadastro e as validações unitárias de ISBN/identificadores. Não foi executado um teste E2E de navegador criando um livro em banco remoto durante esta análise.

---

# 11. ISBN — EXPLICAÇÃO COMPLETA

## 11.1 O que é ISBN

ISBN é um identificador bibliográfico usado para diferenciar uma edição de livro. Ele não é o ID técnico do registro no sistema.

```text
ISBN: identidade bibliográfica externa
UUID do livro: identidade interna do sistema
ID do exemplar: identidade de uma cópia específica
QR: representação visual de um texto, normalmente um ID
```

## 11.2 ISBN-10 e ISBN-13

ISBN-10 tem dez posições e pode usar `X` como dígito final. ISBN-13 tem treze dígitos e usa pesos alternados 1 e 3 no cálculo do checksum.

## 11.3 `_normalize_isbn()`

A função:

```python
re.sub(r"[^0-9Xx]", "", str(value or "")).upper()
```

faz três coisas:

1. converte `None` para texto vazio;
2. remove hífens, espaços e outros caracteres;
3. transforma `x` em `X`.

Exemplo:

```text
978-85-3251-101-0
        |
        v
9788532511010
```

A função não decide se o checksum está correto; ela apenas normaliza.

## 11.4 `_validate_isbn()`

Para ISBN-10:

- exige nove dígitos e um último dígito ou `X`;
- multiplica as posições por pesos de 10 até 1;
- aceita se a soma for divisível por 11.

Para ISBN-13:

- exige treze caracteres numéricos;
- usa peso 1 nas posições pares e 3 nas ímpares;
- aceita se a soma for divisível por 10.

ISBN inválido lança `ValueError`. O endpoint converte esse erro em HTTP 400.

## 11.5 Cache e validação

A normalização acontece antes da consulta. O cache usa o ISBN normalizado como chave. O TTL atual é de quinze minutos e o limite é 128 entradas.

---

# 12. INTEGRAÇÕES DE ISBN

| Fonte | Endpoint usado | Função | Dados obtidos | Papel |
|---|---|---|---|---|
| Google Books | `https://www.googleapis.com/books/v1/volumes?q=isbn:<isbn>` | `_google_books_lookup()` | ISBN, título, autores, categorias | Primeira fonte bibliográfica |
| ISBNsearch | `https://isbnsearch.org/isbn/<isbn>` | `_isbnsearch_lookup()` | Título, autor interpretado do HTML | Segunda fonte |
| Open Library | `https://openlibrary.org/api/books?bibkeys=ISBN:<isbn>&jscmd=data&format=json` | `_openlibrary_lookup()` | Título, autores, subjects/categorias | Terceira fonte |
| Groq texto | `https://api.groq.com/openai/v1` via SDK OpenAI | `_groq_lookup()` | Sugestão de ISBN, título, autor e categorias | Pesquisa inicial/fallback no modo scanner |
| Groq Vision | mesma base URL via SDK OpenAI | `_groq_isbn_from_image()` | ISBN extraído da imagem | Imagem -> ISBN no cadastro |

## 12.1 Google Books

A função envia o ISBN normalizado, escolhe o primeiro item retornado, extrai `volumeInfo` e procura identificadores ISBN-13/ISBN-10. Se não houver dados úteis, lança `LookupError`.

## 12.2 ISBNsearch

A função requisita HTML, usa `_IsbnSearchParser` e extrai o título da tag `<title>` e autor de elementos de texto com rótulo `Author` ou `Authors`. Como depende de HTML externo, mudanças no site podem quebrar a extração.

## 12.3 Open Library

A função interpreta o objeto referente a `ISBN:<isbn>`, coleta autores e subjects. Se não houver título, autor ou categorias, considera não encontrado.

## 12.4 Combinação

As três fontes bibliográficas são executadas em paralelo por `ThreadPoolExecutor`. O código coleta todas as respostas antes de combinar.

Para título/autor:

- valor repetido por duas fontes vence por consenso;
- sem consenso, a ordem é Google Books, ISBNsearch, Open Library;
- Groq é fallback somente quando nenhuma fonte fornece o campo.

Para categorias:

- categorias bibliográficas são combinadas sem duplicatas normalizadas;
- categorias do Groq só entram quando não há categoria bibliográfica.

---

# 13. GROQ

## 13.1 O que é

Groq é o provedor externo usado pelo projeto por meio de uma API compatível com o formato da OpenAI. O código importa `OpenAI` do SDK e altera o `base_url` para `https://api.groq.com/openai/v1`.

## 13.2 Credencial

O backend procura uma chave nesta ordem:

```text
GROQ_API_KEY
API_GROQ
GROQ_API
```

A chave não é colocada no frontend. O frontend apenas chama endpoints do backend.

## 13.3 Groq textual

`_groq_lookup(isbn)` recebe ISBN, normaliza, valida, envia uma instrução para responder JSON e interpreta título, autor e categorias.

Modelo textual:

```python
_GROQ_DEFAULT_MODEL = "allam-2-7b"
```

Pode ser substituído por `GROQ_MODEL`.

## 13.4 Groq Vision

`_groq_isbn_from_image(image_data)` recebe um Data URL de imagem, decodifica base64, verifica tamanho máximo de 2 MB e envia uma mensagem multimodal com texto e `image_url`.

Modelo padrão:

```python
_GROQ_DEFAULT_VISION_MODEL = "qwen/qwen3.8-27b"
```

Pode ser substituído por:

```text
GROQ_VISION_MODEL
```

Resposta esperada:

```json
{"encontrado": true, "isbn": "9788532511010"}
```

ou:

```json
{"encontrado": false, "isbn": ""}
```

## 13.5 Estados

### Implementado

- endpoint `POST /api/books/isbn-vision`;
- recebimento temporário de frame;
- validação de base64/tamanho;
- chamada de modelo configurável;
- normalização/validação do ISBN;
- consulta bibliográfica posterior;
- cancelamento no frontend;
- teste unitário de resposta válida, vazia e inválida.

### Comprovado parcialmente

Um frame branco válido de 100x100 retornou corretamente `encontrado: false`. Isso confirma a comunicação e o formato da resposta, mas não prova a precisão com uma fotografia real de ISBN.

### Não confirmado

- leitura confiável de vários tipos de foto;
- funcionamento com câmera física;
- disponibilidade do modelo em todas as contas Groq;
- precisão do modelo para um código de barras desfocado;
- desempenho em rede de produção.

---

# 14. SCANNER E CÂMERA

## 14.1 Scanner do navegador

`qr-scanner.js`:

1. constrói um modal de câmera;
2. solicita `getUserMedia`;
3. tenta câmera traseira, frontal e alternativas;
4. enumera câmeras;
5. aplica foco contínuo quando o dispositivo anuncia suporte;
6. captura frames em canvas a cada aproximadamente 700 ms;
7. tenta `jsQR`;
8. tenta `BarcodeDetector` com `qr_code`, `code_128`, `ean_13`, `ean_8`, `upc_a` e `upc_e`;
9. chama `/api/qr/decode` como fallback;
10. dispara callback e para a câmera quando encontra algo.

## 14.2 Scanner no cadastro de livro

No cadastro, `scanBookIsbn()` fornece um `frameHandler` opcional ao `QRScanner`.

```text
Cadastro de livro
  |
  v
scanBookIsbn()
  |
  v
QRScanner.start(..., frameHandler)
  |
  v
canvas -> JPEG temporário
  |
  v
POST /api/books/isbn-vision
  |
  v
Groq Vision -> ISBN
  |
  v
GET lógico interno de dados bibliográficos
  |
  v
formulário preenchido
```

O Vision é restrito ao fluxo do cadastro porque os demais chamadores de `QRScanner.start()` não recebem `frameHandler`.

## 14.3 Scanner backend

`/api/qr/decode` recebe imagem base64 ou arquivo. Ele usa Pillow para abrir, OpenCV/NumPy para converter e PyZbar para tentativas com múltiplas variantes: original, grayscale, ampliada, sharpened, CLAHE, threshold e adaptive threshold. Se falhar, tenta `QRCodeDetector` do OpenCV.

## 14.4 QR Code x código de barras

- QR Code é bidimensional e pode conter texto/IDs.
- Código de barras EAN/UPC é normalmente unidimensional e usado para números como ISBN-13.
- `jsQR` foi criado para QR e não substitui um decodificador EAN.
- `BarcodeDetector` pode suportar EAN quando o navegador oferece esse formato.
- PyZbar depende da biblioteca nativa `zbar` para o fallback backend.

## 14.5 O que foi realmente testado

O teste JavaScript valida o callback básico do scanner. O backend foi carregado com suas dependências no `.venv312`. Não foi possível confirmar uma leitura física de barcode em câmera real nesta análise.

---

# 15. QR CODES

## 15.1 QR de livro

O cadastro de livro gera QR com o ID do livro por meio da geração automática. A resolução aceita ID e ISBN em alguns caminhos.

## 15.2 QR de exemplar

O exemplar possui `id`, `code` e `qr_data` no `exemplares_meta`. O formato interno observado começa com `EXEMPLAR-` e inclui referência do livro, código e identificador único. Esse QR individual também é obrigatório para confirmar a devolução do empréstimo correspondente. Para livros sem metadados de exemplares, a geração de cartões cria um código individual por cópia; cartões antigos com QR genérico devem ser reimpressos.

## 15.3 QR de aluno

O cadastro gera QR com o UUID do aluno. A resolução procura pelo ID ou carteirinha.

## 15.4 QR administrativo

O código inicia com `ADMIN-`. O backend identifica o login e exige senha no endpoint `/api/qr/login`.

## 15.5 Diferenças importantes

| Conceito | Função |
|---|---|
| ISBN | Identidade bibliográfica de uma edição |
| ID do livro | UUID interno do registro da obra |
| ID do exemplar | Identidade de uma cópia específica |
| QR Code | Imagem que armazena um texto, geralmente um ID ou prefixo especial |

---

# 16. EMPRÉSTIMOS

## 16.1 Fluxo real

```text
Usuário escolhe livro
  |
  v
Frontend localiza livro/ID/exemplar
  |
  v
Usuário escolhe aluno
  |
  v
Frontend envia livro_id + aluno_id + prazo
  |
  v
POST /api/loans/
  |
  v
Backend confirma livro
  |
  v
Calcula exemplares disponíveis
  |
  v
Escolhe exemplar
  |
  v
Confirma aluno
  |
  v
Calcula vencimento
  |
  v
Insere empréstimo
  |
  v
Frontend sincroniza e renderiza
```

## 16.2 Aluno

`_find_student_by_ref()` procura por ID, depois carteirinha e finalmente JSON local.

## 16.3 Livro e exemplar

O backend busca o livro, lê `exemplares`/`exemplares_ids`, remove exemplares usados em empréstimos ativos e retorna os disponíveis. O usuário pode escolher um código específico; se não escolher, o primeiro disponível é usado.

## 16.4 Data e status

`today_str()` fornece a data atual. `add_days()` calcula vencimento. `loan_status()` classifica o empréstimo.

## 16.5 Devolução

`openDevolution()` abre o modal de confirmação com o botão desabilitado. A pessoa precisa ler o QR individual do exemplar emprestado; o frontend confere o livro e o número do exemplar antes de liberar a confirmação. `return_loan()` exige o campo `exemplar_qr` e valida também o identificador do exemplar no backend: QR ausente retorna HTTP 400 e QR divergente retorna HTTP 403. Somente após essa validação a rota grava a data e a observação da devolução. A conferência de aluno continua opcional e independente do QR obrigatório do livro.

## 16.6 Renovação

`renew_loan()` verifica se não está devolvido, soma dias à data atual de vencimento e incrementa `renovacoes`. Não há limite de renovação observado.

---

# 17. ALUNOS

O cadastro de aluno é feito por `saveStudent()` no frontend e `create_student()` no backend.

Campos:

- nome;
- turma;
- carteirinha;
- sala.

A turma é convertida para maiúscula. A carteirinha pode ser informada ou derivada do ID. O backend retorna QR em base64 quando consegue gerar a imagem.

A tela de alunos permite:

- busca;
- filtro por turma;
- filtro por sala;
- cadastro/edição/exclusão;
- importação CSV;
- histórico;
- geração de QR/carteirinha;
- habilitação/revogação de bibliotecário.

O campo `is_librarian` aparece na UI e no QR de aluno, mas não substitui uma política de autorização server-side.

---

# 18. USUÁRIOS E LOGIN

## 18.1 Fluxo

```text
Usuário preenche login e senha
  |
  v
app.js -> POST /api/auth/login
  |
  v
auth.py busca usuarios no Supabase
  |
  v
_verify_password()
  |
  +--> 401 se falhar
  |
  v
retorna access/login/name/id
  |
  v
app.js define currentUser e cookie
  |
  v
syncAll() e navegação
```

## 18.2 Backend

`_get_user_by_login()` aceita aliases de bibliotecário e consulta `usuarios`. `_verify_password()` tenta Passlib, senha legada, `crypt` e bcrypt conforme o formato.

## 18.3 Frontend

`doLogin()` envia a senha por HTTPS/HTTP conforme a URL usada, mostra mensagens e chama `_finishLogin()` quando o backend responde sucesso.

## 18.4 Frontend versus backend

### Frontend controla

- quais páginas aparecem;
- papel armazenado em `currentUser`;
- cookie de sessão do navegador;
- mensagens e navegação.

### Backend controla

- busca do usuário;
- comparação da senha;
- classificação da resposta de login;
- validações próprias de cada rota.

### Backend não protege atualmente

- não foi encontrado middleware de sessão;
- não foi encontrado JWT/Bearer;
- não foi encontrada verificação do papel em cada rota de negócio.

Portanto, esconder uma página não é o mesmo que proteger o endpoint.

---

# 19. GÊNEROS E CATEGORIAS

As APIs de ISBN retornam categorias externas. `_match_genre()` normaliza acentos, caixa e caracteres especiais, carrega gêneros locais e aplica aliases como:

- `history` -> História;
- `science fiction` -> Ficção Científica;
- `biography` -> Biografia;
- `textbook`/`technical` -> Técnico/Didático conforme o gênero local;
- `horror`/`thriller` -> Terror/Suspense.

O mecanismo usa comparação por inclusão de termos. Isso facilita correspondências, mas pode produzir associação ampla demais quando uma categoria contém outra palavra. Categorias externas são agregadas antes do matching.

---

# 20. RELATÓRIOS

## 20.1 Gráficos

`charts.js` constrói gráficos de:

- resumo de ativos, atrasados e devolvidos;
- livros mais emprestados;
- situação por turma;
- colunas de exportação.

Usa Chart.js carregado por CDN.

## 20.2 Relatórios mensais

`generate_monthly()` calcula por `mes_ano`:

- total de empréstimos;
- total de devoluções;
- total de atrasos;
- livros mais lidos;
- turmas mais ativas.

O payload tenta fazer `upsert` em `relatorios_mensais`.

## 20.3 CSV

Os endpoints geram CSV para:

- atrasados;
- histórico completo;
- livros mais emprestados;
- empréstimos por turma;
- situação dos alunos.

Não foram inventados números de relatórios.

---

# 21. CACHE E DESEMPENHO

## 21.1 Cache ISBN

- chave: ISBN normalizado;
- TTL: 15 minutos;
- limite: 128 registros;
- resultado incompleto não é armazenado;
- entradas antigas são removidas por ordem de uso.

O cache reduz chamadas repetidas às fontes externas.

## 21.2 Retry e timeout

Cada provedor externo usa timeout de seis segundos e até duas tentativas para falhas temporárias, incluindo códigos HTTP como 408, 429, 500, 502, 503 e 504 e falhas de rede observadas.

## 21.3 ThreadPoolExecutor

Google Books, ISBNsearch e Open Library são chamados em paralelo porque são fontes independentes. No modo scanner, Groq também é executado em paralelo com essas fontes quando o ISBN já está conhecido no fluxo textual; no fluxo Vision, primeiro se extrai o ISBN da imagem e depois as três fontes bibliográficas são consultadas.

## 21.4 Medições experimentais

Foram realizadas medições específicas, não garantias gerais:

- com Groq antes da paralelização: aproximadamente 2,261 s;
- sem Groq: aproximadamente 1,265 s;
- depois da paralelização e otimizações: manual aproximadamente 0,421 s;
- scanner aproximadamente 0,507 s.

Os tempos dependem de rede, provedores, banco, câmera e ambiente. Não devem ser apresentados como SLA.

## 21.5 Outros mecanismos de desempenho

O frontend usa `debounce()` e `renderScheduler` para evitar renderização a cada tecla em algumas listas. `Store` mantém snapshots em memória e `localStorage`, mas isso não equivale a sincronização oficial com o banco.

---

# 22. TRATAMENTO DE ERROS

## 22.1 Classes e respostas

- `ValueError`: entrada inválida, principalmente ISBN; endpoint retorna 400.
- `LookupError`: fonte não encontrou livro; endpoint retorna 404.
- `_ProviderError`: fonte externa falhou; em caminhos de consulta pode resultar em 502.
- `RuntimeError`: falha operacional geral; endpoint retorna 502.
- `HTTPException`: handler Flask retorna JSON com o código.
- exceção genérica: handler retorna 500 e registra log.

## 22.2 Provedores externos

```text
API externa
  |
  v
_open_provider / função específica
  |
  +--> retry/timeout
  |
  v
LookupError, _ProviderError ou resultado
  |
  v
_lookup_isbn / endpoint
  |
  v
JSON HTTP
  |
  v
apiFetch / mensagem na interface
```

## 22.3 Banco

`table_ok`, `is_offline_error` e blocos `try/except` permitem que módulos tentem JSON em várias operações. Porém, o `before_request` de `app.py` bloqueia quase todas as APIs de negócio quando não consegue consultar `livros`.

## 22.4 HTTP 429, 404 e timeout

O código de provedores trata 429 como potencialmente repetível e transforma falhas finais em `_ProviderError`. Um 404 de fonte pode virar `LookupError`. O comportamento real de cada provedor pode variar.

---

# 23. FALLBACK JSON

## 23.1 Por que existe

Os arquivos JSON permitem que módulos tenham uma alternativa quando uma consulta específica ao Supabase falha, especialmente em listagens e mutações que reconhecem `is_offline_error`.

## 23.2 Onde existe

- `backend/data/livros.json`;
- `backend/data/alunos.json`;
- `backend/data/emprestimos.json`;
- `backend/data/generos.json`;
- `backend/data/salas.json`.

## 23.3 Limites

Não há fila de sincronização, merge bidirecional, marcação de conflito ou upload posterior confirmados. Se uma escrita for feita localmente durante uma falha e o banco voltar depois, não há reconciliação automática observada.

Além disso, o `before_request` limita o uso offline pela interface porque exige confirmar Supabase em quase todas as APIs.

---

# 24. DEPLOYMENT

## Confirmado

- `app.py` pode iniciar servidor Flask em `0.0.0.0`.
- A porta pode vir de `PORT` ou `FLASK_PORT`.
- `gunicorn` está listado nas dependências.
- O frontend é servido pelo Flask.
- A execução local foi comprovada com o ambiente virtual.

## Não foi possível confirmar

- Procfile;
- Dockerfile;
- `render.yaml`;
- workflow ativo atual;
- comando Gunicorn em produção;
- URL de produção funcional;
- deploy ativo no Render;
- configuração de domínio/HTTPS;
- monitoramento de produção;
- permissões RLS do banco remoto.

Documentos antigos citam Render e workflows, mas não há esses arquivos na árvore real atual. Portanto, não são tratados como deployment atual confirmado.

---

# 25. TESTES

## 25.1 Tabela de testes

| Teste | Arquivo | O que verifica | Estado atual |
|---|---|---|---|
| Login admin/bibliotecário | `test_auth_librarian_login.py` | Verificação de senha, alias e fallback esperado | Falhas na execução completa por incompatibilidade com estado atual/mocks |
| Fallback de livros | `test_books_fallback.py` | Listagem quando Supabase falha | Executado na suíte geral; resultado individual não foi isolado nesta etapa |
| Performance de cartão | `test_card_generation_performance.py` | 20 cartões em menos de 1,5 s | Executado na suíte geral; dependente de qrcode/Pillow |
| Ambiente | `test_env_loading.py` | Prioridade das variáveis do ambiente e fallback `.env` | Passou com valores fictícios e arquivo temporário |
| ISBN | `test_isbn_lookup.py` | validação, cache, fontes, prioridade, Vision e endpoint | `25 passed` em 04/10/2026 |
| QR/ID | `test_qr_id_resolution.py` | CRUD e resolução QR | Executado na suíte geral; depende de qrcode/OpenCV/PyZbar |
| Relatório | `test_reports_student_status.py` | CSV de situação dos alunos | Executado na suíte geral |
| Reconexão | `test_supabase_reconnect.py` | estado offline/reconexão esperado pelo teste | Falha porque `_offline` não existe no cliente atual |
| Identificadores | `test_unique_identifiers.py` | IDs/QR distintos para livros iguais | Executado na suíte geral |
| Formulário ISBN | `frontend/tests/books-isbn.test.js` | preenchimento de título, autor, gênero e área | Passou |
| Scanner JS | `frontend/tests/qr-scanner.test.js` | callback e foco da câmera | Passou |

## 25.2 Resultado reproduzido em 04/10/2026

Com `.venv312`:

```text
Backend completo: 32 passed, 6 failed, 3 warnings
ISBN/Vision isolado: 25 passed, 1 warning
Frontend books ISBN: passed
Frontend qr scanner: passed
```

As seis falhas na execução completa foram quatro testes de login e dois testes de reconexão do Supabase. O teste que antes exigia um `backend/.env` foi atualizado para representar Secrets do Codespace e passou. O teste real de Vision usou frame sintético, não a câmera física.

Os testes não comprovam câmera física, deploy, carga real ou segurança completa.

## 25.3 Como interpretar um teste quebrado

Um teste quebrado prova que aquele teste não passou. Ele não prova sozinho que toda a funcionalidade está quebrada. É necessário distinguir:

```text
teste existe
  |
  v
teste foi executado?
  |
  v
qual resultado?
  |
  v
falha de código, ambiente ou expectativa antiga?
```

Exemplo: `test_env_loading.py` exige um arquivo `.env`, mas o ambiente real usa Codespace Secrets. O teste precisa ser adaptado ao contrato atual; sua falha não prova que os Secrets não funcionam.

---

# 26. FUNCIONALIDADES IMPLEMENTADAS

| Funcionalidade | Classificação | Onde | Evidência |
|---|---|---|---|
| Servir frontend com Flask | Implementada e comprovada | `app.py` | servidor iniciou e home respondeu 200 |
| Health check Supabase | Implementada e comprovada | `app.py` | `/api/health` retornou banco conectado |
| CRUD de livros | Implementada, mas E2E não totalmente testada | `books.py`, `books.js` | rotas e UI presentes; testes de IDs/fallback |
| Cadastro de exemplares | Implementada e testada parcialmente | `_build_exemplar_meta()` | teste de IDs distintos |
| Busca manual ISBN | Implementada e comprovada | `books.py`, `books.js` | 25 testes backend, teste frontend e consulta real HTTP 200 |
| Groq textual | Chamada real confirmada nesta sessão | `_groq_lookup()` | modo scanner recebeu HTTP 200; os dados finais também combinam fontes bibliográficas |
| Groq Vision | Chamada isolada confirmada com frame sintético | `_groq_isbn_from_image()`, endpoint | reconheceu `9788532511010`; câmera física não confirmada |
| Prioridade bibliográfica | Implementada e comprovada por testes | helpers de metadata | consenso/conflito testados |
| Scanner navegador | Implementada parcialmente | `qr-scanner.js` | teste callback; câmera física não confirmada |
| Fallback PyZbar | Implementada condicionalmente | `scanner/routes.py` | requer `libzbar0` no sistema |
| Cadastro de alunos | Implementada, E2E parcial | `students.py`, `students.js` | rotas, UI e testes de QR/ID |
| Importação CSV | Implementada | `students.py`/`students.js` | código presente |
| Salas | Implementada, E2E não totalmente testada | `rooms.py`, `rooms.js` | CRUD presente |
| Gêneros | Implementada, E2E não totalmente testada | `genres.py`, `genres.js` | CRUD presente |
| Empréstimo | Implementada, testes E2E incompletos | `loans.py`, `app.js` | regras de disponibilidade presentes |
| Devolução | Implementada parcialmente | `loans.py` | rota e conferência opcional |
| Renovação | Implementada | `loans.py` | rota incrementa prazo/contador |
| QR de entidades | Implementada | `scanner/routes.py` | geração e cartão presentes |
| Login tradicional | Implementada parcialmente | `auth.py`, `app.js` | backend verifica senha; autorização posterior limitada |
| Login por QR | Implementada parcialmente | `routes.py`, `app.js` | resolução e senha admin presentes |
| Relatórios gráficos | Implementada | `reports.py`, `charts.js` | endpoints e Chart.js |
| Exportação CSV | Implementada | `reports.py` | cinco rotas de exportação |
| Deploy Render | Não confirmado | nenhum arquivo operacional atual | documentação antiga não basta |
| JWT/RBAC server-side | Não implementada no código observado | nenhum arquivo | nenhuma implementação encontrada |
| Sincronização JSON/Supabase | Não confirmada | nenhum mecanismo | não há fila/merge observado |

---

# 27. LIMITAÇÕES

## Técnicas

- APIs externas podem falhar, mudar formato ou limitar requisições.
- ISBNsearch depende de parsing HTML.
- Groq depende de modelo e credencial disponíveis.
- Câmera e `BarcodeDetector` variam conforme navegador/dispositivo.
- PyZbar exige `libzbar0`.
- O backend mistura acesso remoto e JSON, aumentando complexidade.

## Segurança

- Não há autorização server-side por papel nas rotas de negócio.
- Cookie de sessão não é `HttpOnly` nem validado pelo backend.
- CORS é permissivo.
- O endpoint de configuração pode devolver chave configurada.
- O SQL contém policies amplas.
- O cartão administrativo pode conter a senha.
- Há senha padrão legada em SQL/documentação, embora o banco real possa ter outro hash.

## Banco

- O SQL pode não representar exatamente o banco remoto atual.
- Não há sincronização automática entre JSON e Supabase.
- Existem diferenças entre colunas do SQL e campos efetivamente usados pelo backend.
- O bloqueio global do `before_request` limita o offline.

## Testes

- A suíte completa possui falhas.
- Não há testes E2E de navegador completos.
- Não há teste reproduzível de câmera física.
- O ambiente Python 3.14 não possui `crypt`; o `.venv312` reduz esse problema.
- Alguns testes esperam estruturas antigas do cliente Supabase.

## Deploy

- Não há configuração operacional confirmada para Render/Gunicorn.
- Não foi possível confirmar ambiente de produção.

---

# 28. O QUE NÃO FOI IMPLEMENTADO

| Funcionalidade | Necessidade | Estado | Motivo |
|---|---|---|---|
| Autorização server-side por papel | Impedir chamadas diretas indevidas | Não implementada no código observado | Não foi possível confirmar o motivo no estado atual do projeto. |
| JWT/Bearer | Sessão verificável em cada chamada | Não implementada | Nenhuma biblioteca/fluxo JWT encontrado. |
| Reconciliação Supabase/JSON | Evitar divergência após indisponibilidade | Não implementada | Não foi encontrado mecanismo de fila/merge. |
| Limite de renovação | Controlar abusos de prazo | Não implementada | `renew_loan()` incrementa sem limite observado. |
| Deploy Render comprovado | Disponibilizar sistema em produção | Não confirmado | Não há configuração operacional atual. |
| Teste de câmera física | Comprovar leitura real | Não confirmado | Apenas teste de callback e funções foram executados. |
| Modelo Vision universal | Garantir acesso em qualquer conta | Não garantido | Depende do catálogo/permissão da conta Groq. |
| Migração segura de todos os hashes | Alinhar banco e documentação | Não confirmada | O banco remoto observado não coincidiu com todos os seeds documentados. |
| Gestão de usuários | CRUD de contas | Não implementada | Só login/configuração foram encontrados. |
| Auditoria completa | Saber quem alterou cada registro | Parcial | `criado_por` aparece em empréstimos, mas não há trilha geral de auditoria. |

---

# 29. DIFICULDADES ENCONTRADAS

## 29.1 Divergência entre documentação, SQL e banco

**Problema:** documentos/SQL descrevem credenciais ou campos que podem não coincidir com o estado remoto.  
**Causa comprovada:** o código consulta a tabela atual; arquivos antigos são apenas documentação.  
**Impacto:** uma senha documentada pode retornar 401.  
**Como foi tratado:** foi feita verificação do banco sem expor hash; não foi alterado o banco.  
**Estado:** pendente de decisão do responsável pelo banco.

## 29.2 Falha dos testes que exigem `.env`

**Problema:** `test_env_loading.py` exige `backend/.env`.  
**Causa:** o ambiente atual usa Codespace Secrets.  
**Impacto:** o teste falha mesmo com Secrets presentes.  
**Tratamento:** a presença das variáveis foi verificada sem revelar valores.  
**Estado:** teste precisa ser adaptado se for mantido.

## 29.3 Scanner e dependência nativa

**Problema:** PyZbar importa o pacote Python, mas pode falhar sem `zbar`.  
**Causa:** `libzbar0` é uma biblioteca do sistema, não apenas um pacote pip.  
**Impacto:** fallback backend de barcode não funciona em alguns ambientes.  
**Tratamento:** dependências Python foram confirmadas; instalação apt encontrou restrição de permissão.  
**Estado:** BarcodeDetector do navegador pode funcionar; fallback requer instalação de sistema.

## 29.4 Modelo Groq Vision

**Problema:** um modelo Vision pode retornar `model_not_found`.  
**Causa:** catálogo/permissão da conta pode não incluir o modelo escolhido.  
**Impacto observado:** modelos indisponíveis podem causar 502. Em 04/10, o navegador também reportou limite de chamadas do Groq.
**Estado verificado em 04/10:** uma chamada isolada posterior foi aceita e reconheceu um ISBN num frame sintético; câmera física e disponibilidade contínua não foram confirmadas.
**Tratamento atual:** intervalo Vision de 5 segundos e espera crescente após falha; os leitores locais permanecem disponíveis. A conta ainda precisa permitir o modelo configurado.

## 29.5 Falta de autorização server-side

**Problema:** o frontend esconde telas, mas APIs não validam papel.  
**Causa:** ausência de middleware/decorator de autenticação encontrado.  
**Impacto:** acesso direto pode ultrapassar a UI.  
**Tratamento:** não foi implementada correção durante esta análise.  
**Estado:** limitação de segurança pendente.

---

# 30. APRENDIZADOS

## 30.1 Técnico

Possíveis aprendizados derivados diretamente do projeto:

- entender a separação frontend/backend;
- escrever rotas Flask e Blueprints;
- consumir endpoints com `fetch`;
- trabalhar com HTTP, JSON e códigos de resposta;
- modelar tabelas PostgreSQL;
- usar foreign keys, índices e constraints;
- consultar Supabase por um cliente Python;
- usar UUIDs para entidades;
- calcular datas de empréstimo;
- trabalhar com ISBN e checksum;
- integrar APIs externas;
- combinar respostas de provedores;
- usar cache, retry e timeout;
- usar `ThreadPoolExecutor`;
- processar QR/barcode e frames de câmera;
- gerar PNGs e QR Codes;
- escrever testes unitários;
- interpretar falhas de ambiente sem confundi-las com falhas de negócio;
- usar Git para acompanhar mudanças.

Esses itens são tópicos de estudo, não afirmações sobre sentimentos ou experiências pessoais do estudante.

## 30.2 Profissional

O processo documentado permite estudar:

- decomposição de um sistema em módulos;
- investigação por logs e testes;
- comparação entre fonte de verdade e documentação;
- registro de limitações;
- cuidado com secrets;
- revisão de código produzido com auxílio de IA;
- importância de testar integrações externas.

## 30.3 Pessoal

Não foram inventadas experiências pessoais. O estudante pode refletir sobre quais desses aprendizados realmente ocorreram durante o desenvolvimento.

---

# 31. O QUE EU FARIA DIFERENTE

Esta seção oferece possibilidades fundamentadas; não escolhe uma única resposta pelo estudante.

| Problema atual | Possível melhoria | Benefício | Complexidade |
|---|---|---|---|
| APIs sem autorização server-side | Adicionar sessão/token e decorators por papel | Proteção real das operações | Alta |
| Cookie JS não validado pelo backend | Sessão HttpOnly ou token verificável | Reduz manipulação no navegador | Média/alta |
| JSON e Supabase divergem | Escolher um único sistema oficial e criar fila de sincronização | Consistência | Alta |
| Provedores externos instáveis | Adaptadores, observabilidade e circuit breaker | Diagnóstico e resiliência | Média |
| Parsing HTML do ISBNsearch | Usar uma API estruturada ou parser mais testado | Menos quebra por layout | Média |
| Barcode depende de zbar | Empacotar dependência do sistema ou usar biblioteca web compatível | Deploy previsível | Média |
| Testes de ambiente rígidos | Testar Secrets e `.env` com contratos separados | Menos falso negativo | Baixa |
| SQL destrutivo com `DROP TABLE` | Criar migrations incrementais e backup | Menor risco de perda | Média/alta |
| Senha no cartão administrativo | Remover senha da imagem e usar fluxo separado | Menor exposição | Baixa |
| Devolução com aluno opcional | Tornar confirmação obrigatória quando a política exigir | Mais rastreabilidade | Baixa/média |

---

# 32. PRÓXIMOS PASSOS

## Já implementado

- CRUDs principais;
- ISBN manual;
- integração bibliográfica;
- scanner base;
- QR/cartões;
- empréstimo/devolução/renovação;
- relatórios;
- testes específicos de ISBN e frontend.

## Possíveis evoluções futuras

- adaptar testes de login, ambiente e reconexão;
- adicionar autorização server-side;
- confirmar e configurar modelo Vision disponível;
- instalar/empacotar `libzbar0`;
- criar migrations não destrutivas;
- adicionar testes E2E;
- validar câmera física em aparelhos reais;
- criar observabilidade das APIs externas;
- alinhar SQL e schema real do Supabase;
- formalizar deploy de produção;
- criar administração de usuários;
- adicionar auditoria de alterações.

Esses itens são sugestões e não devem ser descritos como implementações atuais.

---

# 33. RESPOSTAS PARA O RELATÓRIO ESCOLAR

## 33.1 Resumo Executivo

### O que precisa aparecer

- problema manual;
- solução web;
- tecnologias principais;
- funcionalidades principais;
- evidências de teste;
- limitações honestas.

### Resposta-base

O projeto é uma aplicação web para organizar uma biblioteca escolar que antes dependia de controles manuais. Ele reúne cadastro de livros, exemplares, alunos, salas e gêneros, além de empréstimos, devoluções, renovações, consulta de ISBN, QR Codes e relatórios. O frontend foi feito com HTML, CSS e JavaScript; o backend utiliza Python e Flask; o caminho principal de persistência usa Supabase/PostgreSQL. Os testes específicos de ISBN e frontend passaram, mas a suíte geral possui falhas de ambiente e testes desatualizados. Não foi possível confirmar deploy de produção ou autorização completa das APIs por papel.

## 33.2 Contextualização do problema

### Como responder

Explique a lista de papel, o crescimento das informações e a dificuldade de localizar/atualizar dados.

### Resposta-base

O controle anterior dos empréstimos era feito manualmente em papel, com nomes, livros e datas. Com o crescimento dos registros, tornou-se mais difícil consultar a situação de cada livro, acompanhar devoluções, atualizar informações e localizar o responsável por um exemplar. O sistema busca organizar esse processo por meio de registros digitais e consultas centralizadas.

## 33.3 Objetivo geral

### Resposta-base

Desenvolver uma aplicação que organize o acervo e o controle de circulação da biblioteca, permitindo cadastrar livros e alunos, registrar empréstimos, acompanhar prazos, registrar devoluções e consultar relatórios.

## 33.4 Objetivos específicos

- digitalizar cadastro de acervo e alunos;
- facilitar busca de livros por texto, ID ou ISBN;
- organizar exemplares individualmente;
- reduzir digitação por QR/barcode quando o leitor funciona;
- registrar empréstimos com aluno, livro, exemplar e datas;
- controlar devoluções e renovações;
- visualizar atrasos e situações por turma;
- exportar informações em CSV;
- estudar integração de APIs externas e banco de dados.

## 33.5 Metodologia de desenvolvimento

### Como responder

Descreva desenvolvimento individual e iterativo, histórico Git, testes e depuração. Não diga Scrum/Kanban sem evidência.

### Resposta-base

O projeto foi desenvolvido individualmente em ciclos de implementação, teste e correção. O Git foi utilizado para registrar mudanças por funcionalidade, como ISBN, scanner, login e relatórios. Os problemas foram analisados por leitura de código, execução de testes, logs e chamadas às APIs. Ferramentas de assistência de IA podem ter sido usadas no processo, mas o código precisou ser revisado e testado. Não há evidência suficiente para afirmar o uso de uma metodologia ágil formal.

## 33.6 Funcionalidades implementadas

Consulte a tabela da seção 26. Use classificações como “implementada”, “parcialmente implementada” e “não confirmada”, em vez de declarar que tudo funciona em produção.

## 33.7 Capturas de tela relevantes

Capturas que demonstrariam o código atual:

1. tela de login;
2. painel com métricas;
3. acervo e modal de cadastro de livro;
4. consulta de ISBN preenchendo o formulário;
5. câmera do cadastro de livro;
6. tela de novo empréstimo;
7. lista de empréstimos com status;
8. modal de devolução;
9. renovação;
10. cadastro de alunos;
11. importação CSV;
12. salas;
13. gêneros;
14. relatórios e gráficos;
15. CSV exportado;
16. tela de espera do banco.

Estas são telas sugeridas; não foram inventadas capturas existentes.

## 33.8 Tecnologias utilizadas

Use a tabela da seção 8 e diferencie tecnologia encontrada no código de tecnologia apenas declarada como dependência.

## 33.9 O MVP funcionou?

Resposta equilibrada:

O núcleo do MVP funciona em partes verificáveis: o servidor inicia, o banco respondeu conectado, o frontend foi servido, os fluxos de ISBN passaram nos testes, o formulário de ISBN passou e o callback do scanner passou. Entretanto, não é possível afirmar que todo o MVP está pronto sem ressalvas, porque a suíte completa possui sete falhas, a câmera física não foi testada, o deploy não foi confirmado e a autorização server-side não está implementada de forma completa.

Classificação recomendada: **funcionamento parcial comprovado, com núcleo operacional e limitações pendentes.**

## 33.10 O que não foi implementado?

- autorização server-side completa;
- JWT/Bearer;
- reconciliação JSON/Supabase;
- deploy de produção comprovado;
- teste E2E de câmera física;
- gestão de usuários;
- limite de renovações;
- auditoria geral.

## 33.11 Dificuldades

- manter integração com provedores externos;
- alinhar resultados diferentes de ISBN;
- tratar falhas de banco e JSON;
- lidar com dependências de câmera/barcode;
- corrigir expectativas antigas de testes;
- manter credenciais fora do código;
- distinguir limitação de ambiente de defeito funcional.

## 33.12 Como foram superadas?

Foram implementados validação de ISBN, retry, timeout, cache, consultas paralelas, combinação por consenso, testes unitários, fallback de leitura e mensagens de erro. As limitações não resolvidas foram registradas separadamente, sem afirmar que foram corrigidas.

## 33.13 Aprendizados

Use os tópicos da seção 30 e escreva a experiência pessoal com suas próprias palavras. Não copie como se fossem sentimentos comprovados neste documento.

## 33.14 O que faria diferente?

Use a tabela da seção 31 e selecione melhorias que correspondam à sua avaliação pessoal.

## 33.15 Próximos passos

Use a seção 32, separando claramente evoluções futuras do que já existe.

## 33.16 Checklist do MVP

| Item | Classificação | Evidência |
|---|---|---|
| Frontend abre | CONCLUÍDO | Flask serviu home com HTTP 200 |
| Backend inicia | CONCLUÍDO | `app.py` executado |
| Supabase acessível no ambiente | CONCLUÍDO nesta execução | `/api/health` retornou conectado |
| Cadastro de livros | PARCIAL | Código e rotas existem; E2E remoto não foi completo |
| Busca manual ISBN | CONCLUÍDO e testado | `25 passed` em 04/10; teste frontend passou |
| Scanner QR/barcode | PARCIAL | código e callback testados; câmera física não confirmada |
| Groq Vision | PARCIAL | chamada isolada reconheceu ISBN em frame sintético; webcam física não confirmada |
| Empréstimos | PARCIAL | código e rotas existem; suíte não é E2E completa |
| Devoluções | PARCIAL | regra e rota existem; conferência do aluno é opcional |
| Renovações | CONCLUÍDO no código | rota implementada; limite não existe |
| Alunos | PARCIAL | CRUD/CSV/QR existem; E2E amplo não confirmado |
| Salas | PARCIAL | CRUD existe; teste E2E não confirmado |
| Gêneros | PARCIAL | CRUD existe; teste E2E não confirmado |
| Relatórios | PARCIAL | endpoints/gráficos/CSV existem; dados de produção não confirmados |
| Login | PARCIAL | backend verifica credencial; autorização posterior incompleta |
| Supabase | CONCLUÍDO nesta execução | health conectado |
| Deploy | NÃO FOI POSSÍVEL CONFIRMAR | sem configuração operacional |
| Suite completa | PARCIAL | 30 passaram e 7 falharam |

---

# 34. COMO ESTUDAR ESTE PROJETO

## 1. Entender o problema

**Estudar:** controle manual, entidades e fluxo de empréstimo.  
**Abrir:** `backend/README.md`, `database.sql`, `backend/api/loans.py`.  
**Acompanhar:** `create_loan()`, `return_loan()`, `renew_loan()`.  
**Avançar quando:** conseguir explicar a relação aluno-livro-exemplar-data.

## 2. Entender o frontend

**Estudar:** HTML, DOM, eventos e modais.  
**Abrir:** `frontend/index.html`, `main.css`.  
**Acompanhar:** IDs de formulário, `onclick`, `oninput` e páginas.  
**Avançar quando:** conseguir localizar o elemento que dispara cada ação.

## 3. Entender o backend

**Estudar:** Flask, função de rota e `jsonify`.  
**Abrir:** `backend/app.py`, `backend/api/books.py`.  
**Acompanhar:** blueprint, decorator `@route`, validação e retorno.  
**Avançar quando:** conseguir explicar o caminho de um `POST`.

## 4. Entender HTTP/API

**Estudar:** GET, POST, PUT, PATCH, DELETE, status e JSON.  
**Abrir:** `frontend/assets/js/api.js`.  
**Acompanhar:** `apiFetch()` e os contratos de `API.books`, `API.loans`.  
**Avançar quando:** conseguir montar uma chamada sem a interface.

## 5. Entender o banco

**Estudar:** tabela, chave, foreign key, índice, JSONB e RLS.  
**Abrir:** `database.sql`, `supabase_client.py`.  
**Acompanhar:** `table()`, `select()`, `insert()`, `update()`, `delete()`.  
**Avançar quando:** conseguir desenhar as relações das tabelas.

## 6. Entender cadastro de livro

**Estudar:** formulário, payload, exemplares e QR.  
**Abrir:** `books.js`, `books.py`, `index.html`.  
**Acompanhar:** `openAddBook()`, `saveBook()`, `create_book()`.  
**Avançar quando:** conseguir narrar o cadastro do clique até o banco.

## 7. Entender ISBN

**Estudar:** ISBN-10, ISBN-13, checksum, normalização, APIs externas.  
**Abrir:** `books.py`, `test_isbn_lookup.py`.  
**Acompanhar:** `_normalize_isbn()`, `_validate_isbn()`, `_lookup_isbn()`.  
**Avançar quando:** conseguir explicar por que fontes diferentes podem discordar.

## 8. Entender scanner

**Estudar:** câmera, canvas, Data URL, QR, EAN, Vision.  
**Abrir:** `qr-scanner.js`, `scanner/routes.py`, `books.js`.  
**Acompanhar:** `_capture()`, `_onFound()`, `_decode_barcode_variants()`.  
**Avançar quando:** souber diferenciar scanner local, fallback backend e Vision.

## 9. Entender empréstimos

**Estudar:** disponibilidade, datas, status e exemplar.  
**Abrir:** `loans.py`, `loans.js`, `app.js`.  
**Acompanhar:** `_available_copies()`, `create_loan()`, `return_loan()`.  
**Avançar quando:** conseguir explicar o impedimento de exemplar duplicado ativo.

## 10. Entender autenticação

**Estudar:** hash, autenticação, autorização e sessão.  
**Abrir:** `auth.py`, `app.js`, `database.sql`.  
**Acompanhar:** `_verify_password()`, `_get_user_by_login()`, `doLogin()`.  
**Avançar quando:** souber explicar por que esconder menu não protege uma API.

## 11. Entender testes

**Estudar:** fixture, monkeypatch, mock, assert e teste de integração.  
**Abrir:** `backend/tests/`, `frontend/tests/`.  
**Acompanhar:** `test_isbn_lookup.py`, `test_qr_id_resolution.py`.  
**Avançar quando:** conseguir diferenciar falha de teste e falha de funcionalidade.

## 12. Entender deploy

**Estudar:** ambiente, Secrets, porta, servidor WSGI e produção.  
**Abrir:** `app.py`, `requirements.txt`, `.env.example`.  
**Acompanhar:** `load_environment()`, `app.run()`, variáveis.  
**Avançar quando:** conseguir listar o que está e não está confirmado sobre Render.

---

# 35. GUIA DE LEITURA DO CÓDIGO

## `backend/app.py`

- **Função:** inicializa Flask e registra o sistema.
- **Principais elementos:** `load_environment()`, `require_database_for_api()`, `health()`, `serve_frontend()`.
- **Quem chama:** processo Python ao iniciar.
- **Quem chama:** blueprints, cliente Flask e navegador.
- **Entrada:** ambiente e requisições HTTP.
- **Saída:** aplicação, arquivos, JSON de health e erros.

## `backend/api/books.py`

- **Função:** acervo, exemplares, ISBN e QR de livros.
- **Principais funções:** `_normalize_isbn()`, `_validate_isbn()`, provedores, `_lookup_isbn()`, `create_book()`.
- **Quem chama:** rotas Flask e `api.js`.
- **Entrada:** ISBN, JSON de livro e IDs.
- **Saída:** JSON de livros, metadados e erros HTTP.

## `backend/api/students.py`

- **Função:** cadastro e manutenção de alunos.
- **Principais funções:** `list_students()`, `create_student()`, `toggle_librarian_access()`, `import_csv()`.
- **Entrada:** filtros, JSON e CSV.
- **Saída:** alunos, QR e contadores de importação.

## `backend/api/loans.py`

- **Função:** circulação de exemplares.
- **Principais funções:** `_available_copies()`, `_find_student_by_ref()`, `create_loan()`, `renew_loan()`, `return_loan()`.
- **Entrada:** IDs, datas, prazo, exemplar e referência do aluno.
- **Saída:** empréstimo, erro de disponibilidade, devolução ou renovação.

## `backend/api/reports.py`

- **Função:** agregações e CSV.
- **Principais funções:** `_fetch_all()`, `chart_summary()`, `top_books()`, `generate_monthly()`, exportações.
- **Entrada:** dados do banco, query `limit` e mês.
- **Saída:** JSON de gráfico, relatório mensal e CSV.

## `backend/api/auth.py`

- **Função:** autenticação.
- **Principais funções:** `_verify_password()`, `_get_user_by_login()`, `login()`.
- **Entrada:** login e senha.
- **Saída:** access, id, login, nome ou erro.

## `backend/api/_helpers.py`

- **Função:** persistência auxiliar e detecção de schema.
- **Principais funções:** `read_json()`, `write_json()`, `table_ok()`, `has_deleted_at()`, `is_offline_error()`.
- **Entrada:** caminhos, clientes, tabelas e exceções.
- **Saída:** listas, booleanos e gravações.

## `backend/utils/supabase_client.py`

- **Função:** criar cliente e executar consultas Supabase.
- **Principais funções:** `_normalize_supabase_url()`, `get_client()`, `sb_exec()`.
- **Entrada:** variáveis de ambiente e queries.
- **Saída:** cliente, dados ou exceção.

## `backend/scanner/routes.py`

- **Função:** QR, barcode, resolução, login QR e cartões.
- **Principais funções:** `_ensure_scan_deps()`, `_decode_barcode_variants()`, `decode_image()`, `_resolve_qr()`, `_build_card()`.
- **Entrada:** frames, códigos, IDs e senha de cartão.
- **Saída:** códigos resolvidos, PNG base64 e estados da câmera.

## `frontend/assets/js/api.js`

- **Função:** cliente HTTP.
- **Principais elementos:** `apiFetch()` e objeto `API`.
- **Entrada:** caminho, método, JSON, AbortSignal.
- **Saída:** Promise com JSON ou erro.

## `frontend/assets/js/app.js`

- **Função:** controlador global.
- **Principais funções:** `doLogin()`, `_finishLogin()`, `_applyRolePermissions()`, `syncAll()`, `confirmLoan()`, devolução e renovação.
- **Entrada:** eventos de interface e respostas API.
- **Saída:** estado, navegação, cookies e renderização.

## `frontend/assets/js/store.js`

- **Função:** estado global e cache local.
- **Principais funções:** setters, getters, `loanStatus()`, `activeLoans()`.
- **Entrada:** arrays vindos da API.
- **Saída:** dados para renderização e `localStorage`.

## `frontend/assets/js/pages/books.js`

- **Função:** acervo e cadastro de livros.
- **Principais funções:** `renderBooks()`, `lookupBookIsbn()`, `scanBookIsbn()`, `saveBook()`.
- **Entrada:** formulário, scanner e respostas de ISBN.
- **Saída:** tabela, modal preenchido e chamadas de criação.

## `frontend/assets/js/qr-scanner.js`

- **Função:** câmera local.
- **Principais funções:** `_capture()`, `_onFound()`, `start()`, `stop()`, `switchCamera()`.
- **Entrada:** câmera e opções de callback.
- **Saída:** código detectado ou frame enviado ao handler opcional.

## `frontend/assets/js/pages/loans.js`

- **Função:** tabela de empréstimos e dashboard.
- **Principais funções:** `renderLoans()`, `renderDashboard()`.
- **Entrada:** `Store`.
- **Saída:** tabelas, indicadores e prioridade de alunos.

## `frontend/assets/js/pages/students.js`

- **Função:** alunos, CSV, histórico e acesso bibliotecário.
- **Principais funções:** `renderStudents()`, `saveStudent()`, `importCSV()`, `showStudentHistory()`.
- **Entrada:** formulários, filtros e scanner.
- **Saída:** listas, históricos e chamadas API.

## `frontend/assets/js/charts.js`

- **Função:** gráficos Chart.js.
- **Entrada:** endpoints de reports.
- **Saída:** gráficos e contadores visuais.

---

# 36. EXPLICAÇÃO DAS FUNÇÕES IMPORTANTES

## `_normalize_isbn(value)`

- **Recebe:** qualquer valor convertido em string.
- **Faz:** remove separadores e converte `X`.
- **Existe porque:** fontes e usuários podem usar hífens/espaços.
- **Retorna:** ISBN sem formatação.
- **Chamado por:** validadores e provedores.
- **Erro:** normalmente não lança erro sozinha.

## `_validate_isbn(normalized)`

- **Recebe:** ISBN já normalizado.
- **Faz:** verifica formato e checksum.
- **Retorna:** `None` quando válido.
- **Erro:** `ValueError` quando inválido.
- **Chamado por:** `_lookup_isbn()` e cada provedor.

## `_google_books_lookup(isbn)`

- **Recebe:** ISBN.
- **Faz:** consulta endpoint Google Books e extrai `volumeInfo`.
- **Retorna:** dicionário de ISBN/título/autor/categorias.
- **Erro:** `LookupError` ou `_ProviderError`.
- **Chamado por:** `_lookup_isbn()`.

## `_isbnsearch_lookup(isbn)`

- **Recebe:** ISBN.
- **Faz:** consulta HTML e usa parser.
- **Retorna:** metadados parciais.
- **Erro:** `LookupError` ou `_ProviderError`.

## `_openlibrary_lookup(isbn)`

- **Recebe:** ISBN.
- **Faz:** consulta JSON de Open Library.
- **Retorna:** título, autores e subjects.
- **Erro:** `LookupError` ou `_ProviderError`.

## `_groq_lookup(isbn)`

- **Recebe:** ISBN.
- **Faz:** pede metadados JSON ao Groq textual.
- **Retorna:** sugestão bibliográfica.
- **Erro:** `LookupError` sem chave/dados ou `_ProviderError`.

## `_groq_isbn_from_image(image_data)`

- **Recebe:** Data URL de frame.
- **Faz:** decodifica base64, envia imagem ao modelo Vision e interpreta JSON.
- **Retorna:** `encontrado` e ISBN.
- **Erro:** frame inválido, Groq ausente, modelo indisponível ou resposta inválida.
- **Não faz:** não fornece título/autor como fonte principal.

## `_lookup_isbn(isbn, use_groq=False)`

- **Recebe:** ISBN e flag de uso do Groq textual.
- **Faz:** normaliza, valida, consulta cache, chama fontes em paralelo e combina resultados.
- **Retorna:** dados bibliográficos enriquecidos com gênero.
- **Erro:** `ValueError`, `LookupError`, `RuntimeError` conforme o caso.
- **Chamado por:** `/isbn-lookup` e `/isbn-vision`.

## `_match_genre(categories)`

- **Recebe:** categorias externas.
- **Faz:** normaliza e compara com gêneros locais/aliases.
- **Retorna:** ID e nome do gênero.
- **Limitação:** comparação por inclusão pode ser ampla.

## `_available_copies(...)`

- **Recebe:** cliente, livro, quantidade e IDs de exemplar.
- **Faz:** remove cópias com empréstimos ativos.
- **Retorna:** lista de códigos/IDs livres.
- **Chamado por:** `create_loan()`.

## `create_loan()`

- **Recebe:** JSON com livro, aluno, prazo, data e exemplar.
- **Faz:** confirma entidades, calcula disponibilidade e datas, grava.
- **Retorna:** empréstimo 201 ou erro.

## `return_loan()`

- **Recebe:** ID e dados opcionais do aluno/observação.
- **Faz:** valida estado e atualiza devolução.
- **Retorna:** empréstimo atualizado ou erro.

## `renew_loan()`

- **Recebe:** ID e dias.
- **Faz:** soma prazo e contador.
- **Retorna:** registro atualizado.

## `doLogin()`

- **Recebe:** valores dos campos de login.
- **Faz:** POST ao backend, mostra erro ou chama `_finishLogin()`.
- **Limitação:** a sessão posterior não é verificada no backend.

## `_capture()`

- **Recebe:** frame da câmera disponível no vídeo.
- **Faz:** desenha no canvas, executa leitores locais e handler Vision opcional.
- **Retorna:** indiretamente chama `_onFound()`.
- **Limitação:** resultados dependem de foco, luz, resolução, navegador e dependências.

---

# 37. FLUXOGRAMAS

## 37.1 Cadastro de livro

```text
Usuário
  |
  v
index.html -> modal-book
  |
  v
books.js -> saveBook()
  |
  v
API.books.create()
  |
  v
POST /api/books/
  |
  v
books.py -> create_book()
  |
  +--> valida título/autor
  +--> new_id()
  +--> _build_exemplar_meta()
  +--> grava Supabase/JSON conforme caminho
  +--> gera QR PNG
  |
  v
JSON da resposta
  |
  v
Store/sync/render
```

## 37.2 Pesquisa ISBN manual

```text
ISBN digitado
  |
  v
_normalize_isbn()
  |
  v
GET /api/books/isbn-lookup?source=manual
  |
  v
use_groq = False
  |
  +--> Google Books
  +--> ISBNsearch
  +--> Open Library
  |
  v
consenso/prioridade/cache
  |
  v
match de gênero
  |
  v
books.js preenche formulário
```

## 37.3 Scanner de cadastro

```text
Clica Ler ISBN
  |
  v
QRScanner.start(... frameHandler)
  |
  v
getUserMedia -> video -> canvas
  |
  v
POST /api/books/isbn-vision
  |
  v
Groq Vision -> JSON ISBN
  |
  v
normaliza/valida ISBN
  |
  +--> Google Books
  +--> ISBNsearch
  +--> Open Library
  |
  v
resultado bibliográfico
  |
  v
formulário preenchido
```

Fallback local:

```text
frame
  |
  +--> jsQR
  +--> BarcodeDetector
  +--> /api/qr/decode
```

## 37.4 Empréstimo

```text
Livro + aluno
  |
  v
app.js confirma
  |
  v
POST /api/loans/
  |
  v
loans.py valida
  |
  v
calcula exemplar disponível
  |
  v
calcula vencimento
  |
  v
insere emprestimo
  |
  v
Store e dashboard
```

## 37.5 Login

```text
login-user + login-pass
  |
  v
app.js doLogin()
  |
  v
POST /api/auth/login
  |
  v
auth.py busca usuarios
  |
  v
_verify_password()
  |
  +--> falha -> 401
  |
  v
access/id/login/name
  |
  v
currentUser + cookie JS
  |
  v
syncAll() e navegação
```

---

# 38. GLOSSÁRIO PARA INICIANTE

| Termo | Explicação |
|---|---|
| API | Interface que permite um programa conversar com outro. |
| Endpoint | Caminho específico de uma API. |
| HTTP | Protocolo usado para trocar requisições e respostas na web. |
| GET | Método normalmente usado para consultar. |
| POST | Método usado para criar ou executar ação. |
| PUT | Método usado para atualizar um recurso. |
| PATCH | Método usado para atualizar parte de um recurso. |
| DELETE | Método usado para excluir um recurso. |
| JSON | Texto estruturado usado nas respostas e requisições. |
| Frontend | Parte que roda no navegador e aparece para o usuário. |
| Backend | Parte do sistema que roda no servidor. |
| Flask | Framework Python usado para criar servidor e rotas. |
| Blueprint | Agrupamento de rotas de um módulo Flask. |
| Route | Função associada a método e caminho HTTP. |
| Fetch | API JavaScript que faz requisições HTTP. |
| Banco de dados | Sistema persistente que guarda registros. |
| PostgreSQL | Banco relacional descrito pelo SQL do projeto. |
| Supabase | Serviço que fornece acesso ao PostgreSQL e APIs. |
| SQL | Linguagem de criação/consulta de banco. |
| UUID | Identificador único de formato longo. |
| CRUD | Create, Read, Update, Delete: criar, consultar, editar e excluir. |
| Cache | Cópia temporária para evitar trabalho repetido. |
| Fallback | Caminho alternativo quando o principal falha. |
| Timeout | Tempo máximo esperado para uma operação. |
| Retry | Nova tentativa depois de uma falha temporária. |
| Thread | Unidade de execução concorrente. |
| ThreadPoolExecutor | Ferramenta Python para executar tarefas em paralelo. |
| QR Code | Código visual bidimensional que guarda texto. |
| ISBN | Identificador bibliográfico de uma edição de livro. |
| Barcode | Código de barras, normalmente unidimensional. |
| EAN | Formato de código de barras; ISBN-13 pode ser representado como EAN-13. |
| OCR | Reconhecimento óptico de caracteres; não foi implementado como biblioteca específica confirmada. |
| Visão computacional | Análise de imagem por software; aparece em OpenCV/Groq Vision. |
| API key | Chave usada para autenticar acesso a um serviço. |
| Variável de ambiente | Valor fornecido fora do código, por exemplo em Secret. |
| Secret | Configuração sensível que não deve ir para o Git. |
| Git | Sistema de controle de versões. |
| GitHub | Serviço de hospedagem/revisão de repositórios Git. |
| Commit | Registro de uma versão/mudança no Git. |
| Deploy | Publicação do sistema em um ambiente de execução. |
| Render | Plataforma citada em documentos, mas não confirmada operacionalmente. |
| CORS | Regra que controla origens que podem chamar uma API. |
| RLS | Row Level Security: regras de acesso por linha do banco. |
| Autenticação | Verificação de quem está tentando entrar. |
| Autorização | Verificação do que uma pessoa pode fazer. |
| Checksum | Cálculo que verifica se um identificador, como ISBN, é válido. |
| `data:` URL | Texto que contém tipo e conteúdo de uma imagem, usado nos frames temporários. |
| JSONB | Tipo PostgreSQL para JSON indexável/estruturado. |
| Foreign key | Campo que aponta para a chave de outra tabela. |
| Constraint | Regra do banco que impede valores inválidos. |
| Soft delete | Marcação de exclusão, como `deleted_at`, sem remover imediatamente a linha. |
| Políticas RLS | Regras que controlam acesso às tabelas no PostgreSQL/Supabase. |

---

# 39. EXPLIQUE COMO SE EU ESTIVESSE APRENDENDO

Ao estudar qualquer parte, use este modelo:

```text
Código
  |
  v
O que significa?
  |
  v
Por que existe?
  |
  v
Exemplo simples
  |
  v
Onde aparece no projeto?
```

### Exemplo: rota

```python
@books_bp.route("/", methods=["GET"])
def list_books():
    ...
```

- **Código:** registra uma função para requisições GET.
- **Significado:** quando alguém pedir `/api/books/`, Flask executa `list_books()`.
- **Por que existe:** listar livros.
- **Exemplo simples:** abrir `/api/books/?q=historia`.
- **No projeto:** `books.js` chama `API.books.list()`.

### Exemplo: payload

```python
payload = {"livro_id": book_id, "aluno_id": student_id}
```

- **Código:** dicionário Python.
- **Significado:** conjunto de campos que será salvo.
- **Por que existe:** representar um empréstimo.
- **Exemplo simples:** um formulário vira JSON.
- **No projeto:** `create_loan()` acrescenta datas e exemplar.

### Exemplo: fallback

```text
Supabase falha -> módulo tenta JSON local
```

Isso não significa que todo o sistema fica offline: `app.py` pode bloquear a requisição antes do módulo. Essa diferença é importante para entender o estado real.

---

# 40. RELAÇÃO ENTRE FRONTEND E BACKEND

| Ação | Arquivo frontend | Função frontend | Endpoint | Função backend | Resultado |
|---|---|---|---|---|---|
| Login | `app.js` | `doLogin()` | `POST /api/auth/login` | `auth.login()` | papel/nome ou 401 |
| Sincronizar dados | `app.js` | `syncAll()`/`syncData()` | livros/alunos/loans | listagens | Store atualizado |
| Cadastrar livro | `books.js` | `saveBook()` | `POST /api/books/` | `create_book()` | livro e QR |
| Editar livro | `books.js` | `saveBook()` | `PUT /api/books/<id>` | `update_book()` | livro atualizado |
| Buscar ISBN | `books.js` | `lookupBookIsbn()` | `GET /api/books/isbn-lookup` | `lookup_isbn()` | metadados |
| Vision ISBN | `books.js`/`qr-scanner.js` | `frameHandler` | `POST /api/books/isbn-vision` | `lookup_isbn_from_image()` | ISBN + livro |
| Scanner QR/barcode | `qr-scanner.js` | `_capture()` | `POST /api/qr/decode` como fallback | `decode_image()` | código/resolução |
| Criar aluno | `students.js` | `saveStudent()` | `POST /api/students/` | `create_student()` | aluno/QR |
| Importar alunos | `students.js` | `importCSV()` | `POST /api/students/import/csv` | `import_csv()` | contadores |
| Criar empréstimo | `app.js`/`students.js` | `confirmLoan()`/histórico | `POST /api/loans/` | `create_loan()` | empréstimo |
| Devolver | `app.js` | `confirmDevolution()` | `POST /api/loans/<id>/return` | `return_loan()` | data devolução |
| Renovar | `app.js` | `confirmRenewal()` | `POST /api/loans/<id>/renew` | `renew_loan()` | nova data |
| Salas | `rooms.js` | `saveRoom()` | `/api/rooms/` | funções rooms | sala |
| Gêneros | `genres.js` | `saveGenre()` | `/api/genres/` | funções genres | gênero |
| Gráficos | `charts.js` | `_build*()` | `/api/reports/*` | funções reports | Chart.js |
| Exportações | `app.js`/páginas | URL direta | `/api/reports/export/*` | `_csv_resp()` e rotas | download CSV |

---

# 41. MAPA DE DEPENDÊNCIAS

```text
index.html
  |
  +--> utils.js
  +--> store.js
  +--> api.js
  +--> qr-scanner.js
  +--> charts.js
  +--> pages/books.js
  +--> pages/students.js
  +--> pages/loans.js
  +--> pages/rooms.js
  +--> pages/genres.js
  +--> app.js
```

```text
app.js
  |
  +--> API
  +--> Store
  +--> Utils
  +--> Charts
  +--> QRScanner
```

```text
API
  |
  +--> HTTP /api/books
  +--> HTTP /api/students
  +--> HTTP /api/loans
  +--> HTTP /api/reports
  +--> HTTP /api/rooms
  +--> HTTP /api/genres
  +--> HTTP /api/auth
  +--> HTTP /api/qr
```

```text
backend/app.py
  |
  +--> auth_bp
  +--> books_bp
  +--> students_bp
  +--> loans_bp
  +--> reports_bp
  +--> rooms_bp
  +--> genres_bp
  +--> qr_bp
```

```text
blueprint
  |
  +--> utils.get_client()
  +--> utils.sb_exec()
  +--> api._helpers
  +--> Supabase/PostgreSQL
  +--> JSON local quando o módulo consegue usar fallback
```

---

# 42. ESTADO ATUAL DO PROJETO

| Área | Estado | Observação |
|---|---|---|
| Cadastro de livros | ✅ confirmado/parcial | Código completo; E2E remoto não completo |
| ISBN manual | ✅ confirmado | 25 testes específicos, teste frontend e consulta real HTTP 200 |
| Scanner | ⚠️ parcial | callback testado; câmera física não confirmada |
| Groq textual | ✅ chamada real confirmada | modo scanner e manual responderam HTTP 200 para o mesmo ISBN |
| Groq Vision | ⚠️ parcial | chamada real isolada reconheceu ISBN em frame sintético; câmera física não testada |
| Empréstimos | ⚠️ parcial | rotas/regras presentes; cobertura E2E limitada |
| Devoluções | ⚠️ parcial | implementada; conferência de aluno é opcional |
| Renovações | ✅ no código | sem limite máximo observado |
| Alunos | ⚠️ parcial | CRUD, CSV, QR e histórico presentes |
| Salas | ⚠️ parcial | CRUD presente, testes E2E não confirmados |
| Gêneros | ⚠️ parcial | CRUD e matching presentes |
| Login | ⚠️ parcial | credencial validada; autorização posterior incompleta |
| Supabase | ✅ confirmado no ambiente | health retornou conectado em 02/10/2026 |
| QR Code | ⚠️ parcial | geração/resolução implementadas; dependências/câmera variam |
| Relatórios | ⚠️ parcial | JSON, gráficos, mensal e CSV implementados |
| Testes específicos | ✅ confirmado | ISBN/Vision 25 passed; frontend 2 passed |
| Testes completos | ⚠️ parcial | 32 passed, 6 failed, 3 warnings em 04/10/2026 |
| Deploy | ❓ não confirmado | sem configuração operacional encontrada |
| Fallback JSON | ⚠️ parcial | existe em módulos, mas pode ser bloqueado pelo guard do app |
| Autorização server-side | ❌ não implementada no código observado | UI esconde menus, APIs não impõem papel |
| JWT/Bearer | ❌ não encontrado | não implementado |
| Reconciliação banco/JSON | ❌ não encontrado | não há fila/merge |

---

# 43. CONCLUSÃO TÉCNICA

O projeto já possui um núcleo funcional amplo: servidor Flask, frontend integrado, CRUDs, empréstimos, devoluções, renovações, ISBN, QR, relatórios e acesso ao Supabase. A organização por blueprints e arquivos de páginas permite estudar cada domínio separadamente.

As partes mais consolidadas para estudo são:

- estrutura Flask e blueprints;
- fluxo frontend -> API -> backend;
- cálculo de empréstimos e status;
- validação/consulta de ISBN;
- geração e resolução de QR;
- relatórios e exportações;
- testes específicos do ISBN.

As partes que ainda exigem atenção são:

- autenticação contínua e autorização real;
- divergência JSON/Supabase;
- segurança de CORS, sessão, policies e cartão administrativo;
- testes completos;
- dependências de scanner;
- modelo e precisão do Groq Vision;
- deploy.

A conclusão correta não é que tudo está pronto nem que tudo está quebrado. O código demonstra um sistema funcional em desenvolvimento, com módulos importantes implementados, testes específicos positivos e limitações técnicas e de segurança que precisam ser consideradas.

---

# 44. CHECKLIST FINAL DE QUALIDADE DA ANÁLISE

- [x] Pastas backend e frontend analisadas.
- [x] Módulos principais Python analisados.
- [x] Banco SQL analisado.
- [x] Dependências analisadas.
- [x] Testes analisados.
- [x] Resultados de testes atuais registrados.
- [x] ISBN analisado.
- [x] Groq textual e Vision separados.
- [x] Scanner navegador e backend diferenciados.
- [x] Login e autorização diferenciados.
- [x] Empréstimo, devolução e renovação analisados.
- [x] Relatórios analisados.
- [x] Fallback JSON analisado.
- [x] Deploy separado entre confirmado e não confirmado.
- [x] Limitações registradas.
- [x] Funcionalidades não confirmadas marcadas.
- [x] Secrets, senhas e API keys não expostos.
- [x] Documentação antiga tratada como contexto, não como prova.

---

# Observação final sobre a fonte de verdade

Este guia representa o estado analisado do repositório em 02/10/2026. Se o banco remoto, os Secrets, as dependências do sistema, o navegador ou os arquivos do projeto mudarem, alguns resultados poderão mudar. Para atualizar este documento, execute novamente os testes, verifique `/api/health`, compare o SQL com o schema remoto e revise as limitações antes de alterar as conclusões.
