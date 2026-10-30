# Auditoria de seguranca e qualidade

## Resultado da auditoria

A auditoria identifica defeitos confirmados no codigo e nas configuracoes. A principal falha é que a seguranca efetiva depende do Flask, enquanto o RLS nao estabelece restricoes uteis e a chave privilegiada do banco pode ser enviada ao navegador.

| Nº | Área | Achado | Arquivo:linha | Gravidade | Estado |
|---:|---|---|---|---|---|
| 1 | Banco | Senha administrativa fixa em texto claro no SQL. | `database.sql:27-29` — `('Administrador', 'admin', 'narceu2026')` | Crítica | Confirmado |
| 2 | Banco/API | A rota publica entrega a `SUPABASE_SERVICE_KEY` ao navegador. | `backend/api/auth.py:606-623` — fallback para `SUPABASE_SERVICE_KEY` | Crítica | Confirmado |
| 3 | Autorizacao | CRUDs, relatórios, exports e operações QR nao exigem login nem papel. | `backend/api/students.py:16`; `backend/api/books.py:843`; `backend/api/reports.py:248-273` | Crítica | Confirmado |
| 4 | Banco | RLS habilitado com políticas `USING(true)` e `WITH CHECK(true)`. | `database.sql:143-157` | Crítica | Confirmado |
| 5 | Autorizacao | Qualquer cliente pode conceder papel de bibliotecario por PATCH. | `backend/api/students.py:178-189` — `grant = bool(body.get("is_librarian", True))` | Crítica | Confirmado |
| 6 | Autorizacao | Papel deriva do texto do login ou de campo de aluno. | `backend/api/auth.py:269-270` — login em lista de nomes | Crítica | Confirmado |
| 7 | QR/senha | Carteirinha administrativa contém a senha visível. | `backend/scanner/routes.py:392-418` — `field2 = f"Senha: {password}"` | Crítica | Confirmado |
| 8 | Sessao | Segredo fixo conhecido é usado sem configuração segura. | `backend/app.py:35-39` — `narceu-biblioteca-2026-dev-only` | Crítica | Confirmado |
| 9 | Banco | Script destrutivo apaga o schema com `DROP ... CASCADE`. | `database.sql:8-16` | Alta | Confirmado |
| 10 | Banco | Exclusao de livro/aluno apaga emprestimos por cascade. | `database.sql:108-109` | Alta | Confirmado |
| 11 | Empréstimos | Disponibilidade e gravação nao sao operações atomicas. | `backend/api/loans.py:125-165` | Alta | Confirmado |
| 12 | Empréstimos | Não há limite de renovações, multa ou bloqueio por atraso. | `backend/api/loans.py:177-216` | Alta | Confirmado |
| 13 | Renovacao | `renovacoes` é incrementado sem limite máximo. | `backend/api/loans.py:191-203` | Alta | Confirmado |
| 14 | CSRF | Mutacoes nao validam token CSRF. | `backend/app.py:48-49` | Alta | Confirmado |
| 15 | Cookies | Configuracao nao exige `Secure`, `HttpOnly` ou `SameSite`. | `backend/app.py:35-39` | Alta | Confirmado |
| 16 | Login | Não há limite de tentativas, bloqueio ou backoff. | `backend/api/auth.py:203-270` | Alta | Confirmado |
| 17 | XSS | Dados da API sao interpolados em `innerHTML`. | `frontend/assets/js/app.js:948-1018`; `frontend/assets/js/pages/students.js:42-58` | Alta | Confirmado |
| 18 | Upload | Imagem base64 nao possui validacao MIME ou limite seguro. | `backend/scanner/routes.py:150-181` | Alta | Confirmado |
| 19 | API | Entrada aceita campos arbitrarios sem schema. | `backend/api/books.py:843-851`; `backend/api/students.py:76-96`; `backend/api/reports.py:68-95` | Alta | Confirmado |
| 20 | QR | QR de aluno com `is_librarian=true` concede bibliotecario sem senha. | `backend/scanner/routes.py:369-380` | Alta | Confirmado |
| 21 | Frontend | Cookie guarda identidade em JSON nao assinado. | `frontend/assets/js/app.js:31-55` | Média | Confirmado |
| 22 | Logout | Não há invalidação server-side da sessão administrativa. | `frontend/assets/js/app.js:36-55` | Média | Confirmado |
| 23 | Senha | O sistema aceita senhas legadas em texto claro. | `backend/api/auth.py:62-68` | Média | Confirmado |
| 24 | Logs | `AUTH_DEBUG` registra prefixo do hash armazenado. | `backend/api/auth.py:238-239` | Média | Confirmado |
| 25 | CORS | Todas as origens podem acessar `/api/*`. | `backend/app.py:48-49` | Média | Confirmado |
| 26 | CSP | CSP permite `'unsafe-inline'`. | `backend/app.py:69-82` | Média | Confirmado |
| 27 | Cabeçalhos | Faltam HSTS, frame protection e política de referrer. | `backend/app.py:84-91` | Média | Confirmado |
| 28 | Integrações | Vision envia imagens inteiras sem quota por usuário/IP. | `backend/api/books.py:218-283` | Média | Confirmado |
| 29 | Integrações | ISBN pode executar varias fontes externas e tentativas. | `backend/api/books.py:632-696` | Média | Confirmado |
| 30 | Integrações | Há aliases alternativos de chave Groq sem gestão central. | `backend/api/books.py:159-163` | Média | Confirmado |
| 31 | Banco | JSONB de exemplares não possui integridade estrutural. | `database.sql:71-74` | Média | Confirmado |
| 32 | Banco | Índice ativo não cobre `exemplar_id`. | `database.sql:120-128` | Média | Confirmado |
| 33 | Banco | Datas não impedem vencimento anterior ao empréstimo. | `database.sql:112-116` | Média | Confirmado |
| 34 | Banco | Timestamps usam `TIMESTAMP` sem timezone. | `database.sql:118` | Média | Confirmado |
| 35 | Auditoria | `criado_por` e `gerado_por` são texto livre sem identidade autenticada. | `database.sql:106-118`; `database.sql:130-141` | Média | Confirmado |
| 36 | Migrations | Não há migrations incrementais. | `database.sql:8-16` | Média | Confirmado |
| 37 | Views | Views criadas no SQL nao sao usadas pela aplicacao. | `database.sql:159-193` | Baixa | Confirmado |
| 38 | Frontend | Host do Supabase está fixado no HTML. | `frontend/index.html:442-445` | Baixa | Confirmado |
| 39 | Dependências | `pytest` não está declarado. | `backend/requirements.txt:1-12` | Média | Confirmado |
| 40 | Dependências | `groq` e `openai` não têm versões fixas. | `backend/requirements.txt:10-12` | Média | Confirmado |
| 41 | Testes | Suíte Python: 180 aprovados, 12 falhas. | `backend/tests/test_isbn_lookup.py:321-350`; `backend/tests/test_qr_id_resolution.py:36-74`; `backend/tests/test_reports_data.py:10-42` | Alta | Confirmado |
| 42 | Testes | Testes de empréstimo nao exercitam concorrencia nem RLS real. | `backend/tests/test_loans_return_qr.py:67-96` | Média | Confirmado |
| 43 | Documentacao | Documentação antiga contradiz o comportamento atual. | `TESTES_EXECUTADOS.md:89-143`; `backend/README.md:279-289` | Média | Confirmado |
| 44 | Documentacao | README diz que senha é configurada, mas o SQL publica fixa. | `backend/README.md:155-160`; `database.sql:27-29` | Média | Confirmado |
| 45 | Deploy | Gunicorn recomendado sem workers, timeout ou proxy definidos. | `backend/README.md:147` | Média | Confirmado |
| 46 | API | Não existe correcao administrativa completa de emprestimo lançado errado. | `backend/api/loans.py:105-216` | Média | Suspeita |

