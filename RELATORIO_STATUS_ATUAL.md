# Relatório 3 - Estado Atual do Projeto e Pitch Aprimorado

## 1. Estado atual do projeto

### Contexto do branch
- Branch atual: `fix/login-error-message`
- Comparado ao `origin/main`, o branch tem 12 commits adicionais.
- Foram alterados 52 arquivos, incluindo backend, frontend, documentação e testes.
- O projeto está em um estágio avançado de desenvolvimento e integração.

### O que já está funcionando
- Backend Flask funcionando como servidor principal e fornecendo a API REST.
- Frontend SPA em JavaScript puro que consome a API e renderiza tela de biblioteca.
- Autenticação de usuários com login por credenciais e login por QR Code de carteirinha.
- Cadastro e gerenciamento de livros, alunos, salas e gêneros.
- Registro e controle de empréstimos, devoluções e renovações.
- Relatórios visuais e exportação de dados em CSV.
- Suporte offline via arquivos JSON locais quando o Supabase não está disponível.
- Scanner de QR Code integrado ao fluxo de biblioteca.

### Componentes que comprovam a funcionalidade
- `backend/app.py` serve o frontend e gerencia rotas principais.
- `backend/api/auth.py` trata autenticação e configuração Supabase.
- `backend/api/books.py`, `students.py`, `loans.py`, `genres.py`, `rooms.py`, `reports.py` fornecem a lógica de negócio.
- `backend/scanner/routes.py` adiciona suporte a QR Code no servidor.
- `frontend/assets/js/app.js` gerencia o comportamento principal da aplicação.
- `frontend/assets/js/api.js` abstrai chamadas REST para o backend.
- `frontend/assets/js/qr-scanner.js` implementa leitura de QR no navegador.
- `backend/utils/supabase_client.py` garante fallback offline quando o Supabase está indisponível.

### Principais pontos fortes atuais
- Arquitetura modular clara, com API separada por recurso.
- O sistema funciona sem uma base de dados externa, o que é excelente para testes e uso local.
- UI orientada para as necessidades escolares: empréstimos, devoluções, histórico e relatórios junto com a criação e uso de carteirnhas para identificação de Alunos e Livros.
- Permissões de usuário já diferenciadas entre administrador e bibliotecário.
- A documentação acompanha o desenvolvimento com guias, relatórios e testes.

### Principais riscos ou melhorias necessárias
- A autenticação ainda não é ideal para produção: falta token seguro/JWT ou sessão consolidada no backend.
- CORS está configurado como aberto (`origins: *`), o que deve ser refinado antes de colocar em produção.
- A segurança de senha usa SHA-256 + salt em vez de um algoritmo adaptativo mais robusto.
- O fallback offline em JSON local precisa de controle melhor de concorrência e integridade de dados.
- Dependências do scanner podem não estar instaladas por padrão, o que exige cuidado ao configurar o ambiente.
- Ainda faltam testes de integração do frontend para validar fluxos completos.
-configurar e verificar se os IDs são diferentes nos livros, evitando erros na parte de empréstimo 

### A fazer em curto prazo
1. Revisar o fluxo de autenticação para usar sessões seguras ou JWT.
2. Limitar CORS a domínios confiáveis quando for implantar em produção.
3. Documentar claramente as dependências necessárias para o scanner QR.
4. Adicionar testes de integração para páginas críticas como login, empréstimo e devolução.
5. Avaliar a migração de SHA-256 para bcrypt ou argon2 no backend.

---

