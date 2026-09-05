# Relatório de estudo do sistema de biblioteca

**Projeto:** Gerenciamento de empréstimo de livros de biblioteca  
**Data da análise:** 2026-09-05  
**Branch analisada:** `fix/login-error-message`

> Este relatório foi escrito como material de estudo. Ele explica o sistema real encontrado no código, usando exemplos simples e identificando também limitações e pendências. Valores secretos do `backend/.env` não são exibidos.

## 1. Introdução ao projeto

### O que é o sistema?

O projeto é um sistema web para administrar uma biblioteca escolar. Ele permite cadastrar livros, alunos, salas e gêneros, além de controlar empréstimos, devoluções, renovações, QR Codes e relatórios.

Podemos imaginar o sistema como uma biblioteca digital:

- o bibliotecário cadastra os livros e alunos;
- cada livro possui um identificador próprio;
- cada exemplar pode ser controlado separadamente;
- um empréstimo relaciona um aluno, um livro e um exemplar;
- o sistema calcula prazos e identifica atrasos.

### Qual problema ele resolve?

Sem um sistema, o controle pode depender de cadernos, planilhas ou memória. Isso dificulta saber:

- quais livros existem;
- quantos exemplares estão disponíveis;
- quem está com cada exemplar;
- quais empréstimos estão atrasados;
- quais turmas utilizam mais a biblioteca.

O sistema centraliza essas informações e automatiza parte do trabalho.

### Objetivo

O objetivo é oferecer um acervo digital e um controle de circulação de livros, com identificação por UUID e QR Code, persistência em Supabase e fallback local em arquivos JSON.

### Quem utiliza?

Há dois papéis previstos:

- **Administrador:** pode acessar cadastros, relatórios, configurações e gerenciamento completo.
- **Bibliotecário:** pode consultar o acervo e realizar operações de empréstimo, devolução e renovação.

Atualmente essa separação é aplicada principalmente no frontend. A autorização completa no backend ainda precisa ser criada.

### Funcionamento geral

O fluxo geral é:

```text
Usuário faz login
    ↓
Frontend abre o painel
    ↓
Usuário consulta ou altera dados
    ↓
JavaScript envia uma requisição HTTP
    ↓
Backend Flask valida e processa
    ↓
Supabase é consultado ou atualizado
    ↓
Backend devolve JSON
    ↓
Frontend atualiza a tela
```

Quando o Supabase não está disponível, alguns módulos usam arquivos JSON locais.

## 2. Tecnologias utilizadas

### HTML

HTML é a linguagem que define a estrutura da página. No projeto, [frontend/index.html](frontend/index.html) contém:

- tela de login;
- menu lateral;
- páginas do painel;
- tabelas;
- formulários;
- modais;
- botões e campos de entrada.

HTML responde à pergunta: **quais elementos existem na tela?**

### CSS

CSS define a aparência dos elementos. O arquivo principal é [frontend/assets/css/main.css](frontend/assets/css/main.css).

Ele controla:

- cores;
- espaçamento;
- tabelas;
- botões;
- tema claro e escuro;
- layout responsivo;
- sidebar e modais;
- estados visuais de erro e sucesso.

CSS responde à pergunta: **como os elementos aparecem?**

### JavaScript

JavaScript dá comportamento à interface. Ele abre modais, realiza requisições, valida campos, atualiza tabelas e controla o scanner.

Principais arquivos:

- [frontend/assets/js/app.js](frontend/assets/js/app.js): controller principal, login, navegação, sessão e sincronização.
- [frontend/assets/js/api.js](frontend/assets/js/api.js): cliente HTTP do frontend.
- [frontend/assets/js/store.js](frontend/assets/js/store.js): estado global dos dados.
- [frontend/assets/js/pages/books.js](frontend/assets/js/pages/books.js): acervo e cadastro de livros.
- `students.js`, `loans.js`, `rooms.js`, `genres.js`: lógica das páginas correspondentes.
- [frontend/assets/js/qr-scanner.js](frontend/assets/js/qr-scanner.js): câmera e leitura de códigos.
- `charts.js`: gráficos do dashboard e relatórios.
- `utils.js`: utilitários de interface.

### Backend Flask

Flask é o framework Python que recebe requisições HTTP, aplica regras e devolve respostas. O arquivo de entrada é [backend/app.py](backend/app.py).

