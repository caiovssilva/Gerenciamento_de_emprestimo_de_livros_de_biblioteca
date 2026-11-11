# 18 — Glossário técnico

| Termo | Significado e uso neste projeto |
|---|---|
| API | Interface que permite frontend chamar operações Flask. |
| Endpoint | URL/método específico, como `GET /api/books/`. |
| HTTP | Protocolo de requisição/resposta entre browser e Flask. |
| JSON | Formato de dados de request/response e arquivos locais. |
| Frontend | HTML/CSS/JS executados no navegador. |
| Backend | Aplicação Python/Flask, regras e acesso ao banco. |
| Framework | Estrutura que oferece ciclo de requisição e roteamento; Flask é o framework backend. |
| Biblioteca | Código reutilizável, como Pillow ou Supabase Python. |
| Blueprint | Grupo modular de rotas Flask registrado com prefixo. |
| Requisição | Método, URL, headers e body enviados pelo cliente. |
| Resposta | Status HTTP, headers e body retornados pelo servidor. |
| Função | Bloco reutilizável de lógica; ex. `_create_loan_record`. |
| Classe | Estrutura que reúne estado/métodos; ex. `SupabaseTable`. |
| Módulo | Arquivo Python/JS que agrupa código. |
| Variável de ambiente | Configuração fornecida fora do código, como `SUPABASE_URL`. |
| `.env` | Arquivo local de chave/valor; o real não foi lido nesta auditoria. |
| `.env.example` | Modelo sem credenciais reais; foi criado na raiz. |
| Secret | Valor sensível injetado por Codespaces/GitHub/Render sem versioná-lo. |
| Autenticação | Verifica identidade (login, senha, cartão). |
| Autorização | Decide se a identidade pode executar uma ação; não há gate geral em todas as rotas. |
| Sessão | Estado associado ao navegador; Flask assina cookie com `SECRET_KEY`. |
| Bearer token | Token enviado em `Authorization`; usado no autoatendimento. |
| Banco relacional | Dados em tabelas conectadas por chaves; aqui PostgreSQL/Supabase. |
| Chave primária | Identificador único de linha; geralmente UUID no SQL. |
| Chave estrangeira | Restrição que liga linhas, por exemplo empréstimo a aluno/livro. |
| RLS | Row Level Security do PostgreSQL; políticas do script não restringem ownership. |
| ORM | Mapeia objetos a tabelas; não foi encontrado. O projeto usa cliente Supabase explícito. |
| CRUD | Create, Read, Update, Delete; operações presentes nos cadastros. |
| Middleware | Código aplicado antes da rota; `before_request` valida sessão/disponibilidade. |
| Fallback | Caminho alternativo após falha, como JSON local; não é garantia de offline. |
| Cache | Resultado mantido temporariamente; consulta ISBN tem cache em memória. |
| Teste unitário | Verifica função pequena isolada, muitas vezes com mocks. |
| Teste de integração | Verifica comunicação entre componentes; Supabase real não foi integrado nesta execução. |
| Teste funcional | Verifica fluxo observável de uma funcionalidade. |
| Mock | Objeto substituto de serviço real; não confirma rede nem RLS. |
| Deploy | Publicação em ambiente hospedado; Render aparece na configuração, não foi acessado. |
| WSGI | Interface padrão para servir app Python; Gunicorn é servidor WSGI. |
| CSV | Formato tabular usado em exports de relatório. |
| QR Code | Código bidimensional para IDs, carteirinhas e exemplares. |
| ISBN | Identificador bibliográfico validado por checksum. |
| CSP | Content Security Policy do browser; há política com `unsafe-inline`. |
| CORS | Política de acesso cross-origin; configurada com origem `*`. |
| CSRF | Requisição forjada usando sessão da vítima; token não foi encontrado. |
| XSS | Injeção de script em conteúdo visualizado; `innerHTML` com dados é risco. |
| Transação | Grupo atômico de operações no banco; fluxo de disponibilidade e INSERT não é transacional no código. |
| Migration | Alteração incremental versionada de schema; não identificada. |
