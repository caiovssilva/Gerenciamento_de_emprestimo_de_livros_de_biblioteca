# Relatório de TCC: Sistema de Gerenciamento de Empréstimos de Livros

**Projeto:** Gerenciamento de Empréstimo de Livros de Biblioteca  
**Objetivo deste documento:** explicar o sistema do mais simples ao mais completo, usando uma linguagem adequada para apresentação de TCC.

> **Escopo:** este relatório explica o funcionamento online, considerando o Supabase como banco de dados principal. O modo offline, arquivos locais, cache e sincronização local foram desconsiderados.

## 1. Resumo do sistema

O sistema foi criado para organizar as atividades de uma biblioteca escolar. Ele permite cadastrar o acervo e os alunos, registrar empréstimos, registrar devoluções, renovar prazos, consultar a situação dos livros e gerar relatórios.

A aplicação é formada por três partes principais:

| Parte | Função | Tecnologia |
|---|---|---|
| Frontend | Telas, formulários, botões, navegação e leitura da câmera | HTML, CSS e JavaScript |
| Backend | Regras, validações e comunicação com o banco | Python e Flask |
| Banco de dados | Armazenamento dos registros | Supabase/PostgreSQL |

Fluxo geral:

```text
Usuário utiliza a tela
        |
        v
Frontend JavaScript envia uma requisição HTTP
        |
        v
Backend Flask recebe e valida os dados
        |
        v
Supabase grava ou consulta os dados
        |
        v
Backend devolve uma resposta
        |
        v
Frontend atualiza a tela
```

## 2. Organização do projeto

| Local | Responsabilidade |
|---|---|
| `backend/app.py` | Cria o servidor Flask e registra as rotas |
| `backend/api/auth.py` | Login por usuário e senha |
| `backend/api/books.py` | Cadastro e manutenção de livros |
| `backend/api/students.py` | Cadastro e manutenção de alunos |
| `backend/api/loans.py` | Empréstimos, devoluções e renovações |
| `backend/api/rooms.py` | Cadastro de salas |
| `backend/api/genres.py` | Cadastro de gêneros |
| `backend/api/reports.py` | Gráficos, consultas e exportações |
| `backend/scanner/routes.py` | QR Codes e cartões imprimíveis |
| `frontend/index.html` | Estrutura das telas |
| `frontend/assets/js/app.js` | Controle dos fluxos da interface |
| `frontend/assets/js/api.js` | Comunicação com o backend |
| `database.sql` | Tabelas, relacionamentos, índices e views |

O arquivo `app.py` registra os grupos de rotas, chamados de *blueprints*:

```python
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(books_bp, url_prefix="/api/books")
app.register_blueprint(students_bp, url_prefix="/api/students")
app.register_blueprint(loans_bp, url_prefix="/api/loans")
```

Isso significa, por exemplo, que uma rota criada em `loans.py` começa com `/api/loans`.

**Observação sobre o login:** o arquivo `auth.py` não possui uma lista fixa de usuários para o login comum. Ele consulta a tabela `usuarios` no Supabase. Os usuários de exemplo aparecem no `database.sql`, mas só passam a existir no banco depois que esse SQL é executado no projeto Supabase. Se a tabela ou a conexão não estiver disponível, o login comum não consegue validar o usuário; ele não busca usuários nos arquivos locais.

## 3. Banco de dados

O banco possui tabelas que representam as principais entidades do sistema:

| Tabela | O que representa | Exemplo de informação |
|---|---|---|
| `usuarios` | Pessoas que podem entrar no sistema | login, senha e nome |
| `livros` | Obras disponíveis no acervo | título, autor e ISBN |
| `alunos` | Pessoas que podem pegar livros | nome, turma e carteirinha |
| `salas` | Salas ou turmas da escola | nome, código e capacidade |
| `generos` | Categorias dos livros | romance, aventura ou história |
| `emprestimos` | Histórico das retiradas | aluno, livro e datas |
| `relatorios_mensais` | Resumos de um mês | totais e rankings |

### 3.1 Identificadores e relacionamentos

Cada registro possui um `id` único. O banco utiliza UUID, que é um identificador grande e difícil de repetir.

```sql
id UUID PRIMARY KEY DEFAULT uuid_generate_v4()
```

As relações principais são:

| Relação | Explicação |
|---|---|
| Livro -> empréstimos | Um livro pode aparecer em vários empréstimos ao longo do tempo |
| Aluno -> empréstimos | Um aluno pode ter vários empréstimos |
| Livro -> gênero | Um livro pode pertencer a um gênero |
| Aluno -> sala | Um aluno pode estar vinculado a uma sala |
| Empréstimo -> exemplar | Cada empréstimo identifica a cópia física utilizada |

No banco, um empréstimo aponta para o livro e para o aluno usando chaves estrangeiras:

```sql
livro_id UUID NOT NULL REFERENCES livros(id)
aluno_id UUID NOT NULL REFERENCES alunos(id)
```

