# 10 — Falhas, riscos e limitações

Os itens abaixo são observações estáticas. “Confirmado” significa que a condição
está diretamente no código/configuração; não implica exploração em produção.

| ID | Classificação / gravidade | Evidência e impacto | Correção recomendada |
|---|---|---|---|
| F-01 | Vulnerabilidade confirmada — crítica | Endpoint público entrega `SUPABASE_KEY` ou, se ausente, `SUPABASE_SERVICE_KEY`; key privilegiada permitiria operação ampla. | Remover endpoints de configuração pública; usar apenas backend e chave anon nunca privilegiada. Rotacionar chave se já exposta. |
| F-02 | Autorização — crítica | CRUD, relatórios e operações de QR não têm verificação geral de sessão/papel. `before_request` restringe self-service, mas deixa anônimo continuar para outras rotas. | RBAC central server-side para toda rota, com testes negativos. |
| F-03 | Configuração banco — alta/crítica | Políticas RLS `USING(true)`/`WITH CHECK(true)` não limitam ownership; service role ignora RLS. | Revogar grants públicos, políticas por papel/ownership e limitar chave backend. |
| F-04 | Credencial — crítica | `database.sql` inclui usuários iniciais e senha em texto literal. | Remover seed de senha conhecida; bootstrap seguro e hash adaptativo. |
| F-05 | Segredo sessão — alta | `app.py` usa chave padrão previsível quando `SECRET_KEY` não existe. Cookie Flask é assinado, não criptografado. | Falhar startup sem segredo robusto; `Secure`, `HttpOnly`, `SameSite` explícitos e rotação. HttpOnly é default Flask, mas não é fixado no app. |
| F-06 | Privilégio — alta | `PATCH/POST /api/students/<id>/access` altera `is_librarian` sem checagem de admin na função/rota. | Exigir papel administrador e auditar alteração. |
| F-07 | Dados pessoais — alta | Endpoints de consulta/export não têm gate geral; dados de alunos e empréstimos podem ser retornados sem autenticação. | Aplicar RBAC e minimização de campos/exportações. |
| F-08 | Senha — alta | `_verify_password` aceita senha armazenada sem `$` por igualdade; SQL de seed inclui legado claro. | Migração que rejeite plaintext, hashing obrigatório e remoção do fallback legado. |
| F-09 | Impressão de credencial — alta | `admin_card` inclui senha digitada em `field2` da imagem gerada. | Remover senha impressa; emitir cartão sem segredo ou token revogável. |
| F-10 | RLS/QR — alta | QR de aluno com `is_librarian=true` cria sessão `staff_librarian` sem senha adicional. | Proteger concessão e exigir fator/autenticação adequada. |
| F-11 | Scripts de banco — alta | `database.sql` inicia com `DROP ... CASCADE`; execução em banco existente pode destruir schema/dados. | Migrar incrementalmente; bloquear execução destrutiva em produção. |
| F-12 | Histórico — alta | FKs de empréstimo usam `ON DELETE CASCADE`, possibilitando remoção de histórico ao excluir livro/aluno. | `RESTRICT`/soft delete e trilha de auditoria. |
| F-13 | XSS — alta | Vários dados dinâmicos são interpolados em `innerHTML`, inclusive linhas de alunos/livros e mensagens. | Usar `textContent`/DOM seguro; sanitização contextual e testes. |
| F-14 | CSRF/session — média/alta | Não foi encontrado token CSRF nos endpoints mutáveis. Sem teste de navegador não se confirmou cenário; risco cresce com cookies autenticados e ausência de validação Origin. | Token CSRF, validar Origin, SameSite adequado e métodos/headers consistentes. |
| F-15 | CORS — média | CORS permite origem `*` em `/api/*`. `supports_credentials` não está habilitado explicitamente, portanto não afirmar leitura cross-origin de cookie. | Restringir origens necessárias. |
| F-16 | Upload/DoS — média | `/api/qr/decode` aceita bytes multipart/base64 sem limite explícito nesse endpoint; visão ISBN limita imagem a 2 MiB. | Definir `MAX_CONTENT_LENGTH`, validar MIME/conteúdo e decodificação. |
| F-17 | Brute force — média | Não há rate limiting/backoff de login no fluxo encontrado. | Rate limit por conta/IP, monitoramento e mensagens uniformes. |
| F-18 | Concorrência empréstimo — risco potencial | Seleção de exemplar e INSERT não estão em transação; índice único parcial evita duplicidade do mesmo exemplar ativo, mas conflito não é tratado explicitamente como 409. | Reserva transacional/RPC e tratamento de conflito; teste concorrente isolado. |
| F-19 | Dependências — limitação | `groq` e `openai` não têm versão fixada; `pytest` não está no requirements; sem relatório de CVE. | Fixar versões e incluir ambiente de testes; executar scanner em ambiente autorizado. |
| F-20 | Suite de testes — falha confirmada do teste | 12 testes falharam nesta execução; evidências e causa provável registradas em 13/14. | Corrigir mocks/configuração e manter integração Supabase separada. |

### Questões que não são conclusões confirmadas

- Não se executou concorrência de produção, portanto não se afirmou dupla
  concessão efetiva; existe índice único parcial que protege a mesma chave.
- Não se testou CSRF, XSS em navegador, key exposure externa, RLS real ou API
  pública remotamente; esses itens são evidências estáticas e riscos.
- Não se identificou CVE específica; não houve varredura de dependências.
