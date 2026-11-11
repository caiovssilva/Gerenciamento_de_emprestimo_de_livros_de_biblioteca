# 09 — Variáveis de ambiente

O inventário veio de leituras de `os.getenv`/`os.environ` no código Python e dos
workflows. **O `.env` real não foi lido.** `.env.example` diferencia-se do arquivo
local secreto: documenta nomes e padrões; Secrets mantêm valores fora do
workspace/repositório e são injetados pela plataforma.

| Variável | Uso | Obrigatória? / ausência |
|---|---|---|
| `PORT` | Porta da plataforma; precede `FLASK_PORT` | Opcional; segue para porta padrão |
| `FLASK_PORT` | Porta local no `app.py` | Opcional; padrão 5000 |
| `FLASK_ENV` | Define debug no `app.py` | Opcional; padrão `development` ativa debug |
| `SECRET_KEY` | Sessão Flask e assinatura self-service | Deve ser definida forte em produção; ausência usa segredo fixo conhecido e bloqueia emissão segura de token self-service |
| `SELF_SERVICE_SECRET_KEY` | Segredo separado para token, se presente | Opcional; fallback para `SECRET_KEY` |
| `AUTH_DEBUG` | Logs extras de autenticação | Opcional; desativado por padrão |
| `SUPABASE_URL` | Endpoint de dados e health readiness | Obrigatória para APIs dependentes do banco |
| `SUPABASE_SERVICE_KEY` | Chave preferida do cliente backend | Não obrigatória se houver `SUPABASE_KEY`; privilégios dependem do tipo |
| `SUPABASE_KEY` | Chave fallback do cliente backend/config | Alternativa; usar anon/public no frontend não substitui autorização |
| `SUPABASE_ANON_KEY` | Secret usado no workflow de manutenção | Necessária apenas para o workflow de ping |
| `GOOGLE_BOOKS_API_KEY` | Query key opcional no Google Books | Opcional; consulta tenta sem chave |
| `GROQ_API_KEY`, `API_GROQ`, `GROQ_API` | Chave de Groq, aliases em ordem | Opcional; recursos Groq falham como não configurados |
| `GROQ_MODEL` | Modelo texto do Groq | Opcional; padrão definido no código |
| `GROQ_VISION_MODEL` | Modelo visão Groq | Opcional; padrão `qwen/qwen3.8-27b` |
| `OPENAI_API_KEY` | Chave de visão OpenAI | Opcional; provedor OpenAI fica indisponível sem ela |
| `OPENAI_VISION_MODEL` | Modelo visão OpenAI | Opcional; padrão `gpt-4o-mini` |
| `ISBNDB_API_KEY` | Cabeçalho Authorization para ISBNdb | Opcional; provedor só participa se presente |
| `ISBN_VISION_PROVIDER` | Provedor padrão da visão | Opcional; padrão `groq` |

No GitHub Actions, configure `SUPABASE_URL` e `SUPABASE_ANON_KEY` como repository
secrets. Em Codespaces, use Secrets do Codespaces e reabra/reinicie o processo
para atualizar seu ambiente. Não registre valores em issue, relatório ou arquivo
versionado.

O Flask chama `load_dotenv` com o caminho `backend/.env`. Portanto, o
`.env.example` recém-criado na raiz **não é carregado automaticamente** pelo app;
ele serve como referência. No Codespaces, variáveis fornecidas no processo são
preferíveis. Para configuração local por arquivo, o caminho esperado pelo código
é `backend/.env`; esse arquivo real foi mantido intocado.

O `backend/.env.example` existente também lista `DATABASE_MODE` e
`ENABLE_DEFAULT_CREDENTIALS`; não foi encontrada leitura dessas duas variáveis
nos arquivos de execução examinados. São documentadas como exemplos legados, não
como configuração runtime confirmada.

O `.gitignore` já ignora `.env` e `.env.*`; a exceção adicionada permite versionar
apenas o exemplo raiz sem remover as regras de segredo.