## 4. Como funciona o login

O login pode ser feito com usuário e senha.

### 4.1 Fluxo do login

1. O usuário digita login e senha.
2. O frontend verifica se os campos não estão vazios.
3. O frontend envia um `POST` para `/api/auth/login`.
4. O backend procura o login na tabela `usuarios`.
5. O backend confere a senha armazenada.
6. Se os dados estiverem corretos, devolve o nome, o login, o ID e o tipo de acesso.
7. O frontend libera o painel principal.

Portanto, o caminho real é:

```text
Usuário e senha -> /api/auth/login -> tabela usuarios do Supabase
                 -> verifica senha -> devolve access, nome, login e id
```

O `database.sql` contém usuários de exemplo:

```sql
INSERT INTO usuarios (nome, login, senha) VALUES
    ('Administrador', 'admin', 'narceu2026'),
    ('Bibliotecária', 'biblioteca', 'narceu2026');
```

Esse trecho apenas prepara os dados iniciais. Ele não é executado automaticamente pelo Flask. Por isso, se esses usuários não estiverem cadastrados no Supabase, o login não funcionará, mesmo que eles estejam escritos no arquivo SQL.

Código do frontend:

```javascript
const response = await fetch("/api/auth/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ login: user, password: pass })
});
```

Código simplificado do backend:

```python
user = _get_user_by_login(login_str)

if not user:
    return jsonify({"error": "Usuário ou senha incorretos"}), 401

if not _verify_password(password, user.get("senha", "")):
    return jsonify({"error": "Usuário ou senha incorretos"}), 401
```

### 4.2 Tipos de acesso

O backend retorna um campo chamado `access`:

| Valor | Significado na aplicação |
|---|---|
| `admin` | Administrador |
| `librarian` | Bibliotecário |

Depois do sucesso, o frontend cria um objeto em memória:

```javascript
_finishLogin({
  role: "admin",
  login: result.login,
  name: result.name
});
```

O sistema usa esse papel somente para mostrar ou esconder partes da interface. As rotas da API não verificam sessão, token ou papel. Portanto, chamadas diretas aos endpoints não são protegidas por autorização de usuário.

O campo `access` também não vem de uma coluna de papel na tabela `usuarios`. O backend calcula esse valor com base no login: `biblioteca` ou `bibliotecario` recebe `librarian`; qualquer outro login autenticado recebe `admin`.

### 4.3 Por que pode parecer que o login não vem do banco?

Há três situações diferentes no projeto:

| Situação | O que realmente acontece |
|---|---|
| Login comum na aplicação | Consulta `usuarios` no Supabase |
| Testes automatizados | Usam um cliente falso criado dentro do teste, sem acessar o Supabase real |
| Login por QR administrativo | Interpreta códigos com prefixo `ADMIN-`, sem consultar uma senha de usuário |

Assim, a frase correta para a apresentação é: **o login comum foi programado para vir do Supabase, mas depende de a tabela `usuarios` estar criada, preenchida e acessível. Os testes não comprovam uma conexão real, pois substituem o cliente por dados simulados. Já o QR administrativo não consulta a tabela `usuarios`: qualquer código iniciado por `ADMIN-` é aceito como acesso administrativo.**

## 5. Cadastro de livros

Para cadastrar um livro, são necessários pelo menos título e autor.

```python
if not body.get("titulo") or not body.get("autor"):
    return jsonify({"error": "titulo e autor são obrigatórios"}), 400
```

O sistema também pode receber:

- ISBN;
- área;
- gênero;
- quantidade de exemplares.

O backend cria um ID para o livro e prepara os exemplares:

```python
book_id = new_id()
copies = max(1, int(body.get("exemplares", 1)))
```

Se forem cadastrados três exemplares, eles podem receber os códigos `001`, `002` e `003`.

Cada exemplar também recebe um identificador próprio:

```python
exemplar_id = f"{book_id}-EX-{code}-{new_id()}"
```

Isso é importante porque duas cópias do mesmo título não são necessariamente a mesma cópia física.

Antes de excluir um livro, o sistema consulta seus empréstimos ativos. Se houver algum, a exclusão é bloqueada:

```python
if ativos:
    return jsonify({"error": "Livro possui empréstimos ativos."}), 409
```

Isso impede a exclusão enquanto existe uma retirada em aberto. Porém, depois que todos os empréstimos forem devolvidos, o livro pode ser apagado fisicamente. Como `livro_id` usa `ON DELETE CASCADE`, essa exclusão pode remover também os empréstimos relacionados e afetar o histórico. Para alunos, o endpoint usa `deleted_at` e faz uma exclusão lógica: o registro permanece no banco, mas deixa de aparecer nas listagens.

## 6. Cadastro de alunos

Para cadastrar um aluno, o sistema exige nome e turma:

