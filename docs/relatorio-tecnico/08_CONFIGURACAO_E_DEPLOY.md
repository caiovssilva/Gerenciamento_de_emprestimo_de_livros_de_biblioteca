# 08 — Configuração e deploy

## Execução local descrita

O README sugere Python 3.11+, instalação de `backend/requirements.txt` e
`python backend/app.py`. O Flask escolhe `PORT`, depois `FLASK_PORT`, depois
5000; o modo debug é derivado de `FLASK_ENV == "development"`.

## Deploy documentado

`backend/README.md` descreve Render com raiz do repositório, build
`pip install -r requirements.txt`, inicialização
`gunicorn --chdir backend app:app` e health check `/api/health`. Para operação,
informa variáveis Supabase e `SECRET_KEY`. O workflow de manutenção consulta uma
URL Render fixa a cada 10 minutos. Isso documenta intenção/configuração, não prova
que serviço remoto está no ar.

## Supabase

`/api/health` não depende do banco; `/api/ready` consulta `livros` e responde
503 sem conexão. A inicialização Flask não exige conexão imediata, mas o
middleware bloqueia muitas APIs de negócio quando o Supabase não responde.

## Segredos e ambiente

- Preferir Secrets de Codespaces/Render/GitHub Actions.
- `SECRET_KEY` não deve cair no fallback do código; é usada para assinatura de
  sessão e token self-service.
- `SUPABASE_SERVICE_KEY` deve permanecer estritamente no servidor; a rota pública
  de configuração é um risco porque pode retorná-la.
- O arquivo real `.env` foi deliberadamente ignorado nesta auditoria. Nenhuma
  presença ou valor de secret foi verificado.
- `.env.example` na raiz contém nomes e valores vazios/padrões não secretos.
- O bootstrap do Flask procura `backend/.env`, não `.env` na raiz. O exemplo raiz
  é documentação/modelo; Secrets injetados no processo funcionam sem arquivo
  local. Nenhum `backend/.env` foi criado ou modificado.

## Limitações de deploy

Não foi feita instalação de dependências, build, inicialização de servidor,
acesso ao Render, execução de workflow ou conexão ao Supabase. Não foram
determinados workers/timeouts de produção nem persistência do filesystem do
provedor.
