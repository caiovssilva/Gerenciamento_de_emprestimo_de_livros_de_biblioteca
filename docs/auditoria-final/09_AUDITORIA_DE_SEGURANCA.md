# 09 — Auditoria de segurança

Análise defensiva estática de código/configuração; sem exploração dinâmica,
nenhum serviço externo atacado e `.env` real intocado.

| ID | Evidência do repositório | Classificação e limite |
|---|---|---|
| SEC-01 | `api/auth.py:get_supabase_config` e aliases em `app.py` escolhem `SUPABASE_KEY` ou `SUPABASE_SERVICE_KEY` e devolvem `{url,key}` | Exposição pela API é confirmada no código; não foi chamada em rede. Se a configuração ativa for service key, impacto potencial crítico |
| SEC-02 | Rotas de negócio não passam por autorização geral; `before_request` especializa apenas escopos conhecidos | Falta de gate universal observada estaticamente; endpoint específico não foi testado com HTTP anônimo |
| SEC-03 | `database.sql` define policies permissivas `USING(true)`/`WITH CHECK(true)` e habilita RLS | Confirmado no script; roles/grants remotos desconhecidos |
| SEC-04 | DDL semeia credenciais administrativas em texto literal | Confirmado no script; não se confirmou execução no banco ativo |
| SEC-05 | `app.py` tem `SECRET_KEY` fallback previsível | Confirmado no código; valor ativo do processo não foi verificado |
| SEC-06 | `students.toggle_librarian_access` altera a flag sem check explícito de papel | Confirmado no handler; não testado por chamada |
| SEC-07 | `admin_card` escreve senha digitada em campo da imagem gerada | Confirmado no código; nenhuma imagem foi gerada |
| SEC-08 | Templates JavaScript montam valores de API em `innerHTML`; CSP contém `unsafe-inline` | Sink confirmado; execução de payload XSS não testada |
| SEC-09 | Não foi encontrado token CSRF nos endpoints mutáveis; CORS permite `*` | Config estática; impacto depende de cookies/origem/navegador e não foi explorado |
| SEC-10 | QR decode aceita conteúdo multipart/base64 sem limite explícito local ao handler | Código observado; limites de proxy/plataforma não conhecidos |
| SEC-11 | `database.sql` usa `DROP ... CASCADE`; FKs de empréstimo usam `ON DELETE CASCADE` | Confirmado em arquivo; script não executado |
| SEC-12 | Não foi executado scanner de vulnerabilidade de dependências | Nenhuma CVE é declarada ou presumida nesta auditoria |

## Recomendações prioritárias

Remover endpoint que retorna key privilegiada e rotacionar key caso tenha sido
exposta; aplicar RBAC server-side em todas as rotas; restringir grants/RLS;
remover senha seed/plaintext legado e fallback de secret; proteger alteração de
papéis; não imprimir senha; usar DOM seguro; implementar CSRF, CORS allowlist,
rate limit e limites de upload; revisar cascades e transformar SQL em migrations
incrementais.

Não afirmar segurança total: ambiente real, navegador, banco, credenciais e
dependências não foram testados dinamicamente.