```python
if not body.get("nome") or not body.get("turma"):
    return jsonify({"error": "nome e turma são obrigatórios"}), 400
```

Também podem ser informados:

- Carteirinha;
- Sala;
- Turma.

Se a carteirinha não for informada, o sistema usa parte do ID como valor padrão:

```python
card = (body.get("carteirinha") or "").strip() or sid[:8]
```

Isso significa que a carteirinha pode ser digitada pela escola ou gerada automaticamente. O valor informado passa por `strip()`, que remove espaços no início e no fim. Quando o campo fica vazio, são usados os oito primeiros caracteres do ID único do aluno. Se o valor já pertencer a outro aluno, o cadastro é recusado para evitar duplicidade.

A carteirinha exibida e o conteúdo do QR Code não são exatamente a mesma coisa. A carteirinha mostra o valor do campo `carteirinha`, mas o QR Code guarda o ID completo do aluno. Assim, a leitura do QR localiza o aluno pelo ID; a busca digitada também pode encontrar o registro pela carteirinha.

Depois do cadastro, o sistema gera automaticamente uma imagem PNG da carteirinha. Essa imagem contém o nome, a turma, a sala, o número da carteirinha, os oito primeiros caracteres do ID e um QR Code com o ID completo do aluno. Na lista de alunos, o botão com o ícone de impressora gera novamente esse cartão.

Na tela aberta para o cartão existem duas opções:

1. **Imprimir:** abre a caixa de impressão do navegador.
2. **Baixar PNG:** salva a imagem da carteirinha como arquivo PNG.

Se o navegador bloquear a nova aba, é necessário permitir pop-ups para o endereço da aplicação.

A turma é convertida para letras maiúsculas, facilitando a padronização:

```python
"turma": body["turma"].strip().upper()
```

Um aluno com empréstimo ativo não deve ser excluído. O sistema verifica essa situação antes da exclusão.

## 7. Salas e gêneros

Salas organizam os alunos. Uma sala possui nome, código, descrição e capacidade.

Gêneros organizam os livros. Um gênero possui nome, ícone e cor. Por exemplo:

| Gênero | Uso |
|---|---|
| Técnico / Didático | Livros escolares e técnicos |
| Ficção Científica | Histórias de ciência e futuro |
| Romance | Narrativas românticas |
| História | Livros históricos |
| Outros | Categorias que não se encaixam nas anteriores |

Ao excluir um gênero, os livros relacionados não são excluídos. O vínculo do gênero é apenas removido:

```sql
genero_id UUID REFERENCES generos(id) ON DELETE SET NULL
```

A mesma ideia é usada para salas: excluir uma sala não apaga o aluno, apenas remove o vínculo com aquela sala.

## 8. Empréstimo de livro

O empréstimo é a operação central do sistema.

### 8.1 Fluxo pela tela

1. O bibliotecário pesquisa o livro por título, ISBN ou ID.
2. Também pode escanear o QR Code do livro ou exemplar.
3. O sistema mostra quantos exemplares estão disponíveis.
4. O bibliotecário seleciona um aluno por nome, ID, carteirinha ou QR Code.
5. O sistema mostra se o aluno está regular ou possui empréstimos atrasados.
6. O bibliotecário informa o prazo.
7. O botão de confirmação envia os dados ao backend.
8. O backend valida tudo e grava o empréstimo no Supabase.

O frontend envia este tipo de informação:

```javascript
const payload = {
  livro_id: pendingLoan.book.id,
  aluno_id: pendingLoan.student.id,
  exemplar: pendingLoan.exemplar,
  dias: days,
  data_emprestimo: date,
  observacao: obs,
  criado_por: currentUser?.login || "sistema"
};
```

### 8.2 Validações do backend

O backend verifica:

| Verificação | Resultado se falhar |
|---|---|
| Livro foi informado? | Erro 400 |
| Aluno foi informado? | Erro 400 |
| Livro existe? | Erro 404 |
| Aluno existe? | Erro 404 |
| Há exemplar livre? | Erro 409 |
| O exemplar escolhido está livre? | Erro 409 |

Trecho principal:

```python
if not book_id or not student_id:
    return jsonify({"error": "livro_id e aluno_id são obrigatórios"}), 400

if not books:
    return jsonify({"error": "Livro não encontrado"}), 404

if not avail:
    return jsonify({"error": "Nenhum exemplar disponível no momento"}), 409
```

### 8.3 Escolha do exemplar

O sistema consulta os empréstimos que ainda não possuem data de devolução. Esses são os empréstimos ativos.

```python
rows = sb_exec(
    sb.table("emprestimos")
      .select("exemplar", "exemplar_id")
      .eq("livro_id", book_id)
      .is_("devolvido_em", "null")
)
```

Depois, ele compara os exemplares usados com a lista total e monta a lista dos disponíveis. Se o bibliotecário não escolher uma cópia específica, o sistema usa a primeira livre:

```python
exemplar_info = avail[0]
```