## Achados críticos e altos: exploração, impacto e correção

### 1. Senha padrão e SQL destrutivo
- **Explorar:** entrar com `admin`/`narceu2026`; executar o SQL em dados existentes.
- **Impacto:** acesso administrativo imediato e perda irreversível.
- **Correção:** remover senhas fixas e os `DROP`; criar o administrador por bootstrap protegido.

```sql
ALTER TABLE usuarios ALTER COLUMN senha SET NOT NULL;
INSERT INTO usuarios (nome, login, senha)
VALUES ('admin', 'admin', crypt(:senha_inicial, gen_salt('bf')));
```

### 2. `service_role` entregue ao navegador
- **Explorar:** chamar `/api/config/supabase` e reutilizar a chave.
- **Impacto:** leitura e alteração integral da base.
- **Correção:** não retornar a chave privilegiada e remover o cliente direto do frontend.

```python
from flask import abort

@app.get("/api/config/supabase")
def frontend_supabase_config():
    abort(404)
```

### 3. APIs sem autenticação
- **Explorar:** chamar DELETE, PATCH ou CSV export sem sessão.
- **Impacto:** alteração de dados, privilégios e informações pessoais.
- **Correção:** aplicar RBAC central em todas as rotas.

```python
from functools import wraps
from flask import abort, session

def require_access(*roles):
    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            if session.get("access_scope") not in roles:
                abort(403)
            return func(*args, **kwargs)
        return wrapped
    return decorator
```

### 4. RLS permissivo
- **Explorar:** usar a chave vazada ou a API REST diretamente.
- **Impacto:** todas as operações são permitidas.
- **Correção:** remover service_role do cliente público e criar políticas por papel e ownership.

```sql
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon;

CREATE POLICY usuarios_own_select ON usuarios
FOR SELECT TO authenticated
USING (auth.uid()::text = id::text);
```

