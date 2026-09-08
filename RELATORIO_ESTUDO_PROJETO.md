# Relatório de Estudo do Projeto

## 1. Visão geral

Este projeto é um sistema web de gerenciamento de biblioteca escolar. Ele permite:

- autenticar administradores e bibliotecários;
- cadastrar, editar, listar e excluir livros;
- cadastrar alunos, salas e gêneros;
- registrar, devolver e renovar empréstimos;
- ler QR Codes e códigos de barras;
- gerar QR Codes e carteirinhas;
- exibir relatórios e exportar CSV;
- usar Supabase como banco principal e arquivos JSON como fallback offline.

### Tecnologias

- **Backend:** Python, Flask, Flask-CORS.
- **Banco:** Supabase/PostgreSQL acessado pela API do Supabase.
- **Frontend:** HTML, CSS e JavaScript sem framework.
- **QR e imagem:** qrcode, Pillow, OpenCV, pyzbar e bibliotecas do navegador.
- **Testes:** pytest no backend e Node.js no teste do scanner frontend.
- **Automação:** GitHub Actions em `.github/workflows`.

## 2. Ordem recomendada para estudar

Estude nesta sequência:

1. `backend/app.py`: entrada do servidor, registro das rotas e arquivos estáticos.
2. `frontend/index.html`: telas, botões e carregamento dos scripts.
3. `frontend/assets/js/api.js`: como o frontend chama o backend.
4. `backend/api/_helpers.py`: leitura JSON, validação de tabelas e fallback.
5. `backend/utils/supabase_client.py`: conexão online e modo offline.
6. `backend/api/auth.py`: login e permissões.
7. `backend/api/books.py`: CRUD de livros e consulta de ISBN.
8. `backend/api/students.py`: cadastro e acesso de bibliotecário.
9. `backend/api/loans.py`: regra principal de empréstimo, devolução e renovação.
10. `backend/scanner/routes.py` e `frontend/assets/js/qr-scanner.js`: QR, câmera e códigos de barras.
11. `backend/api/reports.py`: relatórios e exportações.
12. `frontend/assets/js/app.js`, `store.js`, `utils.js` e `pages/*.js`: comportamento da interface.
13. `backend/tests`: como cada regra é verificada.
14. `.github/workflows`: automações agendadas.
15. `.venv`: ambiente de execução e dependências, não lógica do sistema.

Não comece pelo `.venv`: ele contém pacotes instalados, não o código de negócio.

## 3. Fluxo completo de uma requisição

```text
Usuário no navegador
    -> frontend/index.html
    -> JavaScript chama API em /api/...
    -> backend/app.py recebe a requisição
    -> blueprint correto trata a rota
    -> Supabase é consultado
    -> se necessário, JSON local é usado como fallback
    -> resposta JSON volta ao frontend
    -> Store e página atualizam a tela
```

Exemplo de criação de livro:

```text
books.js
  -> API.books.create()
  -> POST /api/books/
  -> books.create_book()
  -> gera UUID e exemplares
  -> salva no Supabase ou livros.json
  -> gera QR Code
  -> retorna o livro criado
```

## 4. Backend: arquivo por arquivo

### `backend/app.py`

É o ponto de entrada do servidor Flask.

Responsabilidades:

- carregar `backend/.env` com `load_dotenv`;
- configurar Flask e CORS;
- registrar os blueprints `/api/auth`, `/api/books`, `/api/students`, `/api/loans`, `/api/reports`, `/api/rooms`, `/api/genres` e `/api/qr`;
- servir o frontend pela mesma porta;
- fornecer `/api/health`;
- tratar erros HTTP e erros inesperados;
- aplicar cabeçalhos de segurança, incluindo CSP.

Comando de execução:

```bash
./.venv/bin/python backend/app.py
```

### `backend/api/_helpers.py`

Funções compartilhadas entre as APIs:

- `read_json`: lê arquivos JSON com proteção contra arquivo ausente ou inválido;
- `write_json`: grava dados locais;
- `table_ok`: verifica se uma tabela Supabase existe;
- `has_deleted_at`: verifica suporte a soft delete;
- `is_offline_error`: identifica erros que permitem fallback local.

### `backend/api/auth.py`

Implementa:

- login por usuário e senha;
- busca do usuário no Supabase;
- fallback para usuários locais;
- identificação de administrador e bibliotecário;
- entrega da configuração pública necessária ao frontend.

Estude especialmente o tratamento de senha e a diferença entre credencial de usuário, chave pública e chave de serviço.

### `backend/api/books.py`

Implementa o acervo:

- listagem e filtros por título, autor, ISBN e gênero;
- consulta de livro por ID, ISBN ou exemplar;
- criação com UUID próprio;
- geração dos exemplares físicos;
- atualização e exclusão;
- consulta de ISBN pela Google Books e fallback externo.