### 8.4 Datas e registro

O prazo padrão é de sete dias. O usuário pode informar outra quantidade, mas o sistema sempre considera pelo menos um dia.

```python
try:
    days = max(1, int(body.get("dias", 7)))
except:
    days = 7
```

O registro salvo possui, entre outros, estes campos:

| Campo | Função |
|---|---|
| `id` | Identifica o empréstimo |
| `livro_id` | Identifica o livro |
| `aluno_id` | Identifica o aluno |
| `exemplar` | Código da cópia, como `001` |
| `exemplar_id` | Identificador específico da cópia |
| `data_emprestimo` | Data da retirada |
| `data_devolucao_prevista` | Prazo esperado |
| `devolvido_em` | Data real da devolução; começa vazia |
| `observacao` | Anotação opcional |
| `criado_por` | Usuário que fez a operação |

O payload de criação é semelhante a este:

```python
payload = {
    "id": new_id(),
    "livro_id": book_id,
    "aluno_id": student_id,
    "exemplar": exemplar_info["code"],
    "exemplar_id": exemplar_info["id"],
    "data_emprestimo": dt,
    "data_devolucao_prevista": add_days(dt, days),
    "devolvido_em": None
}
```

O banco também possui uma regra para não permitir dois empréstimos ativos do mesmo exemplar:

```sql
CREATE UNIQUE INDEX idx_exemplar_ativo
ON emprestimos (livro_id, exemplar)
WHERE devolvido_em IS NULL;
```

## 9. Situação do empréstimo

A função `loan_status` classifica cada empréstimo:

```python
def loan_status(loan):
    if loan.get("devolvido_em"):
        return "returned"
    return "overdue" if days_until(due) < 0 else "active"
```

| Situação interna | Significado |
|---|---|
| `active` | Está emprestado e ainda não venceu |
| `overdue` | Está emprestado e passou do prazo |
| `returned` | Foi devolvido |

A lógica é simples:

```text
Existe data de devolução?
    Sim -> devolvido
    Não -> compara o prazo com a data atual
             prazo vencido -> atrasado
             prazo não vencido -> ativo
```

## 10. Devolução

### 10.1 Fluxo

1. O sistema localiza o empréstimo pelo ID.
2. Confirma que o empréstimo existe.
3. Confirma que ele ainda está aberto.
4. Opcionalmente, confere a identificação do aluno.
5. Grava a data de devolução.
6. O empréstimo deixa de ser ativo.
7. O exemplar volta a aparecer como disponível.

Trecho da validação:

```python
if not loans:
    return jsonify({"error": "Empréstimo não encontrado"}), 404

if loans[0].get("devolvido_em"):
    return jsonify({"error": "Empréstimo já foi devolvido"}), 409
```

A atualização enviada ao banco é:

```python
upd = {
    "devolvido_em": body.get("devolvido_em") or today_str(),
    "observacao": body.get("observacao", "") or ""
}
```

Depois da devolução, `devolvido_em` deixa de ser nulo. Por isso, o registro não entra mais na lista de empréstimos ativos e o exemplar pode ser escolhido novamente.

### 10.2 Conferência do aluno

A devolução pode receber o ID, QR Code ou carteirinha do aluno. Quando essa informação é enviada, o backend compara o aluno identificado com o aluno que realizou o empréstimo:

```python
if str(student.get("id", "")) != str(loan["aluno_id"]):
    return jsonify({"error": "Este exemplar pertence a outro aluno."}), 403
```

Na implementação atual, essa conferência é opcional. Portanto, uma devolução sem identificação do aluno ainda pode ser aceita.

## 11. Renovação

A renovação aumenta a data prevista de devolução de um empréstimo ativo.

Fluxo:

1. O usuário escolhe um empréstimo ativo.
2. Informa quantos dias deseja acrescentar.
3. O backend verifica se o empréstimo já foi devolvido.
4. Soma os dias ao prazo atual.
5. Aumenta o contador `renovacoes`.
6. Atualiza o registro no Supabase.

Código principal:

```python
if loan.get("devolvido_em"):
    return jsonify({
        "error": "Empréstimo já foi devolvido — não é possível renovar"
    }), 409

nova_data = add_days(base, days)
upd = {
    "data_devolucao_prevista": nova_data,
    "renovacoes": renov_anterior + 1
}
```

O sistema atual não define um número máximo de renovações.

## 12. QR Codes

QR Code é um código visual que armazena um texto. Neste sistema, esse texto normalmente é um ID ou um código especial. O QR não precisa guardar todos os dados do livro ou do aluno; depois da leitura, o sistema usa o código para fazer uma consulta.

### 12.1 Tipos de QR Code

| Tipo | Conteúdo aproximado | Uso |
|---|---|---|
| Livro | ID do livro | Encontrar uma obra |
| Exemplar | `EXEMPLAR-...` | Encontrar uma cópia específica |
| Aluno | ID do aluno | Identificar o aluno |
| Administrador | `ADMIN-admin` ou semelhante | Login por QR |

