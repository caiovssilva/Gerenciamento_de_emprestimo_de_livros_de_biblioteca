# 03 — Lógica de programação

Este documento acompanha os mecanismos centrais sem transcrever módulos inteiros.

## Inicialização Flask

`backend/app.py` calcula o caminho de `backend/.env`, chama `load_dotenv` sem
sobrescrever valores já definidos no processo, importa blueprints e registra
rotas. Em seguida instala CORS, middleware, handlers e rotas de health/estáticos.
O comando de desenvolvimento no README é `python backend/app.py`; em produção o
README recomenda Gunicorn.

## Consulta Supabase

`get_client()` em `backend/utils/supabase_client.py` mantém um cliente em cache.
`_get_env_config()` lê `SUPABASE_URL` e prefere `SUPABASE_SERVICE_KEY` a
`SUPABASE_KEY`. `SupabaseTable` encadeia `select`, `eq`, `insert`, `update`,
`delete`, `upsert`, entre outros. `sb_exec(query)` executa e retorna `data`,
levantando exceções de erro.

O cliente não verifica a conexão ao ser construído; a conectividade é exercitada
quando uma query executa. O helper `table_ok` testa uma seleção pequena e cacheia
resposta positiva.

## Login administrativo

`POST /api/auth/login` lê `login` e `password`, busca a linha em `usuarios`,
verifica hash por Passlib/bcrypt/crypt e também aceita comparação com valor legado
sem `$`. A autenticação bem-sucedida limpa a sessão e grava `access_scope`
`staff_admin` ou `staff_librarian`, derivado do login. O retorno inclui `access`,
ID, login e nome. Não foi encontrado limite de tentativas no fluxo.

O autoatendimento é separado: `POST /api/auth/self-service/login` valida a
carteirinha, assina token `itsdangerous` por até 30 minutos, e grava na sessão
cookie os identificadores de escopo/aluno. Rotas de histórico verificam token,
escopo e propriedade do empréstimo.

## Empréstimo, renovação e devolução

`_create_loan_record()` valida IDs obrigatórios, busca livro, calcula exemplares
ativos e seleciona um livre, valida aluno, calcula vencimento e insere registro.
A disponibilidade é calculada em uma leitura seguida de inserção; não existe
transação explícita no código. O banco contém índice único parcial sobre
`(livro_id, exemplar)` para itens ativos, o que pode rejeitar a corrida, mas a
resposta desse conflito não é convertida explicitamente em 409 neste trecho.

Renovação confere se o empréstimo ainda está ativo e, no fluxo normal, pede QR do
exemplar. Estende prazo pelo número configurado e incrementa `renovacoes`, sem
limite máximo aparente. Devolução também exige QR do exemplar no caminho normal e
atualiza `devolvido_em`; os dois fluxos fazem leitura e update separados.

## Consulta ISBN

`_lookup_isbn()` normaliza e valida checksum do ISBN, verifica cache em memória
(TTL de 15 minutos, até 128 entradas) e consulta Google Books, ISBNsearch e Open
Library em paralelo com `ThreadPoolExecutor`. Quando não há metadados completos,
consulta página HTML do Google Books e busca Open Library; ISBNdb só entra se
`ISBNDB_API_KEY` estiver configurada. O modo scanner adiciona Groq como sugestão.
Resultados bibliográficos são combinados e podem ser cacheados.

A leitura de imagem valida prefixo MIME `data:image/`, base64 e limite de 2 MiB,
e chama Groq ou OpenAI Vision via SDK `openai` configurado para chat completions.
Não há chamada real de API nesta auditoria.

## Estado frontend

`Store` mantém listas em memória e as normaliza (por exemplo, `titulo` para
`title`), além de tentar persistir cópias em `localStorage`. `API` centraliza
URLs e serialização HTTP. `app.js` coordena login, navegação e sincronização;
arquivos `pages/*.js` preenchem tabelas/modais e disparam operações. A aplicação
usa eventos de DOM e funções globais, sem bundler ou import ES module observado.

## Síncrono, assíncrono e concorrência

- Rotas Flask e operações Supabase são síncronas.
- O browser usa `async/await` em `fetch`.
- Consulta de fontes ISBN é concorrente via executor Python.
- Scanner de câmera do servidor usa `threading.Thread` e `Lock`.
- As consultas externas HTTP usam timeout 6 s e tentam novamente uma vez para
  certos erros HTTP/rede.

## Tratamento de erros

Há handlers globais e mensagens específicas em rotas; também existem blocos
`except` que recorrem ao JSON ou ocultam falhas. Isso dificulta diferenciar erro
de schema, rede e dado inválido em alguns endpoints. A auditoria não alterou esse
comportamento.