Exemplo simples:

```text
Frontend: GET /api/books/
Backend: busca livros
Backend: retorna JSON
Frontend: desenha os livros na tabela
```

### Supabase/PostgreSQL

Supabase fornece um banco PostgreSQL acessível por API. O sistema armazena nele usuários, livros, alunos, salas, gêneros, empréstimos e relatórios.

A conexão é centralizada em [backend/utils/supabase_client.py](backend/utils/supabase_client.py).

### Arquivos JSON

Os arquivos em [backend/data](backend/data) funcionam como armazenamento local alternativo:

- `livros.json`;
- `alunos.json`;
- `salas.json`;
- `generos.json`;
- `emprestimos.json`.

Eles ajudam o sistema a continuar operando em modo offline, mas ainda não existe reconciliação automática com o Supabase.

### OpenCV, PyZbar, qrcode e Pillow

Essas bibliotecas apoiam a leitura e geração de imagens:

- OpenCV: processamento de imagens e câmera;
- PyZbar: leitura de códigos de barras e QR Codes;
- qrcode: geração de QR Codes;
- Pillow: abertura e criação de imagens.

### Google Books API

A Google Books API é usada para pesquisar um livro a partir do ISBN. Ela pode retornar título, autores e categorias.

A integração está no backend, mas depende da disponibilidade e da quota do serviço externo. Durante a análise, a API respondeu `HTTP 429`, que significa limite temporário de requisições.

### Chart.js, jsQR e Tabler Icons

O frontend utiliza CDNs para:

- Chart.js: gráficos;
- jsQR: leitura de QR Code no navegador;
- Tabler Icons: ícones da interface.

## 3. Estrutura do projeto

```text
backend/
  app.py                 Entrada do servidor Flask
  api/                   Rotas separadas por módulo
  data/                  Fallback JSON local
  scanner/               QR, código de barras e cartões
  utils/                 IDs, datas, Supabase e helpers
  tests/                 Testes Python
frontend/
  index.html             Estrutura da aplicação
  assets/css/main.css    Estilos
  assets/js/             Lógica do frontend
  tests/                 Teste JavaScript do scanner
database.sql             Estrutura do PostgreSQL/Supabase
```

### Backend

- [backend/app.py](backend/app.py): cria o Flask, carrega ambiente, registra blueprints e serve o frontend.
- [backend/api/auth.py](backend/api/auth.py): login e configuração do Supabase.
- [backend/api/books.py](backend/api/books.py): CRUD de livros e pesquisa ISBN.
- [backend/api/students.py](backend/api/students.py): alunos, importação CSV e acesso de bibliotecário.
- [backend/api/loans.py](backend/api/loans.py): empréstimos, devoluções e renovações.
- `rooms.py` e `genres.py`: salas e gêneros.
- [backend/api/reports.py](backend/api/reports.py): gráficos e exportações.
- [backend/scanner/routes.py](backend/scanner/routes.py): scanner, QR e cartões.
- [backend/utils/helpers.py](backend/utils/helpers.py): UUID, datas e status.
- [backend/utils/supabase_client.py](backend/utils/supabase_client.py): cliente e fallback.

### Frontend

- `index.html` contém as páginas em uma única aplicação.
- `app.js` controla a aplicação.
- `api.js` concentra as chamadas ao backend.
- `store.js` guarda os dados carregados na memória e no localStorage.
- Os arquivos em `pages/` controlam cada área.

## 4. Frontend

### Login

A tela de login possui:

- usuário;
- senha;
- botão de entrada;
- mensagem de erro;
- entrada por carteirinha QR.

Ao clicar em entrar, [app.js](frontend/assets/js/app.js) envia `POST /api/auth/login`.

### Navegação

O menu lateral possui páginas como:

- Painel;
- Empréstimos;
- Acervo;
- Gêneros;
- Alunos;
- Salas;
- Relatórios;
- Configurações.

A navegação troca a página visível sem recarregar todo o documento.

### Formulários

Os formulários são usados para cadastrar e editar:

- livros;
- alunos;
- salas;
- gêneros.

Os botões chamam funções JavaScript, que montam objetos JSON e enviam para a API.

### Como os dados aparecem?

O backend retorna JSON. O frontend salva os dados no `Store` e renderiza:

