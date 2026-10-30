# Sistema de Gerenciamento de Empréstimos da Biblioteca

Aplicação web para administração de acervo, alunos, empréstimos e devoluções,
com relatórios, exportação CSV e leitura/geração de QR Codes.

## Tecnologias

- Backend: Python, Flask e Supabase (PostgreSQL).
- Frontend: HTML, CSS e JavaScript.
- Testes: pytest no backend e `node --test` no frontend.

## Requisitos

- Python 3.11 ou superior.
- Git.
- Node.js para executar os testes JavaScript.
- Projeto Supabase configurado para executar operações que dependem do banco.

## Executar localmente

1. Crie e ative um ambiente virtual:

   ```bash
   python -m venv .venv
   ```

   Linux/macOS:

   ```bash
   source .venv/bin/activate
   ```

   Windows PowerShell:

   ```powershell
   .venv\Scripts\Activate.ps1
   ```

2. Instale as dependências:

   ```bash
   pip install -r backend/requirements.txt
   ```

3. Configure as variáveis de ambiente do backend (por exemplo,
   `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` e `SECRET_KEY`) como variáveis do
   processo ou em `backend/.env`.

   O arquivo [.env.example](.env.example) é apenas um modelo de referência na
   raiz; o backend carrega `backend/.env`. Se já existir um `.env`, preserve-o:
   não o substitua nem o versione. Nunca publique chaves ou segredos no
   frontend, neste README ou em logs.

4. Inicie o servidor:

   ```bash
   python backend/app.py
   ```

5. Abra <http://localhost:5000>.

O Flask serve a aplicação frontend e a API. A API depende da conexão Supabase
para as operações de negócio; quando o banco não estiver disponível, essas
rotas podem retornar `503`. A rota `/api/health` verifica se o Flask responde;
`/api/ready` verifica a prontidão do banco.

## Testes

Na raiz do repositório:

```bash
python -m pytest backend/tests
node --test frontend/tests/*.test.js
```

`pytest` precisa estar instalado no ambiente Python. Os testes podem usar mocks
e não substituem validação com banco Supabase isolado ou navegador real.

Na última execução documentada em 30/10/2026, a suíte Python teve 180 aprovados
e 12 falhos; os testes Node tiveram 7 aprovados. Consulte
[as evidências e limitações da auditoria](docs/auditoria-final/13_EVIDENCIAS.md)
antes de interpretar esses resultados.

## Estrutura principal

```text
backend/             API Flask, integrações e testes Python
frontend/            interface web, módulos JavaScript e testes Node
database.sql         script SQL do schema e políticas do Supabase
docs/auditoria-final/ resultados e limites da auditoria mais recente
docs/relatorio-tecnico/ documentação técnica do projeto
```

## Banco de dados

O arquivo [database.sql](database.sql) descreve a estrutura e as políticas do
banco. **Ele contém comandos destrutivos (`DROP ... CASCADE`)**: revise-o e faça
backup antes de qualquer execução. Não o execute em uma base com dados que
precisam ser preservados.

## Segurança e limitações conhecidas

Este README não certifica o sistema para produção. A auditoria estática
registrou questões de autorização, configuração Supabase, segredo de sessão,
QR e outros pontos ainda não validados dinamicamente. Use um ambiente isolado,
credenciais de menor privilégio e segredos fortes; não exponha uma chave
`service_role` ao navegador.

Consulte [a conclusão da auditoria](docs/auditoria-final/15_CONCLUSAO_DA_VALIDACAO.md)
e [a análise de segurança](docs/auditoria-final/09_AUDITORIA_DE_SEGURANCA.md)
para detalhes e limitações.

## Documentação

- [Índice dos relatórios finais](docs/auditoria-final/00_RESUMO_DA_AUDITORIA.md)
- [README do backend](backend/README.md)
- [Andamento da auditoria](ANDAMENTO_AUDITORIA.md)
