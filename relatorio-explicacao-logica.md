# Relatório de explicação da lógica do sistema

## 1. Visão geral
Este projeto é uma aplicação web para gerenciamento de empréstimo de livros em uma biblioteca. A estrutura é dividida em:

- Backend em Flask, responsável por autenticação, regras de negócio, persistência e exportação de relatórios.
- Frontend em HTML, CSS e JavaScript puro, responsável pela interface do usuário e pela interação com a API.
- Dados locais em JSON, com fallback para funcionamento mesmo quando a conexão com o banco/Supabase não estiver disponível.

## 2. Arquitetura do sistema

### Backend
O backend é iniciado por [backend/app.py](backend/app.py). Ele:
- cria a aplicação Flask;
- registra os blueprints das principais áreas do sistema;
- define regras de segurança e tratamento de erros;
- serve o frontend e expõe endpoints da API.

### Frontend
O frontend é servido pelo Flask e é composto por:
- [frontend/index.html](frontend/index.html): estrutura das páginas e componentes da interface.
- [frontend/assets/css/main.css](frontend/assets/css/main.css): estilização e responsividade.
- [frontend/assets/js/app.js](frontend/assets/js/app.js): lógica principal da interface.
- [frontend/assets/js/api.js](frontend/assets/js/api.js): comunicação com o backend.
- [frontend/assets/js/store.js](frontend/assets/js/store.js): cache local em navegador.

## 3. Lógica principal do sistema

### 3.1 Autenticação
A autenticação é feita no endpoint de login em [backend/api/auth.py](backend/api/auth.py).

Fluxo:
1. O usuário envia login e senha pela interface.
2. O backend valida as credenciais.
3. Se estiverem corretas, retorna um token de acesso implícito na resposta da API.
4. O frontend recebe a resposta e habilita o painel principal.

A aplicação também suporta login por QR Code, usado para autenticação administrativa ou identificação de alunos.

### 3.2 Cadastro e consulta de livros
A lógica de livros está em [backend/api/books.py](backend/api/books.py).

Ela faz:
- leitura de livros;
- filtro por texto e gênero;
- criação, atualização e exclusão de itens;
- geração de exemplares e códigos QR associados.

### 3.3 Empréstimos e devoluções
A lógica de empréstimos está em [backend/api/loans.py](backend/api/loans.py).

Fluxo de empréstimo:
1. O usuário seleciona um livro e um exemplar disponível.
2. O sistema verifica se o exemplar não está emprestado.
3. O sistema valida se o aluno existe.
4. Cria o empréstimo com data, prazo de devolução e status inicial.

Fluxo de devolução:
1. O sistema identifica o empréstimo ativo.
2. Marca a data de devolução.
3. Libera o exemplar para uso futuro.

Também há suporte para renovação de prazo.

### 3.4 Relatórios
A lógica de relatórios está em [backend/api/reports.py](backend/api/reports.py).

A aplicação gera:
- resumo de empréstimos ativos, atrasados e devolvidos;
- ranking de livros mais emprestados;
- relatórios por turma;
- exportações em CSV.

### 3.5 Persistência
O projeto usa:
- arquivos JSON em [backend/data](backend/data) como base local;
- tentativa de integração com Supabase via cliente em [backend/utils/supabase_client.py](backend/utils/supabase_client.py).

Se a conexão com o banco falhar, o sistema continua funcionando com o arquivo local.

## 4. Como o frontend funciona
O arquivo [frontend/assets/js/app.js](frontend/assets/js/app.js) atua como controlador principal.

Ele é responsável por:
- controlar o login e logout;
- navegar entre páginas;
- renderizar dashboards, listas e formulários;
- chamar a API para criar e atualizar registros;
- atualizar os gráficos e a interface após cada operação.

O arquivo [frontend/assets/js/store.js](frontend/assets/js/store.js) mantém um estado local em memória e no navegador, reduzindo a necessidade de novas requisições em cada ação.

## 5. Pontos fortes do projeto
- Arquitetura simples e fácil de entender.
- Fallback local robusto.
- Interface de gestão completa para biblioteca.
- Suporte a QR Code para leitura e identificação.
- Relatórios prontos para exportação.

## 6. Observação importante
A lógica atual está bem estruturada para um sistema de gestão bibliotecária simples e funcional. As mudanças realizadas foram focadas em experiência visual e responsividade, sem alterar o fluxo principal de negócio.
