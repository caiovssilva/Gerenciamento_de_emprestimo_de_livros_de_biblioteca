# Relatório: Consulta de livros por ISBN

## 1. Objetivo

Este relatório documenta como o sistema consulta livros por ISBN, desde a entrada do usuário no frontend até a resposta das fontes externas e o preenchimento do formulário de cadastro.

A análise foi feita sobre o código existente no frontend, backend, banco de dados e testes. Nenhum código de aplicação foi alterado.

## 2. Fluxo completo

1. O usuário abre o modal de cadastro de livro em `frontend/index.html`.
2. O ISBN é informado no campo `book-isbn` por digitação manual ou pelo botão `Ler`.
3. O botão `Ler` chama `scanBookIsbn()` em `frontend/assets/js/pages/books.js`.
4. `scanBookIsbn()` inicia `QRScanner.start("book-isbn", ...)`.
5. `frontend/assets/js/qr-scanner.js` tenta ler o código pela câmera usando:
   - `jsQR` para QR Code;
   - `BarcodeDetector` para formatos de código de barras compatíveis;
   - `/api/qr/decode` como fallback para decodificação da imagem no backend.
6. Depois da leitura, o valor é normalizado por `_normalizeIsbn()`.
7. `lookupBookIsbn()` também normaliza o valor e chama `API.books.lookupIsbn(isbn)`.
8. `API.books.lookupIsbn()` executa uma requisição GET para:

   ```text
   /api/books/isbn-lookup?isbn=<ISBN-normalizado>
   ```

9. O backend registra essa rota pelo blueprint de livros com o prefixo `/api/books`.
10. A função `lookup_isbn()` recebe o parâmetro da query string e chama `_lookup_isbn()`.
11. `_lookup_isbn()` normaliza e valida o ISBN e consulta as fontes externas nesta ordem:
    1. Google Books;
    2. ISBNsearch;
    3. Open Library.
12. Os dados encontrados podem ser combinados. Campos ausentes de uma fonte podem ser completados por outra.
13. O backend tenta associar as categorias encontradas a um gênero local usando `_match_genre()`.
14. A resposta JSON retorna para `apiFetch()` no frontend.
15. `lookupBookIsbn()` utiliza a resposta para preencher os campos do cadastro.
16. O usuário confere os dados e clica em `Salvar`.
17. `saveBook()` envia o ISBN, título, autor, área, quantidade de exemplares e `genero_id` para a rota de criação ou atualização do livro.

## 3. Arquivos e funções

| Arquivo | Função | Responsabilidade |
|---|---|---|
| `frontend/index.html` | formulário do livro | Campo ISBN, botão `Ler` e botão `Pesquisar` |
| `frontend/assets/js/api.js` | `API.books.lookupIsbn()` | Monta a chamada para `/api/books/isbn-lookup` |
| `frontend/assets/js/pages/books.js` | `_normalizeIsbn()` | Remove caracteres não numéricos, preserva `X` e converte para maiúsculas |
| `frontend/assets/js/pages/books.js` | `lookupBookIsbn()` | Consulta o backend, trata a resposta e preenche o formulário |
| `frontend/assets/js/pages/books.js` | `scanBookIsbn()` | Recebe o código da câmera e inicia a consulta |
| `frontend/assets/js/pages/books.js` | `saveBook()` | Persiste o livro depois da conferência do usuário |
| `frontend/assets/js/qr-scanner.js` | `QRScanner.start()` | Abre a câmera e inicia a leitura |
| `frontend/assets/js/qr-scanner.js` | `_capture()` | Captura os frames e tenta decodificar QR/código de barras |
| `backend/api/books.py` | `_normalize_isbn()` | Normaliza o ISBN no backend |
| `backend/api/books.py` | `_google_books_lookup()` | Consulta a Google Books API |
| `backend/api/books.py` | `_isbnsearch_lookup()` | Consulta e interpreta o HTML do ISBNsearch |
| `backend/api/books.py` | `_openlibrary_lookup()` | Consulta a Open Library API |
| `backend/api/books.py` | `_match_genre()` | Relaciona categorias externas a gêneros locais |
| `backend/api/books.py` | `_lookup_isbn()` | Controla a ordem dos provedores, fallback, combinação e cache |
| `backend/api/books.py` | `lookup_isbn()` | Endpoint HTTP `GET /api/books/isbn-lookup` |
| `backend/scanner/routes.py` | `_resolve_qr()` | Resolve QR como ID, ISBN, exemplar, aluno ou cartão administrativo |
| `frontend/assets/js/app.js` | `lookupBook()` | Busca local de livros durante o empréstimo; não consulta as APIs bibliográficas |

