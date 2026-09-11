# Relatorio de explicacao da logica completa do sistema

## 1. Visao geral

O projeto e um sistema de gerenciamento de biblioteca escolar. Ele controla livros, exemplares, alunos, salas, generos e emprestimos. Tambem oferece login administrativo, acesso restrito de bibliotecario, QR codes, leitura de codigo de barras, consulta de ISBN e relatorios.

A arquitetura atual e:

```text
Navegador
   |
   v
Frontend SPA (HTML + CSS + JavaScript)
   |
   v
Flask / API REST
   |----------------------|
   v                      v
Supabase/PostgreSQL       JSON local
(banco principal)         (fallback/demonstracao)
```

O Flask tambem serve o frontend. Portanto, em desenvolvimento, uma unica aplicacao atende a pagina e as rotas `/api/...`.

## 2. Inicializacao da aplicacao

1. `backend/app.py` define o diretorio do backend e carrega variaveis de ambiente.
2. O Flask e criado apontando seu diretorio estatico para `frontend/`.
3. Os blueprints sao importados e registrados com prefixos REST.
4. CORS e cabecalho CSP sao aplicados.
5. O endpoint `/api/health` testa uma consulta simples na tabela `livros`.
6. Para as APIs de negocio, `before_request` verifica se o Supabase esta acessivel. Se nao estiver, retorna `503` em vez de gravar silenciosamente no local.
7. Rotas que nao sao API devolvem arquivos do frontend; caminhos desconhecidos retornam `index.html`, permitindo a navegacao da SPA.

## 3. Configuracao e persistencia

`backend/utils/supabase_client.py` cria o cliente a partir de URL e chave. O cliente e reutilizado e possui reconexao para falhas transitórias.

Os helpers em `backend/api/_helpers.py` concentram:

- leitura de JSON;
- escrita atomica ou controlada dos dados locais;
- verificacao de existencia de tabela/coluna;
- classificacao de erros offline;
- datas e identificadores.

A regra geral dos endpoints e:

1. tentar Supabase quando a tabela existe;
2. executar a operacao no banco;
3. em indisponibilidade ou compatibilidade, consultar os JSON locais quando o modulo permite;
4. devolver sempre um JSON com o contrato esperado pelo frontend.

O `database.sql` define as tabelas `usuarios`, `salas`, `generos`, `livros`, `alunos`, `emprestimos` e `relatorios_mensais`, alem de indices e views. Em producao, o Supabase e a fonte oficial dos dados.

## 4. Autenticacao e autorizacao

O login do frontend envia credenciais para `POST /api/auth/login`. O backend:

1. normaliza o login;
2. procura o usuario no Supabase ou na fonte local prevista;
3. verifica a senha com o mecanismo configurado;
4. retorna o acesso como `admin` ou `librarian`;
5. o frontend cria o estado da sessao e atualiza a navegacao.

O administrador possui acesso total. Um aluno pode receber permissao de bibliotecario, mas esse perfil fica limitado a painel, emprestimos e acervo. O frontend oculta paginas administrativas e o backend deve continuar sendo considerado a barreira real de autorizacao.

A carteirinha administrativa usa codigo `ADMIN-<login>`. O endpoint de geracao exige a senha real antes de gerar a imagem. Ao ler esse QR no login, o sistema pede a senha administrativa para confirmar o acesso.

## 5. Fluxo de livros e exemplares

### Listagem

`GET /api/books/` busca livros, opcionalmente filtra por texto ou genero e acrescenta os dados do genero. O frontend mostra titulo, autor, genero, area, quantidade total e disponibilidade.

### Cadastro

Ao cadastrar um livro, `POST /api/books/`:

1. valida titulo e autor;
2. cria um ID;
3. define quantidade de exemplares;
4. gera IDs unicos para cada exemplar;
5. grava `exemplares_ids` e `exemplares_meta`;
6. salva no Supabase ou JSON conforme a disponibilidade;
7. gera um QR do livro.

Cada exemplar possui um codigo diferente. Isso permite saber exatamente qual unidade esta emprestada, mesmo quando o livro tem varias copias.

### ISBN

O frontend normaliza o ISBN e chama `/api/books/isbn-lookup`. O backend consulta, em ordem, Google Books, isbnsearch.org e OpenLibrary. O resultado pode combinar dados de mais de uma fonte.

Depois:

1. categorias externas sao comparadas aos generos cadastrados;
2. a comparacao remove acentos e usa aliases, por exemplo `science fiction` para `Ficcao Cientifica`;
3. `area` recebe `Geral`, pois as fontes nao possuem uma area/curso confiavel;
4. a resposta inclui ISBN, titulo, autor, categorias, area, `genero_id` e `genero_nome`;
5. o frontend preenche somente campos vazios, preservando informacoes digitadas pelo usuario.

O cache `_ISBN_CACHE` evita consultas repetidas durante a vida do processo. Se uma fonte nao tiver o ISBN, a proxima e tentada. Um retorno sem autor ou categoria e uma ausencia de metadados, nao necessariamente uma falha do sistema.

## 6. Scanner de QR e codigo de barras

O scanner do navegador (`frontend/assets/js/qr-scanner.js`) segue esta ordem:

1. abre a camera com `getUserMedia`;
2. lista e permite trocar cameras;
3. tenta foco continuo quando o dispositivo suporta;
4. captura quadros periodicamente;
5. tenta `jsQR` para QR codes;
6. tenta `BarcodeDetector` com QR, Code 128, EAN-13, EAN-8, UPC-A e UPC-E;
7. se o navegador nao suportar isso, envia a imagem para `POST /api/qr/decode`.

No backend, `scanner/routes.py` usa OpenCV, NumPy e `pyzbar`. O `pyzbar` depende da biblioteca nativa ZBar (`libzbar0t64` no Ubuntu). O backend testa variacoes de escala, contraste e nitidez para aumentar a chance de leitura.

Depois da leitura, `_resolve_qr()` identifica:

- `ADMIN-...`: cartao administrativo;
- `EXEMPLAR-...`: exemplar especifico de livro;
- ID ou ISBN: livro;
- ID ou carteirinha: aluno.

O callback devolve o resultado para a pagina que iniciou o scanner. No cadastro, o valor lido e normalizado como ISBN e dispara a busca automatica.

## 7. Alunos, salas e generos

`students.py` controla cadastro, pesquisa, importacao CSV, salas vinculadas, historico e permissao de bibliotecario.

`rooms.py` controla salas e seus dados basicos. O frontend usa as salas para filtros e para exibir o local do aluno.

`genres.py` controla nome, icone e cor dos generos. Quando um genero e excluido, os livros vinculados ficam sem `genero_id`, evitando referencias invalidas. A listagem calcula a quantidade de livros por genero.

## 8. Emprestimos

O fluxo de novo emprestimo normalmente e:

1. selecionar ou localizar aluno;
2. localizar livro por titulo, ISBN, ID ou scanner;
3. selecionar exemplar disponivel;
4. validar regras de disponibilidade;
5. gravar o emprestimo com data de retirada e vencimento;
6. atualizar a tela e os indicadores.

A devolucao preenche `devolvido_em`. A renovacao altera a data prevista conforme a quantidade de dias. O status e calculado a partir das datas:

- `active`: ainda nao devolvido e dentro do prazo;
- `overdue`: ainda nao devolvido e prazo vencido;
- `returned`: possui data de devolucao.

O backend recalcula disponibilidade com base nos emprestimos ativos, evitando depender somente de um contador visual.

## 9. Relatorios

`reports.py` monta os indicadores consultando livros, alunos e emprestimos. Ele fornece:

- resumo de emprestados, atrasados e devolvidos;
- livros mais emprestados;
- totais por turma;
- relatorios mensais persistidos quando solicitados;
- CSV de atrasados;
- CSV do historico completo;
- CSV de livros mais emprestados;
- CSV por turma;
- CSV de status por aluno.

`charts.js` chama os endpoints de resumo e desenha os graficos. O frontend atualiza os dados em ciclos definidos pela aplicacao. Para integrar com AppSheet, a planilha pode consumir os CSVs, mas o Supabase deve continuar como fonte principal para evitar edicoes concorrentes.

## 10. Estado global e interface

`api.js` transforma funcoes JavaScript em chamadas HTTP. `store.js` guarda livros, alunos, emprestimos, salas e generos recebidos da API. `app.js` controla sessao, pagina ativa, permissoes, modais globais e sincronizacao.

Os arquivos em `pages/` cuidam das acoes especificas de cada tela. `utils.js` concentra selecao de elementos, datas, toasts e pequenas funcoes de interface. `index.html` contem a estrutura das paginas e modais; `main.css` fornece o tema visual e a responsividade.

O ciclo comum de uma tela e:

```text
abrir pagina
  -> carregar estado pelo store/API
  -> renderizar tabela ou painel
  -> usuario executa acao
  -> API valida e grava
  -> syncData atualiza o store
  -> tela e graficos sao redesenhados
```

## 11. Testes e operacao

Os testes Python verificam login, fallback de livros, desempenho de carteirinhas, ambiente, resolucao QR, relatorios, reconexao e IDs unicos. O teste JavaScript verifica callback do scanner e foco da camera.

Para executar localmente:

```bash
.venv312/bin/pip install -r backend/requirements.txt
.venv312/bin/python backend/app.py
```

Acesse `http://localhost:5000`. O protocolo e HTTP no servidor de desenvolvimento; usar HTTPS nessa porta produz erros de requisicao no Werkzeug.

## 12. Limites conhecidos

- Google Books pode retornar `429` quando a cota diaria acaba.
- OpenLibrary pode responder `200` com objeto vazio para ISBN desconhecido.
- Algumas fontes nao possuem autor, categoria ou area para determinados livros.
- A camera depende de permissao do navegador, HTTPS em ambientes publicos e boa iluminacao.
- Sem ZBar, o fallback Python nao le codigo de barras.
- O AppSheet nao deve editar simultaneamente os mesmos emprestimos que o sistema principal.
- Segredos como chaves de API devem permanecer em Secrets ou `.env`, nunca no Git ou em mensagens.

## Conclusao

A logica do sistema combina uma SPA simples no navegador, uma API Flask organizada por entidade e um banco Supabase com fallback local. O desenho favorece continuidade operacional: a interface permanece utilizavel durante falhas controladas, identificadores de exemplares tornam os emprestimos rastreaveis e os relatorios podem ser exportados para integracoes externas. A confiabilidade depende principalmente de configuracao de ambiente, disponibilidade do Supabase, quota das APIs externas e suporte da camera ao formato de codigo utilizado.