O ISBN é metadado bibliográfico. O identificador principal do sistema continua sendo o UUID gerado por `new_id()`.

A chave da Google Books é lida por `GOOGLE_BOOKS_API_KEY`. Ela deve permanecer em variável de ambiente e nunca no frontend ou no código.

### `backend/api/students.py`

Implementa:

- listagem, busca, criação, edição e exclusão de alunos;
- importação de alunos por CSV;
- concessão e revogação do acesso de bibliotecário;
- fallback para `backend/data/alunos.json`.

### `backend/api/loans.py`

É o módulo mais importante das regras de negócio.

Estude:

- validação de aluno e livro;
- cálculo de exemplares disponíveis;
- prevenção de empréstimo sem disponibilidade;
- criação de empréstimo;
- devolução;
- renovação;
- status ativo, atrasado e devolvido.

### `backend/api/genres.py`

CRUD de gêneros. Gêneros possuem nome, cor e ícone e são associados aos livros.

### `backend/api/rooms.py`

CRUD de salas. Também participa da montagem dos dados de alunos e do cálculo de ocupação.

### `backend/api/reports.py`

Gera:

- resumo geral;
- livros mais emprestados;
- empréstimos por turma;
- dados mensais;
- CSV de atrasados, histórico, livros, turmas e situação de alunos.

### `backend/scanner/routes.py`

Implementa o scanner no servidor e as operações de QR:

- `/api/qr/decode`: recebe imagem base64 ou arquivo;
- `/api/qr/generate`: gera QR Code;
- `/api/qr/card/*`: gera carteirinhas/cartões;
- `/api/qr/login`: resolve login por QR;
- `/api/qr/start`, `/stop`, `/result` e `/status`: scanner com OpenCV no servidor.

O módulo tenta pyzbar/OpenCV e depois `QRCodeDetector`. Também resolve o código para livro, exemplar, aluno ou administrador.

### `backend/utils/helpers.py`

Funções pequenas e fundamentais:

- `new_id`: gera UUID;
- `today_str`: data atual;
- `add_days`: calcula vencimento;
- `days_until`: calcula dias restantes;
- `loan_status`: retorna `active`, `overdue` ou `returned`.

### `backend/utils/supabase_client.py`

É a camada de acesso ao banco.

Fluxo:

1. lê `SUPABASE_URL` e `SUPABASE_SERVICE_KEY` ou `SUPABASE_KEY`;
2. cria o cliente Supabase;
3. reutiliza a conexão enquanto ela funciona;
4. se houver falha de rede, entra em modo offline;
5. após uma janela de recuperação, tenta conectar novamente;
6. APIs usam arquivos JSON quando o banco não está disponível.

## 5. Dados locais do backend

A pasta `backend/data/` contém o fallback offline:

- `livros.json`: livros, ISBN, exemplares e QR;
- `alunos.json`: alunos, turmas e carteirinhas;
- `emprestimos.json`: histórico e vencimentos;
- `generos.json`: categorias dos livros;
- `salas.json`: salas e capacidade.

Esses arquivos são úteis para estudar o formato dos dados e testar sem banco, mas a execução online usa o Supabase quando disponível.

## 6. Frontend que conversa com o backend

- `frontend/index.html`: estrutura da SPA, botões e campos.
- `assets/js/api.js`: cliente HTTP e objeto `API`.
- `assets/js/app.js`: login, navegação, empréstimos e resolução de QR.
- `assets/js/store.js`: estado dos dados no navegador.
- `assets/js/utils.js`: DOM, datas, modais, mensagens e utilitários.
- `assets/js/charts.js`: gráficos.
- `assets/js/qr-scanner.js`: câmera do navegador, foco suportado e decodificação local.
- `assets/js/pages/books.js`: tela de livros e consulta ISBN.
- `assets/js/pages/students.js`: tela de alunos e histórico.
- `assets/js/pages/loans.js`: tela de empréstimos.
- `assets/js/pages/rooms.js`: tela de salas.
- `assets/js/pages/genres.js`: tela de gêneros.
- `assets/css/main.css`: aparência e responsividade.

Para entender qualquer botão, siga: HTML do botão -> função JavaScript -> `API.*` -> rota Flask -> persistência -> atualização do Store/tela.

## 7. Testes do backend

Arquivos em `backend/tests/`:

- `test_auth_librarian_login.py`: login de administrador, bibliotecário e fallback local;
- `test_books_fallback.py`: livros locais quando Supabase falha;
- `test_card_generation_performance.py`: velocidade de geração de carteirinhas;
- `test_env_loading.py`: carregamento do `.env` a partir de qualquer diretório;
- `test_qr_id_resolution.py`: criação, busca e resolução de QR de aluno/livro;
- `test_reports_student_status.py`: exportação da situação dos alunos;
- `test_supabase_reconnect.py`: cache, modo offline e reconexão;
- `test_unique_identifiers.py`: IDs e QR diferentes para livros iguais.