- tabelas;
- badges de status;
- cards;
- gráficos;
- mensagens de confirmação;
- estados vazios.

### Cadastro de livros por ISBN

No cadastro de livros há:

- campo ISBN/código de barras;
- botão `Ler`;
- botão `Pesquisar`;
- título;
- autor;
- gênero;
- área;
- quantidade de exemplares.

O ISBN ajuda a preencher os dados. Ele não substitui o ID único do sistema.

## 5. Backend

### O que é o backend?

O backend é a parte do sistema que roda no servidor. Ele recebe requisições, consulta dados, aplica regras e devolve respostas.

### Rotas

Uma rota é um endereço que executa uma função. Exemplos:

- `POST /api/auth/login`: autenticação;
- `GET /api/books/`: lista livros;
- `POST /api/books/`: cria livro;
- `POST /api/loans/`: cria empréstimo;
- `POST /api/loans/<id>/return`: registra devolução;
- `GET /api/health`: verifica o sistema e o banco.

### Regras de negócio existentes

- Livro precisa de título e autor.
- Aluno precisa de nome e turma.
- Empréstimo precisa de livro e aluno.
- Não é permitido emprestar quando não há exemplar disponível.
- Não é permitido devolver duas vezes o mesmo empréstimo.
- Não é permitido renovar um empréstimo já devolvido.
- O ISBN é informação bibliográfica, não identificador principal.

### Limitação importante

As rotas não verificam uma sessão confiável antes de executar operações. O frontend esconde telas conforme o papel, mas um cliente pode chamar a API diretamente. A autorização backend ainda precisa ser implementada.

## 6. Banco de dados

O schema está em [database.sql](database.sql).

### Tabelas

- `usuarios`: contas de acesso.
- `salas`: salas da instituição.
- `generos`: categorias dos livros.
- `livros`: acervo e exemplares.
- `alunos`: usuários da biblioteca.
- `emprestimos`: circulação de exemplares.
- `relatorios_mensais`: resultados agregados.

### Livro e identificadores

A tabela `livros` possui:

- `id`: UUID principal;
- `isbn`: ISBN opcional;
- `titulo`;
- `autor`;
- `area`;
- `genero_id`;
- `exemplares`;
- `exemplares_ids` e `exemplares_meta`.

O processo correto é:

```text
ISBN ajuda a encontrar os dados
ID UUID identifica o registro
ID do sistema gera o QR Code
```

### Como o sistema salva dados?

1. A rota recebe JSON.
2. O backend valida campos básicos.
3. O cliente Supabase tenta inserir ou alterar o registro.
4. Em erro classificado como offline, o backend grava em JSON local.
5. O frontend recebe o resultado e atualiza a tela.

### Limitações do banco

- RLS está habilitado, mas as policies atuais usam `true` de forma ampla.
- Usuários são inseridos com senha inicial em texto puro.
- `ON DELETE CASCADE` pode apagar histórico de empréstimos.
- Não existe fila de sincronização offline.

## 7. Funcionamento completo: cadastrar um livro com código de barras

Imagine que o bibliotecário possui um livro físico.

1. O bibliotecário entra no sistema.
2. Abre a página **Acervo**.
3. Clica em **Cadastrar livro**.
4. Clica em **Ler**.
5. O navegador pede permissão para usar a câmera.
6. O scanner tenta ler QR ou código EAN/ISBN.
7. Se necessário, a imagem é enviada para `/api/qr/decode`.
8. O ISBN lido vai para o campo do formulário.
9. O frontend chama `/api/books/isbn-lookup`.
10. O backend consulta a Google Books API.
11. Título, autor, ISBN e categorias retornadas são enviados ao frontend.
12. O usuário confere os campos e ajusta o gênero, se necessário.
13. Ao clicar em salvar, o frontend chama `POST /api/books/`.
14. O backend gera um UUID com `new_id()`.
15. O ISBN é armazenado como dado do livro.
16. Os exemplares recebem identificadores próprios.
17. O livro é inserido no Supabase ou no JSON local.
18. O QR Code é gerado a partir do ID do sistema.
19. O frontend mostra o QR e atualiza o acervo.

Se a Google Books estiver limitada, o usuário pode preencher os dados manualmente.

## 8. Lógica das principais funcionalidades

### Login