### 12.2 QR de livro

Ao criar um livro, o backend transforma o ID em uma imagem PNG codificada em Base64 e envia essa imagem na resposta HTTP. O QR não é salvo como uma imagem no banco; seu conteúdo é o ID do livro:

```python
qr.add_data(payload["id"])
img.save(buf, format="PNG")
result["qr_code"] = "data:image/png;base64," + base64.b64encode(
    buf.getvalue()
).decode()
```

O navegador consegue mostrar essa imagem diretamente porque ela começa com `data:image/png;base64,`.

### 12.3 QR de exemplar

O cadastro cria metadados e códigos de exemplar, e os cartões de livro podem gerar um QR individual para cada exemplar. O padrão usado é semelhante a:

```text
EXEMPLAR-ID_DO_LIVRO-EX-001-ID_UNICO
```

O frontend separa esse texto para descobrir:

- ID do livro;
- código do exemplar, como `001`;
- ID completo do exemplar.

Trecho da interpretação:

```javascript
if (!normalized.toUpperCase().startsWith("EXEMPLAR-")) return null;
```

Assim, ao escanear uma cópia específica, o sistema pode mostrar exatamente qual exemplar será emprestado. Livros antigos sem `exemplares_meta` recebem apenas um cartão com o ID do livro.

### 12.4 QR de aluno

Ao cadastrar um aluno, o QR Code recebe o ID dele:

```python
qr.add_data(sid)
```

Quando o código é lido, o sistema procura o ID na tabela `alunos`. Se encontrar, retorna os dados do aluno para o fluxo de empréstimo.

### 12.5 Busca da carteirinha no histórico

Na tela de empréstimos, o botão **Escanear aluno** lê o QR Code da carteirinha. O frontend recebe o texto do QR, que normalmente é o ID completo do aluno, e chama a resolução do código.

O sistema procura nesta ordem:

1. nos alunos já sincronizados no navegador, comparando o ID ou a carteirinha;
2. no backend, pelo ID do aluno;
3. no backend, pela carteirinha.

Quando encontra o aluno, o sistema preenche a identificação, mostra o nome e a turma, calcula a situação dos empréstimos e abre o histórico. O histórico filtra os registros de `emprestimos` cujo `aluno_id` é igual ao ID encontrado. Dessa forma, o QR não armazena o histórico: ele apenas permite localizar o aluno que está relacionado aos empréstimos.

Se o código for de um livro, de um administrador ou não for reconhecido, o sistema não abre o histórico e informa que o QR é incompatível ou desconhecido.

### 12.5 Leitura do QR

O scanner do navegador usa a câmera, o vídeo e o processamento JavaScript. O callback recebe o texto lido e chama a resolução do código:

```javascript
const scanned = await resolveQRCodeAsync(code);

if (scanned.type === "student") {
  setLoanStudent(scanned.data);
}
```

O sistema diferencia os códigos desta forma:

```text
Começa com ADMIN-?       -> administrador
Começa com EXEMPLAR-?    -> exemplar de livro
É ID/carteirinha de aluno? -> aluno
É ID/ISBN de livro?      -> livro
Caso contrário           -> desconhecido
```

## 13. Login por QR Code

Existe um fluxo diferente do login com senha:

1. A câmera lê o QR Code.
2. O frontend envia o texto para `/api/qr/login`.
3. O backend interpreta o código.
4. Um QR `ADMIN-...` retorna acesso administrativo, sem validar usuário ou senha no banco.
5. Um QR de aluno com `is_librarian = true` retorna acesso de bibliotecário.
6. Um aluno comum recebe acesso negado ao painel.

No frontend, a leitura envia o texto do QR para `POST /api/qr/login`. O backend resolve o código e devolve o tipo de acesso. Para um QR de aluno, ele localiza o cadastro pelo ID ou pela carteirinha e verifica o campo `is_librarian`. Se esse campo for verdadeiro, o frontend inicia a sessão em memória como `librarian`; caso contrário, mostra que a carteirinha não possui acesso ao painel.

Há uma diferença importante no cartão administrativo: códigos iniciados por `ADMIN-` são interpretados como administradores. Nesse fluxo atual, o backend não consulta a tabela `usuarios` nem exige uma senha adicional. Portanto, essa regra deve ser apresentada como uma limitação de segurança do sistema.

Se o QR for de um livro, de um exemplar ou estiver inválido, o login é negado e o sistema informa que o código não foi reconhecido ou deve ser usado em outra tela.

Código do backend:

```python
if resolved["type"] == "admin":
    return jsonify({"access": "admin", **resolved})

if resolved["type"] == "student":
    if student.get("is_librarian"):
        return jsonify({"access": "librarian", "data": student})
```