### 5. Segredo padrão e cookies
- **Explorar:** forjar sessão com segredo conhecido ou interceptar HTTP.
- **Impacto:** escalada administrativa e roubo de sessão.
- **Correção:** exigir segredo forte e configurar cookies seguros.

```python
app.config.update(
    SECRET_KEY=os.environ["SECRET_KEY"],
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)
```

### 6. Senha dentro da carteirinha administrativa
- **Explorar:** gerar a imagem e ler o campo impresso.
- **Impacto:** a cópia divulga credencial permanente.
- **Correção:** remover a senha da imagem e usar token curto, revogável e hashado.

### 7. Papel concedido por QR sem senha
- **Explorar:** alterar `is_librarian=true` e ler o QR.
- **Impacto:** privilégios de bibliotecário sem senha.
- **Correção:** exigir senha segura para elevar o usuário a bibliotecário.

### 8. Corrida na reserva de exemplar
- **Explorar:** enviar dois empréstimos simultâneos para o mesmo exemplar.
- **Impacto:** exemplar emprestado a dois registros.
- **Correção:** executar RPC transacional com `SELECT ... FOR UPDATE` e UPDATE condicionado.

```sql
ALTER TABLE emprestimos
ADD CONSTRAINT uq_exemplar_ativo
UNIQUE (livro_id, exemplar_id)
WHERE devolvido_em IS NULL;
```

### 9. Cascade apaga histórico
- **Explorar:** excluir livro ou aluno com empréstimos.
- **Impacto:** perda de histórico e relatórios.
- **Correção:** trocar `ON DELETE CASCADE` por `RESTRICT` e soft delete.

```sql
ALTER TABLE emprestimos
DROP CONSTRAINT emprestimos_livro_id_fkey,
ADD CONSTRAINT emprestimos_livro_id_fkey
FOREIGN KEY (livro_id) REFERENCES livros(id) ON DELETE RESTRICT;
```

### 10. XSS por dados da API
- **Explorar:** cadastrar nome/título contendo HTML e visualizar o registro.
- **Impacto:** execução no contexto administrativo.
- **Correção:** usar `textContent` ou elementos DOM criados explicitamente.

```javascript
element.textContent = title;
```

### 11. Falta de CSRF
- **Explorar:** página externa envia POST usando a sessão.
- **Impacto:** alterações não autorizadas.
- **Correção:** token CSRF por sessão, validação de `Origin` e `SameSite=Strict`.

## Plano de correção prioritário

1. Revogar e rotacionar a `service_role`; remover a rota pública e limpar a chave vazada.
2. Substituir senha fixa por bootstrap seguro e hash Argon2/bcrypt.
3. Proteger todas as rotas por RBAC central.
4. Reescrever RLS e impedir uso privilegiado no navegador.
5. Configurar segredo forte, cookies seguros, logout server-side e expiração.
6. Remover senha da carteirinha e exigir senha para privilégios administrativos.
7. Implementar CSRF e restrição efetiva de CORS.
8. Tornar empréstimo, renovação e devolução transacionais.
9. Trocar CASCADE por RESTRICT, adicionar auditoria e migrations.
10. Corrigir XSS e endurecer CSP.
11. Limitar uploads e uso das APIs externas.
12. Corrigir as 12 falhas da suíte Python e adicionar integração, concorrência e segurança.
13. Fixar dependências e adicionar `pytest` ao ambiente automatizado.
14. Atualizar a documentação e remover credenciais públicas.

## Cinco perguntas difíceis da defesa

### 1. Por que RLS protege o backend que usa `service_role`?
Não protege. `service_role` contorna RLS. O RLS só funciona como controle efetivo com chave limitada e políticas coerentes. Como o backend usa chave privilegiada e políticas abertas, a seguranca depende inteiramente do Flask.

### 2. Como impedir duas devoluções simultâneas?
O código atual não impede. Duas requisicoes podem ler o empréstimo ativo antes do primeiro UPDATE. A solução é transacao com `SELECT ... FOR UPDATE`, UPDATE condicionado por `devolvido_em IS NULL` ou RPC atômica.

### 3. Como garantir que um bibliotecário não vire administrador?
Não há garantia robusta. O papel deriva do texto do login e da sessão. É necessário armazenamento de usuários/papéis no banco e consulta de papel em toda operação sensível.

### 4. Por que a interface não pode validar autorização?
O usuário controla o navegador e pode chamar diretamente os endpoints. Esconder botoes é UX, nao seguranca. A autorização precisa existir no backend e no banco.

### 5. Por que não usar `ON DELETE CASCADE` no histórico?
Empréstimos são registros históricos e não podem desaparecer sem rastro. Entidades principais devem usar soft delete ou restrição de integridade, com audit trail de usuário e timestamp.

## Resultado dos testes executados

- Frontend: todos os testes JavaScript executados passaram.
- Backend: `180 passed, 12 failed, 1 warning`.