- **Começa:** usuário envia login e senha.
- **Arquivos:** `index.html`, `app.js`, `api/auth.py`.
- **Internamente:** backend procura o usuário, verifica senha e devolve o papel.
- **Resultado:** frontend mostra o painel.
- **Status:** funciona em desenvolvimento, mas precisa de sessão server-side.

### Cadastro de livro

- **Começa:** usuário abre o modal.
- **Arquivos:** `index.html`, `books.js`, `api.js`, `books.py`.
- **Internamente:** dados são validados, ID é gerado e registro é salvo.
- **Resultado:** livro, exemplares e QR.
- **Status:** funcionamento básico implementado.

### Pesquisa ISBN

- **Começa:** ISBN é digitado ou lido.
- **Arquivos:** `books.js`, `api.js`, `books.py`.
- **Internamente:** Google Books é consultada.
- **Resultado:** preenchimento automático.
- **Status:** parcial por quota externa e falta de cache.

### Scanner

- **Começa:** usuário pressiona botão da câmera.
- **Arquivos:** `qr-scanner.js`, `scanner/routes.py`.
- **Internamente:** câmera captura frames; jsQR/BarcodeDetector/Pyzbar tentam reconhecer o conteúdo.
- **Resultado:** callback recebe o código.
- **Status:** parcial; teste automatizado passou, mas falta câmera real.

### Empréstimo

- **Começa:** usuário procura livro e aluno.
- **Arquivos:** `loans.js`, `api.js`, `loans.py`.
- **Internamente:** disponibilidade é calculada e o exemplar é associado ao aluno.
- **Resultado:** empréstimo com data de devolução.
- **Status:** funcional, mas com risco de concorrência.

### Devolução

- **Começa:** usuário escolhe empréstimo ativo.
- **Internamente:** backend valida o empréstimo e grava `devolvido_em`.
- **Resultado:** exemplar volta a ficar disponível.
- **Status:** implementada, ainda precisa de testes E2E.

### Relatórios

- **Começa:** usuário abre Relatórios.
- **Internamente:** backend agrega empréstimos, livros, alunos e turmas.
- **Resultado:** gráficos, dados mensais e CSV.
- **Status:** implementado, com validação e autorização pendentes.

## 9. Status atual

### 🟢 Funcionando

- Servidor Flask e frontend servido pelo backend.
- Health check do Supabase.
- Consulta da API de livros sem login.
- Login local testado.
- CRUD básico e operações de empréstimo implementados.
- Teste JavaScript do scanner aprovado.
- IDs próprios, exemplares e QR Codes implementados.

### 🟡 Parcialmente funcionando

- Sessão: expira no frontend, mas não é validada no backend.
- Scanner: código possui vários fallbacks, mas não há teste com câmera física.
- Cadastro ISBN: implementado, mas a Google Books pode responder `HTTP 429`.
- Fallback JSON: funciona localmente, mas não sincroniza depois.
- Relatórios: existem, mas não estão protegidos por autorização real.

### 🔴 Com problema ou risco

- APIs sem autorização por requisição.
- RLS permissivo.
- Possível exposição de chave de serviço.
- Credenciais padrão e senha inicial em texto puro.
- Exclusão em cascade com risco de perder histórico.
- Concorrência na escolha de exemplares.

### ⚪ Ainda não implementado

- JWT ou sessão server-side.
- RBAC real no backend.
- Fila de sincronização offline/online.
- Cache e fallback robusto para Google Books.
- Suíte E2E completa.
- CI com pytest e testes de segurança.

## 10. Modificações já realizadas

- Correção do login e das mensagens de erro.
- Aliases para bibliotecário/biblioteca.
- Verificação com bcrypt/passlib e fallback local.
- Timeout visual de sessão de 30 minutos.
- Otimização da inicialização do scanner.
- Otimização de geração de carteirinhas.
- Melhorias no tema escuro e responsividade.
- IDs únicos para livros e exemplares.
- QR Codes para entidades e exemplares.
- Scanner com suporte a QR, EAN/ISBN e imagens de baixa qualidade.
- Cadastro automático por ISBN integrado ao modal existente.

As mudanças mais recentes de ISBN e robustez do scanner estão presentes no workspace, mas ainda aparecem como alterações locais não commitadas.

## 11. Problemas atuais

### Segurança

As APIs aceitam chamadas diretas sem comprovar usuário e papel. Isso significa que esconder o botão no frontend não impede uma requisição manual.