## 4. URL completa usada pelo frontend

A URL base é definida em `frontend/assets/js/api.js`:

```javascript
const API_BASE = `${window.location.origin}/api`;
```

Portanto, em execução normal, a URL é:

```text
http(s)://<host>/api/books/isbn-lookup?isbn=<ISBN-normalizado>
```

Se `window.location.origin` não estiver disponível, o código usa:

```text
http://localhost:5000/api/books/isbn-lookup?isbn=<ISBN-normalizado>
```

O parâmetro é codificado com `encodeURIComponent()`.

## 5. Como o ISBN chega ao backend

### Digitação manual

O usuário digita no campo `book-isbn` e clica em `Pesquisar`, que chama `lookupBookIsbn()`.

O campo de cadastro não possui um handler de tecla Enter para iniciar automaticamente essa consulta.

### Câmera

O botão `Ler` chama `scanBookIsbn()`. O scanner usa a câmera do navegador por meio de `navigator.mediaDevices.getUserMedia()`.

A leitura pode ocorrer por:

- `jsQR`, para QR Codes;
- `BarcodeDetector`, para formatos como EAN-13;
- endpoint `/api/qr/decode`, como fallback quando a leitura local não for suficiente.

O código lido é passado como `result.primary`, normalizado e enviado à consulta bibliográfica.

### Tela de empréstimos

A tela de empréstimos também aceita ISBN, mas o comportamento é diferente. A função `lookupBook()` procura nos livros já carregados em `Store.books()` por ISBN, ID ou título. Ela não chama `/api/books/isbn-lookup`.

## 6. Normalização

A função `_normalizeIsbn()` existe no frontend e no backend. Ela:

- converte o valor para texto;
- remove tudo que não seja número ou `X`;
- converte `x` para `X`.

O código verifica apenas se o resultado possui 10 ou 13 caracteres. Não existe validação do dígito verificador do ISBN.

## 7. Fontes externas

### Google Books

URL:

```text
https://www.googleapis.com/books/v1/volumes?q=isbn:<ISBN>
```

Função: `_google_books_lookup()`.

Dados obtidos:

- `isbn`;
- `titulo`;
- `autor`, formado a partir de `authors`;
- `categorias`, formada a partir de `categories`.

A API key é opcional e, quando configurada, é acrescentada como parâmetro `key`.

### ISBNsearch

URL:

```text
https://isbnsearch.org/isbn/<ISBN>
```

Função: `_isbnsearch_lookup()`.

A resposta HTML é interpretada por `_IsbnSearchParser`.

Dados obtidos:

- título, extraído da tag `<title>`;
- autores, extraídos dos campos `Author` ou `Authors`;
- categorias: lista vazia.

### Open Library

URL:

```text
https://openlibrary.org/api/books?bibkeys=ISBN:<ISBN>&jscmd=data&format=json
```

Função: `_openlibrary_lookup()`.

Dados obtidos:

- título;
- autores;
- assuntos, convertidos em `categorias`.

## 8. Fallback e erros

A ordem de tentativa é Google Books, ISBNsearch e Open Library.

Quando o Google Books não encontra um item, `_google_books_lookup()` gera `LookupError` e a próxima fonte é tentada.

Quando o ISBNsearch não encontra título válido, `_isbnsearch_lookup()` gera `LookupError` e a próxima fonte é tentada.

Quando a Open Library não possui dados do ISBN, `_openlibrary_lookup()` gera `LookupError`. Se nenhuma fonte tiver retornado dados, o backend responde com erro HTTP 502.

Erros de rede, timeout e erros HTTP também fazem o backend tentar o próximo provedor.

Se alguma fonte retornar dados parciais, o resultado pode ser mantido e complementado pelas fontes seguintes.

