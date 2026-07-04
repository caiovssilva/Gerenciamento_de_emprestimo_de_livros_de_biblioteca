# Relatório 1 — Implementação feita

## 1. Visão geral
Este relatório documenta as melhorias aplicadas no sistema de gerenciamento de empréstimo de livros, com foco em QR, controle de empréstimos, relatórios e ajuste de identidade visual da biblioteca.

## 2. O que foi corrigido e implementado

### 2.1. Fluxo de QR e identificação única
- Cada aluno agora recebe um identificador único (`qr_id`) para o QR de acesso.
- Cada livro novo recebe um identificador único (`qr_id`) para o QR do acervo.
- Cada exemplar passou a receber um identificador próprio, permitindo identificar cada cópia de forma distinta mesmo quando o livro ou o autor sejam iguais.
- O scanner passou a reconhecer QR único de aluno, QR único de livro e QR de exemplar específico.

### 2.2. Controle de empréstimo e devolução
- O sistema agora trata o exemplar como uma unidade específica.
- Quando um exemplar está emprestado, ele fica associado ao aluno responsável.
- A devolução só é concluída quando a carteirinha do aluno correto é lida ou o fluxo de devolução é acionado com o aluno correspondente.
- Se outro aluno tentar devolver, o sistema bloqueia e informa que o exemplar pertence a outro responsável.
- O painel passou a exibir o nome do aluno responsável quando o exemplar está emprestado.

### 2.3. Relatórios
- Foi adicionado um novo relatório de exportação em CSV com o status de alunos por empréstimo:
  - quem pegou o livro,
  - quem está devendo,
  - quem já devolveu.
- O endpoint novo está disponível em `/api/reports/export/student-status`.

### 2.4. Branding e URL da biblioteca
- O texto “Biblioteca Narceu de Paiva Filho” foi aplicado na interface principal.
- O nome da biblioteca foi ajustado nos cartões e na tela de login.
- A identidade visual da biblioteca foi padronizada para o nome oficial.

## 3. Arquivos alterados
- backend/api/books.py
- backend/api/students.py
- backend/api/loans.py
- backend/api/reports.py
- backend/scanner/routes.py
- frontend/index.html
- frontend/assets/js/app.js
- backend/tests/test_reports_student_status.py
- backend/tests/test_unique_identifiers.py

## 4. Validação executada
- Verificação de sintaxe dos módulos Python alterados com `python -m py_compile`.
- Checagem do fluxo principal do frontend via `node --check` para o controller principal.

## 5. Observação de execução
- O servidor foi iniciado com sucesso localmente em `http://127.0.0.1:5000` após instalação das dependências do backend.