### Google Books

A API externa possui limite de uso. O sistema recebeu `HTTP 429` durante a análise. Sem cache e backoff, novas tentativas podem continuar falhando.

### Câmera

O backend processa frames, mas isso não prova que uma câmera física específica reconhecerá todos os códigos. Iluminação, foco, distância e qualidade do código continuam importantes.

### Dados offline

Um registro salvo no JSON durante indisponibilidade do Supabase pode não chegar ao banco depois. Isso pode criar divergência entre usuários e ambientes.

### Testes

O teste JavaScript passou, mas os testes Python não foram executados porque `pytest` não está instalado no ambiente atual.

## 12. Melhorias necessárias

- Criar autenticação confiável para cada requisição.
- Corrigir autorização de administrador e bibliotecário.
- Restringir RLS.
- Rotacionar segredos e eliminar credenciais padrão.
- Criar cache de ISBN.
- Adicionar retry com espera progressiva.
- Usar provedor alternativo ou permitir preenchimento manual claro.
- Limitar chamadas do scanner sem reconhecimento.
- Validar ISBN com dígitos verificadores.
- Usar transação na escolha de exemplares.
- Criar reconciliação Supabase/JSON.
- Substituir `except:` genérico por exceções específicas.
- Melhorar acessibilidade, mensagens e estados de carregamento.
- Adicionar pytest, CI e testes E2E.

## 13. Funcionalidades ainda não criadas

| Funcionalidade | Objetivo | Local sugerido | Prioridade | Status |
|---|---|---|---|---|
| Sessão server-side/JWT | Proteger as APIs | `backend/app.py` e middleware | Crítica | Não implementada |
| RBAC no backend | Aplicar papéis de forma real | Todos os blueprints | Crítica | Não implementada |
| RLS seguro | Proteger o Supabase | `database.sql` | Crítica | Não implementada |
| Fila offline/online | Sincronizar JSON depois | `backend/utils/` | Alta | Não implementada |
| Cache ISBN | Reduzir quota da Google Books | `backend/api/books.py` | Alta | Não implementada |
| Testes E2E | Validar fluxos completos | `backend/tests` e frontend | Alta | Não implementada |
| Auditoria | Registrar quem alterou dados | Banco e backend | Média | Não implementada |
| Limite de renovação | Aplicar regra de negócio | `loans.py` e banco | Média | Não implementada |

## 14. Funcionalidades que precisam ser modificadas

- **Autenticação:** transformar o cookie frontend em sessão assinada e verificável.
- **Configuração Supabase:** nunca devolver `SUPABASE_SERVICE_KEY` ao navegador.
- **Cadastro ISBN:** adicionar cache, backoff, validação e mensagem específica para quota.
- **Scanner:** aplicar throttle, teste físico e diagnóstico de câmera.
- **Empréstimos:** tornar escolha e gravação de exemplar atômicas.
- **Exclusão:** preservar histórico com soft delete.
- **Renovação:** definir e validar limite de renovações.
- **Fallback JSON:** criar reconciliação com conflitos explícitos.
- **Relatórios:** proteger endpoints e validar limites de consulta.

## 15. Segurança

### Login

O login ocorre no backend e não expõe senha no JavaScript. Há suporte a hashes e fallback local.

### Permissões

A interface diferencia administrador e bibliotecário, mas a API não confirma esse papel. Essa é a principal falha de segurança atual.

### Chaves e variáveis

O arquivo `backend/.env` está ignorado pelo Git, o que impede seu commit acidental. Mesmo assim, chaves compartilhadas ou expostas devem ser rotacionadas. O endpoint de configuração precisa retornar somente a chave pública.

### Banco

O banco possui RLS, chaves estrangeiras e índices, mas as policies permissivas anulam grande parte da proteção. As policies precisam distinguir usuários autenticados, papéis e operações.

### Validação

Existem validações básicas para campos obrigatórios. Ainda faltam validações uniformes para datas, ISBN, CSV, limites numéricos, tamanhos e autorização.

## 16. Testes

### Já testado

- Teste JavaScript do callback do scanner: aprovado.
- Sintaxe JavaScript: aprovada.
- Compilação dos módulos Python alterados: aprovada em validações anteriores.
- Health check: HTTP 200 e banco conectado.
- Consulta de livros sem login: HTTP 200.
- Consulta REST real à tabela `livros`: HTTP 200.
- Pesquisa Google Books: identificada limitação HTTP 429.