Ponto importante para a apresentação: qualquer código iniciado por `ADMIN-` é interpretado como administrativo. O backend não confirma se o login informado existe na tabela `usuarios` e não pede uma senha adicional nesse fluxo. Além disso, o cartão chamado `bibliotecario` também usa o prefixo `ADMIN-`, portanto ele retorna acesso `admin`, não `librarian`.

## 14. API e comunicação

O arquivo `api.js` centraliza as requisições do frontend. A função `apiFetch` monta a URL, envia o pedido e transforma erros HTTP em erros JavaScript.

```javascript
const res = await fetch(API_BASE + path, {
  headers: { "Content-Type": "application/json" },
  ...options,
});

if (!res.ok) throw new Error(data.error || `Erro HTTP ${res.status}`);
```

### 14.1 Principais endpoints

A tabela abaixo apresenta apenas os endpoints mais usados. Também existem rotas para salas, gêneros, atualização e exclusão de livros e alunos, importação CSV, concessão de acesso de bibliotecário, decodificação de QR, cartões imprimíveis e controle do scanner.

| Método | Endpoint | Função |
|---|---|---|
| `POST` | `/api/auth/login` | Login com usuário e senha |
| `GET` | `/api/books/` | Lista livros |
| `POST` | `/api/books/` | Cria livro |
| `PUT` | `/api/books/<id>` | Atualiza livro |
| `DELETE` | `/api/books/<id>` | Exclui livro |
| `GET` | `/api/students/` | Lista alunos |
| `POST` | `/api/students/` | Cria aluno |
| `POST` | `/api/loans/` | Cria empréstimo |
| `POST` | `/api/loans/<id>/return` | Registra devolução |
| `POST` | `/api/loans/<id>/renew` | Renova prazo |
| `GET` | `/api/reports/chart-summary` | Dados para gráficos |
| `POST` | `/api/qr/login` | Login por QR |
| `POST` | `/api/qr/generate` | Gera QR em PNG |
| `GET` | `/api/health` | Verifica o serviço e o banco |

## 15. Relatórios

Os resumos, rankings, agrupamentos e exportações são calculados a partir de livros, alunos e empréstimos. O relatório mensal também pode ser salvo na tabela `relatorios_mensais` pelo endpoint de geração.

O painel pode mostrar:

| Relatório | O que apresenta |
|---|---|
| Resumo | Quantidade de ativos, atrasados e devolvidos |
| Livros mais emprestados | Ranking por quantidade de empréstimos |
| Por turma | Quantidade de empréstimos por turma |
| Mensal | Totais de um mês e rankings |
| Atrasados | Lista para exportação CSV |
| Histórico completo | Todos os empréstimos e suas situações |
| Status dos alunos | Livros associados a cada aluno |

A função de resumo conta os empréstimos por situação:

```python
active = sum(1 for l in loans if loan_status(l) == "active")
overdue = sum(1 for l in loans if loan_status(l) == "overdue")
returned = sum(1 for l in loans if loan_status(l) == "returned")
```

Os relatórios podem ser usados pela escola para descobrir quais livros são mais procurados, quais turmas usam mais a biblioteca e quais empréstimos estão atrasados.

## 16. Regras importantes do banco

| Regra | Motivo |
|---|---|
| Livro precisa ter título | Evita cadastro sem identificação |
| Livro precisa ter autor | Completa a identificação da obra |
| Aluno precisa ter nome e turma | Permite identificar o usuário |
| Exemplar deve ser maior ou igual a 1 | Evita livro sem cópia |
| Carteirinha é única | Evita duas pessoas com a mesma identificação |
| QR de livro e aluno é único | Os campos `qr_id` são únicos no schema, mas os cadastros atuais não preenchem esses campos; a identificação efetiva usa principalmente os IDs gerados |
| Exemplar ativo é único | Evita empréstimo duplicado da mesma cópia |
| Livro ou aluno com empréstimo ativo não é excluído | Bloqueia a operação enquanto há retirada aberta; livros podem ser apagados depois e alunos são marcados com `deleted_at` |
| Empréstimo devolvido não pode ser renovado | Impede alteração indevida do histórico |

## 17. Testes existentes

O projeto possui testes automatizados para alguns comportamentos:

Esses testes são pontuais. Não há cobertura abrangente de permissões, RLS, CRUD completo, concorrência de empréstimos, devoluções, renovações ou segurança.

| Teste | O que verifica |
|---|---|
| Login de bibliotecário | Login e aliases de usuário |
| Ambiente | Carregamento de configurações |
| QR e IDs | Resolução de códigos e identificadores |
| Relatórios | Situação dos alunos |
| Identificadores únicos | IDs diferentes para registros diferentes |
| Scanner JavaScript | Callback básico do scanner |

Um exemplo verifica que dois livros com o mesmo título ainda recebem IDs diferentes:

```python
assert first_data["id"] != second_data["id"]
assert first_data["exemplares_ids"][0] != second_data["exemplares_ids"][0]
```