A rota converte os erros da seguinte forma:

- ISBN inválido: HTTP 400;
- nenhuma fonte encontrada: HTTP 502;
- falha de consulta externa: HTTP 502;
- resposta encontrada: HTTP 200.

No frontend, `apiFetch()` transforma respostas não-OK em exceções. `lookupBookIsbn()` captura a exceção, mostra uma mensagem no status do formulário e chama `Utils.toast()`.

A mensagem exibida no formulário é genérica:

```text
Livro não encontrado. Você pode preencher os dados manualmente.
```

Não há indicação de qual provedor falhou.

## 9. Campos preenchidos no formulário

| Campo retornado | Uso no frontend |
|---|---|
| `isbn` | Campo `book-isbn` |
| `titulo` | Campo `book-title`, somente se estiver vazio |
| `autor` | Campo `book-author`, somente se estiver vazio |
| `categorias` | Não preenche campo; aparece no texto de status |
| `area` | Campo `book-area`, somente se estiver vazio |
| `genero_id` | Seleciona o campo `book-genre` quando nenhum gênero já foi escolhido |
| `genero_nome` | Não é utilizado por `lookupBookIsbn()` e não é colocado no formulário |

O gênero é, portanto, parcialmente automático. O backend tenta encontrar um gênero local a partir das categorias externas. Sem correspondência, o usuário precisa escolher manualmente.

Existe uma função frontend chamada `_genreIdFromCategories()`, mas ela não é usada no fluxo atual.

## 10. Uso do ISBN no sistema

O ISBN é usado como metadado bibliográfico e possui índice no banco de dados.

Ele é usado para:

- consulta externa durante o cadastro;
- filtragem da lista de livros;
- busca local durante empréstimos;
- resolução de livros escaneados quando o código corresponde diretamente ao ISBN;
- consulta alternativa na rota `GET /api/books/<book_id>`.

A busca por ISBN durante o empréstimo é local e não consulta Google Books, ISBNsearch ou Open Library.

## 11. Identificadores

### ISBN

É o identificador bibliográfico da obra. Pode ser vazio, é armazenado no campo `isbn` e não substitui o identificador interno.

### ID próprio

É o identificador principal do livro no sistema. É gerado pelo backend com `new_id()` e corresponde à chave primária da tabela `livros`.

### QR Code

Os QR Codes internos são gerados a partir do ID próprio do livro ou de um identificador de exemplar.

Os exemplares usam códigos no formato aproximado:

```text
EXEMPLAR-<id-do-livro>-EX-<codigo>-<id-do-exemplar>
```

O QR Code é usado para localizar livros, exemplares, alunos e cartões administrativos. O ISBN não é o identificador principal dos QR Codes gerados pelo sistema.

## 12. Outras APIs, bibliotecas e endpoints relacionados

Foram encontrados os seguintes elementos relacionados à leitura ou resolução de códigos:

- `/api/qr/decode`: decodifica imagem e tenta resolver o código como livro, ISBN, exemplar ou aluno;
- `/api/qr/start`, `/api/qr/stop` e `/api/qr/result`: endpoints de scanner no backend;
- `jsQR`: biblioteca carregada por CDN para leitura de QR Code;
- `BarcodeDetector`: API do navegador para códigos de barras;
- OpenCV e Pyzbar: bibliotecas backend usadas no fallback de leitura.

Nenhuma outra API bibliográfica ou endpoint específico de consulta de ISBN foi encontrado.

## 13. Informações não encontradas

- Não existe validação do dígito verificador do ISBN.
- Não existe teste automatizado específico para `/api/books/isbn-lookup`.
- Não existe teste automatizado das respostas das três fontes externas.
- Não existe retry com backoff específico para a consulta de ISBN.
- Não existe tratamento frontend que identifique qual provedor falhou.
- `genero_nome` retornado pelo backend não é usado para preencher o formulário.
- `categorias` não são colocadas em um campo do formulário.
- A busca de livros do empréstimo não consulta automaticamente as fontes externas.
- Os endpoints de câmera do servidor não são usados pelo fluxo principal de cadastro por ISBN; o cadastro usa a câmera do navegador e o fallback `/api/qr/decode`.