### Ainda precisa ser testado

- Toda a suíte Python com `pytest` instalado.
- Login inválido e acesso por cada papel.
- API com e sem sessão.
- Policies RLS reais.
- CRUD completo de cada entidade.
- Concorrência de exemplares.
- Devoluções e renovações inválidas.
- Scanner com câmera real, EAN-13, ISBN-10 e baixa iluminação.
- Fluxo completo ISBN até salvar o livro.
- Responsividade e acessibilidade.
- Falhas externas, timeout, quota e fallback.

## 17. Próximos passos

### Primeiro: segurança crítica

1. Rotacionar segredos.
2. Remover credenciais padrão.
3. Criar sessão confiável.
4. Proteger todas as rotas.
5. Corrigir RLS.

### Segundo: integridade dos dados

1. Proteger concorrência de exemplares.
2. Evitar exclusão destrutiva.
3. Criar reconciliação offline.
4. Padronizar erros e validações.

### Terceiro: ISBN e scanner

1. Adicionar cache.
2. Implementar backoff para 429.
3. Criar fallback de provedor.
4. Testar câmeras reais.
5. Melhorar feedback ao usuário.

### Quarto: testes e qualidade

1. Adicionar pytest às dependências.
2. Criar CI.
3. Criar testes E2E.
4. Testar segurança, concorrência e responsividade.

### Quinto: produção

1. Desativar debug.
2. Usar WSGI de produção.
3. Configurar secrets fora do repositório.
4. Configurar backup e monitoramento.
5. Publicar somente após resolver prioridades críticas e altas.

## Glossário

- **Frontend:** parte visual que roda no navegador.
- **Backend:** parte do sistema que roda no servidor.
- **API:** conjunto de caminhos usados para comunicação entre sistemas.
- **Banco de dados:** local organizado onde os registros são armazenados.
- **Rota:** endereço do backend que executa uma função.
- **Endpoint:** uma rota específica de uma API.
- **CRUD:** Create, Read, Update e Delete; criar, consultar, alterar e excluir.
- **Deploy:** publicação do sistema para uso em um ambiente.
- **Servidor:** processo que recebe requisições e envia respostas.
- **Autenticação:** confirmação de quem é o usuário.
- **Autorização:** confirmação do que o usuário pode fazer.
- **JSON:** formato de texto usado para trocar dados estruturados.
- **HTTP:** protocolo usado nas requisições web.
- **Requisição:** pedido enviado por um cliente ao servidor.
- **Resposta:** resultado devolvido pelo servidor.
- **UUID:** identificador único, normalmente representado por uma sequência longa.
- **ISBN:** código bibliográfico de um livro; neste projeto não é o ID principal.
- **QR Code:** imagem que guarda um texto ou identificador legível por câmera.
- **EAN:** formato de código de barras usado em produtos, inclusive livros.
- **RLS:** Row Level Security; regras do banco que limitam quais linhas podem ser acessadas.
- **Fallback:** caminho alternativo usado quando o caminho principal falha.
- **Offline:** funcionamento sem conexão com o banco remoto.
- **E2E:** teste de ponta a ponta, simulando o fluxo completo do usuário.
- **HTTP 429:** resposta que indica excesso ou limite de requisições.
- **CORS:** regra que controla quais origens podem chamar uma API.
- **CSP:** política que restringe scripts, imagens e conexões permitidos no navegador.

## Conclusão final

O sistema já possui uma base funcional ampla e pode ser usado como aplicação de desenvolvimento. O fluxo de biblioteca, identificação de livros, QR Codes e cadastro por ISBN está representado no código. Porém, a segurança atual depende demais do frontend, e a integração Google Books depende de uma quota externa que já apresentou `HTTP 429`.

Para estudar e apresentar o projeto, é importante explicar a diferença entre:

- **implementado:** existe no código;
- **funcionando:** foi validado em algum cenário;
- **parcial:** existe, mas tem limitações;
- **pendente:** ainda precisa de desenvolvimento;
- **não implementado:** não há código correspondente.

O próximo passo técnico mais importante é proteger o backend e o banco antes de tratar o sistema como pronto para produção.