Comandos:

```bash
./.venv/bin/python -m pytest -q backend/tests
./.venv/bin/python -m compileall -q backend
```

O teste de performance pode variar conforme a máquina. Uma falha nesse teste não significa necessariamente falha funcional.

O teste frontend atual é:

```bash
node --test frontend/tests/qr-scanner.test.js
```

Ele valida o callback do scanner e a aplicação de foco contínuo simulada. Não substitui teste físico em celular.

## 8. `.venv`: o que estudar e o que não estudar

`.venv/` é um ambiente virtual Python. Ele contém:

- `.venv/bin`: executáveis, como Python, pytest e Flask;
- `.venv/lib/python3.12/site-packages`: bibliotecas instaladas;
- `.venv/include`: arquivos de desenvolvimento;
- `.venv/share`: metadados e manuais.

Pacotes importantes:

- Flask e Werkzeug: servidor web;
- Flask-Cors: CORS;
- python-dotenv: `.env`;
- supabase: banco;
- qrcode e Pillow: geração de imagens;
- OpenCV, NumPy e pyzbar: leitura de códigos;
- pytest: testes.

Não edite arquivos dentro de `.venv` e não faça commit dela. Se precisar recriar:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

## 9. `.github`: automações

### `.github/workflows/Manter render ativo.yml`

Executa a cada dez minutos ou manualmente e chama `/api/health` do Render. Serve para evitar que o serviço entre em suspensão.

### `.github/workflows/manter_supabase_ativo.yml`

Executa diariamente ou manualmente. Usa `SUPABASE_URL` e `SUPABASE_ANON_KEY` armazenados nos **GitHub Secrets** e faz uma consulta simples à tabela `livros`.

O workflow não contém as credenciais diretamente. Secrets devem ser configurados em:

```text
GitHub -> Settings -> Secrets and variables -> Actions
```

## 10. Banco e `database.sql`

`database.sql` descreve a estrutura inicial do banco. Estude as tabelas e compare com os campos usados nos módulos:

- `livros`;
- `alunos`;
- `emprestimos`;
- `salas`;
- `generos`;
- usuários/autenticação, conforme o esquema.

Uma boa prática é comparar cada campo do SQL com os payloads dos métodos `POST` e `PUT` das APIs.

## 11. Segurança importante

- Nunca faça commit de `backend/.env`.
- Nunca coloque chaves do Supabase ou Google Books no frontend.
- Como credenciais reais foram expostas durante esta conversa, revogue-as e gere novas chaves.
- Use `backend/.env.example` apenas como modelo sem valores reais.
- Restrinja chaves de API ao serviço necessário.
- Em produção, substitua a `SECRET_KEY` padrão.
- O servidor Flask de desenvolvimento não deve ser usado como servidor de produção.

## 12. Plano de estudo prático

### Etapa 1: executar

1. Ative o `.venv`.
2. Execute `backend/app.py`.
3. Abra `http://localhost:5000`.
4. Acesse `/api/health`.

### Etapa 2: observar

1. Abra o DevTools do navegador.
2. Faça login.
3. Observe as chamadas `/api/auth/login`, `/api/books/`, `/api/students/` e `/api/loans/`.
4. Compare a requisição com a rota correspondente no Flask.

### Etapa 3: seguir um caso completo

Estude o fluxo de criar livro:

```text
index.html -> books.js -> api.js -> books.py -> supabase_client.py -> Supabase
```

Depois repita para:

- criar aluno;
- criar empréstimo;
- devolver livro;
- escanear QR;
- gerar relatório.

### Etapa 4: testar falhas

1. Teste ISBN inválido.
2. Teste Supabase indisponível e observe o JSON local.
3. Teste código QR desconhecido.
4. Teste empréstimo sem exemplares disponíveis.
5. Teste devolução duplicada.
6. Teste acesso de bibliotecário.

### Etapa 5: modificar com segurança

Antes de qualquer mudança:

1. identifique a rota ou função responsável;
2. leia o teste relacionado;
3. faça a menor alteração possível;
4. execute o teste específico;
5. execute a suíte completa;
6. verifique `git diff --check`.

## 13. Perguntas para verificar se você entendeu

1. Qual arquivo registra os blueprints no Flask?
2. Como o frontend descobre a URL da API?
3. O que acontece quando o Supabase fica offline?
4. Qual é a diferença entre ID do livro, ISBN e QR do exemplar?
5. Onde a regra de disponibilidade de exemplares é aplicada?
6. Como um aluno vira bibliotecário?
7. Quais rotas geram relatórios?
8. Por que `.venv` não deve ser commitado?
9. Onde os workflows do GitHub guardam credenciais?
10. Qual teste comprova que IDs de livros iguais continuam distintos?

Se você conseguir responder essas perguntas e traçar o fluxo de uma criação de empréstimo do navegador até o Supabase, já terá entendido a arquitetura principal do projeto.