Isso demonstra que dois livros com o mesmo título recebem IDs diferentes e que seus exemplares também recebem IDs diferentes. Esse teste não comprova a unicidade de alunos, empréstimos ou IDs gerados diretamente pelo banco.

## 18. Pontos fortes

- Organiza os principais dados de uma biblioteca.
- Separa frontend, backend e banco.
- Usa IDs únicos para livros, alunos e empréstimos.
- Diferencia livro e exemplar físico.
- Calcula automaticamente o prazo de devolução.
- Identifica empréstimos atrasados.
- Impede empréstimo de exemplar já ocupado.
- Permite leitura e geração de QR Codes.
- Possui relatórios e exportações.
- Possui testes automatizados pontuais, mas não uma cobertura completa do sistema.

## 19. Limitações atuais

Estas limitações fazem parte do código atual e devem ser apresentadas com honestidade:

| Limitação | Explicação simples |
|---|---|
| Sessão não persistente | Depois do login, o sistema guarda o usuário apenas em memória do navegador |
| Autorização incompleta | O backend não exige o papel do usuário em todas as rotas |
| QR administrativo sem segunda confirmação | O QR pode funcionar como acesso administrativo sozinho |
| Limite de renovação ausente | Não existe quantidade máxima de renovações |
| Devolução com identificação opcional | É possível devolver sem informar a carteirinha |
| Senhas iniciais inseguras no SQL | O arquivo SQL possui senhas de exemplo em texto puro |
| Políticas RLS abertas | As políticas atuais usam `USING (true)` e `WITH CHECK (true)` |

## 20. Auditoria de segurança

Esta seção descreve problemas de segurança encontrados no código online. Ela é importante para a apresentação porque mostra não somente o que o sistema faz, mas também em quais condições ele ainda não deve ser usado em produção.

### 20.1 Resumo dos riscos

| Severidade | Problema | Consequência |
|---|---|---|
| Crítica | APIs sem autenticação e autorização | Qualquer pessoa pode tentar alterar livros, alunos e empréstimos |
| Crítica | RLS aberta no SQL | As políticas não confirmam quem está acessando os dados |
| Crítica | Possível envio da `SUPABASE_SERVICE_KEY` | Uma chave privilegiada pode chegar ao navegador |
| Crítica | QR `ADMIN-*` sem validação | Um texto previsível pode ser aceito como acesso administrativo |
| Alta | Senha inicial em texto puro | A senha pode ser descoberta diretamente no SQL |
| Alta | Dados pessoais sem proteção | Alunos, carteirinhas e empréstimos podem ser consultados sem login |
| Alta | HTML inserido diretamente na tela | Nomes ou títulos maliciosos podem causar XSS |
| Alta | Sem limite de tentativas de login | Facilita ataques de força bruta |
| Média | CORS permite qualquer origem | Sites externos podem fazer chamadas para a API |
| Média | Validação e limites incompletos | Entradas enormes ou valores inválidos podem causar problemas |

### 20.2 Falta de autenticação contínua

O login verifica usuário e senha, mas depois não existe sessão, cookie seguro, JWT ou outro token enviado nas requisições seguintes. As rotas de livros, alunos, empréstimos e relatórios não possuem um bloqueio que confirme a identidade do usuário.

Na prática, esconder um botão no frontend não protege a API. Uma pessoa poderia enviar uma requisição diretamente para um endpoint, sem passar pela tela.

**Correção recomendada:** criar autenticação contínua e funções de autorização no backend, como `require_login()` e `require_admin()`. Cada operação deve verificar o usuário antes de consultar ou alterar dados.

### 20.3 RLS permissiva

No `database.sql`, várias políticas usam:

```sql
USING (true) WITH CHECK (true)
```

Isso significa, de forma simples, que a política não restringe por usuário. A tabela `usuarios` ainda possui a coluna `senha`, por isso ela não deveria ser lida publicamente.

**Correção recomendada:** usar políticas baseadas em usuários autenticados e seus papéis. A senha nunca deve ser retornada em consultas públicas.

### 20.4 Chave privilegiada do Supabase

O endpoint de configuração pode escolher `SUPABASE_SERVICE_KEY` quando `SUPABASE_KEY` não está disponível. A chave `service_role` é privilegiada e deve permanecer somente no servidor.

**Impacto:** se essa chave for enviada ao navegador, alguém pode extraí-la e usá-la fora da aplicação.

**Correção recomendada:** nunca retornar `SUPABASE_SERVICE_KEY` em uma resposta HTTP. O navegador deve receber apenas uma chave pública, quando necessário, e o backend deve guardar a chave privilegiada em variável de ambiente protegida.

### 20.5 QR Code administrativo

O backend classifica qualquer código iniciado por `ADMIN-` como administrador. Por exemplo, `ADMIN-qualquer-texto` pode ser interpretado como uma credencial válida, sem consulta à tabela `usuarios` e sem senha adicional.

