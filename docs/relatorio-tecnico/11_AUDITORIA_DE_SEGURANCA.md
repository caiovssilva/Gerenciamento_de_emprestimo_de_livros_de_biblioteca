# 11 — Auditoria de segurança

## Escopo e método

Revisão estática do Flask, frontend, SQL, dependências declaradas e workflows;
testes unitários locais executados. Não houve exploração de serviços externos,
acesso a dados de terceiros, uso de banco real, teste de carga nem leitura do
`.env`.

## Achados prioritários

| Prioridade | Evidência | Impacto/condição | Recomendação |
|---|---|---|---|
| Crítica | Rota `/api/config/supabase` e aliases obtêm `SUPABASE_KEY` ou fallback `SUPABASE_SERVICE_KEY`. | Cliente anônimo pode receber credencial do servidor; se service role, acesso amplo e bypass de RLS. | Desativar a rota, remover cliente Supabase do browser e rotacionar credenciais expostas. |
| Crítica | APIs de negócio não exigem papel geral; a proteção global só especializa sessão de autoatendimento. | Chamadas HTTP diretas podem ler/alterar dados independentemente da interface. | Aplicar autenticação e autorização explícitas por função/endpoint. |
| Crítica/alta | Policies SQL amplas `true`; script inclui senha seed em texto claro. | Acesso público conforme grants e credenciais; acesso conhecido se script executado. | RLS de menor privilégio, grants mínimos e bootstrap de credenciais seguro. |
| Alta | Secret Flask previsível em fallback; cookies não configuram `Secure`/`SameSite` no app. | Falsificação de sessão assinada se fallback estiver em uso; transmissão insegura se não houver TLS. Flask mantém HttpOnly default true. | Exigir secret forte e configurar Secure/HttpOnly/SameSite; TLS em produção. |
| Alta | Flag bibliotecário atualizável por rota sem RBAC; QR desse aluno cria sessão staff. | Elevação indevida da função pela API exposta. | Limitar alteração a administrador autenticado e adicionar auditoria. |
| Alta | Senha aparece em PNG de carteirinha administrativa; plaintext legado é aceito. | Cópias da imagem mantêm credencial reutilizável e banco pode guardar senha clara. | Remover senha do cartão, migrar/obrigar hash, revogar credenciais existentes. |
| Alta | Dados externos são montados em `innerHTML`; CSP permite `unsafe-inline`. | Conteúdo controlado pode executar script no contexto de usuário caso escapamento não seja feito em cada ponto. | DOM seguro e CSP baseada em nonce/hash; validar entradas e saída contextual. |
| Média/alta | Sem token CSRF encontrado; CORS `*`; rate limit não encontrado. | Aumenta superfície para chamadas cruzadas e tentativa de senha; cenário depende do cookie/navegador e configuração efetiva. | CSRF+Origin, CORS allowlist e limitação de tentativas. |
| Média | Upload QR sem limite de tamanho explícito; dependências sem auditoria de CVE. | Consumo de memória/CPU e risco não quantificado de pacote. | Limites de upload, validação robusta e auditoria de dependências. |

## Controles observados

- Senhas novas podem ser rehashadas com Passlib, mas a falha ao atualizar hash é
  ignorada e plaintext legado ainda autentica.
- Self-service usa token assinado com validade de 30 min e valida escopo/aluno.
- Rotas de empréstimo exigem QR no caminho de renovação/devolução tradicional.
- Existem headers CSP e `object-src 'none'`, porém há `unsafe-inline`.
- `health` e `ready` separam liveness de disponibilidade do banco.

## Não validado dinamicamente

Não se tentou falsificar sessão, explorar XSS/CSRF, usar key divulgada, contornar
RLS ou atacar endpoint externo. Não se confirmou se secrets atuais estão
configurados nem se a chave service role foi exposta anteriormente. O `.env`
permaneceu intocado. Não há resultado de scanner de dependências.

Detalhes e correções recomendadas estão em [10 — Falhas](10_RELATORIO_DE_FALHAS.md).