**Correção recomendada:** usar um token aleatório, assinado e com validade curta, ou exigir senha/segunda confirmação. O texto do QR não deve ser suficiente para liberar acesso administrativo.

### 20.6 Senhas e força bruta

O SQL possui senhas de exemplo em texto puro, e o backend ainda aceita senhas legadas sem hash para depois tentar convertê-las. Além disso, não há limite de tentativas de login.

**Correções recomendadas:**

- armazenar somente hashes com bcrypt ou Argon2id;
- remover senhas conhecidas do SQL de produção;
- exigir troca de senha inicial;
- limitar tentativas por IP e por conta;
- registrar tentativas suspeitas;
- manter a mesma mensagem para usuário inexistente e senha errada.

### 20.7 Dados pessoais e XSS

As APIs podem retornar dados como nome, turma, carteirinha e histórico de empréstimos sem autenticação. Isso expõe informações pessoais desnecessariamente.

Além disso, algumas páginas colocam valores vindos do banco diretamente em `innerHTML` e em atributos `onclick`. Se alguém cadastrar um título ou nome contendo HTML malicioso, esse conteúdo pode ser executado no navegador. Esse tipo de falha é chamado de XSS, ou execução de script entre sites.

**Correção recomendada:** proteger as rotas, retornar somente os campos necessários e usar `textContent` ou criação segura de elementos DOM. Valores nunca devem ser colocados diretamente em HTML ou em eventos inline sem escape apropriado.

### 20.8 CORS, validações e concorrência

O servidor configura `origins: "*"`, permitindo chamadas da API a partir de qualquer origem. Também faltam limites consistentes para tamanho de textos, datas, quantidade de dias, parâmetro `limit` dos relatórios e arquivos CSV.

No empréstimo, o banco possui um índice único que impede dois empréstimos ativos da mesma cópia. Isso é um ponto positivo. Porém, em duas requisições simultâneas, uma delas pode falhar como erro inesperado em vez de retornar claramente `409 Conflict`.

**Correções recomendadas:** restringir o CORS ao domínio da aplicação, validar tamanho e formato no servidor, limitar consultas e arquivos e tratar violação de unicidade como conflito de empréstimo.

### 20.9 O que não foi encontrado

Não encontrei consultas SQL montadas por concatenação. As consultas observadas usam o construtor do cliente Supabase, portanto não há evidência de SQL Injection tradicional no código analisado.

Isso não significa que o sistema esteja seguro: a ausência de SQL Injection não corrige a falta de autenticação, as políticas RLS abertas, a exposição potencial de chave, o QR administrativo nem o XSS.

### 20.10 Testes de segurança que ainda faltam

| Teste | Objetivo |
|---|---|
| Acessar cada endpoint sem login | Confirmar que APIs privadas são bloqueadas |
| Usar perfil bibliotecário em operação administrativa | Confirmar separação de funções |
| Usar QR `ADMIN-` falso | Confirmar que o código não libera acesso sozinho |
| Verificar resposta de configuração | Garantir que a `service_role` nunca seja enviada |
| Cadastrar HTML em título e nome | Verificar proteção contra XSS |
| Fazer muitas tentativas de senha | Verificar proteção contra força bruta |
| Enviar valores muito grandes ou inválidos | Verificar limites e validações |
| Criar dois empréstimos simultâneos | Verificar tratamento do conflito |
| Testar RLS com usuários reais | Confirmar as permissões no Supabase |

## 21. Exemplo de apresentação completa

Uma forma simples de explicar o funcionamento para a banca é:

> O usuário acessa a aplicação pelo navegador. O frontend apresenta os formulários e envia as ações para uma API criada em Flask. O backend valida as informações e consulta o Supabase, que armazena livros, alunos e empréstimos. Para realizar um empréstimo, o sistema identifica o livro, encontra um exemplar disponível, identifica o aluno, calcula a data de devolução e grava o registro. Na devolução, ele preenche a data real, liberando o exemplar novamente. Os QR Codes facilitam a identificação porque guardam IDs ou códigos, que são usados para localizar os registros no banco. Os relatórios transformam o histórico de empréstimos em informações para a gestão da biblioteca.

## 22. Conclusão

O sistema é uma aplicação web de gerenciamento de biblioteca. Seu funcionamento pode ser resumido em quatro ações:

```text
Cadastrar -> identificar -> registrar empréstimo -> controlar devolução
```

O login identifica o tipo de usuário, os cadastros alimentam o banco, o empréstimo relaciona livro, exemplar e aluno, e a devolução encerra essa relação. Os QR Codes tornam a identificação mais rápida, enquanto os IDs garantem que cada registro e cada exemplar sejam reconhecidos corretamente.

A solução já cobre o fluxo principal de uma biblioteca escolar. Para uma evolução futura, as prioridades seriam implementar autenticação contínua, autorização no backend, proteção adicional para QR administrativo, limite de renovações e testes mais amplos de segurança.
