# Relatorio atual do projeto - 02/10/2026

## 1. Resumo executivo

O projeto esta funcionando com backend Flask, frontend servido pelo proprio backend e banco Supabase conectado. O fluxo de consulta de ISBN foi ampliado para diferenciar pesquisa manual e leitura pela camera.

O fluxo de ISBN isolado esta aprovado:

- Backend ISBN e Vision: 24 testes aprovados.
- Frontend do cadastro de livros: teste aprovado.
- Scanner frontend existente: teste aprovado.
- Banco: conectado.
- Groq: chave carregada e modelo Vision configurado.

A suite completa ainda possui 7 falhas em testes antigos ou dependentes da configuracao local. Elas nao estao relacionadas ao fluxo de consulta ISBN validado.

## 2. Estado atual do ambiente

- Branch: `fix/login-error-message`
- Revisao atual: `d9d64cf`
- Worktree: limpo, sem alteracoes pendentes no Git.
- Servidor Flask: ativo na porta 5000.
- URL local: `http://localhost:5000`
- Banco Supabase: conectado.
- `GROQ_API_KEY`: configurada por Codespace Secret.
- `GROQ_VISION_MODEL`: `qwen/qwen3.8-27b` por padrao.
- O arquivo `backend/.env` nao existe; a configuracao vem dos Secrets do Codespace.

O endpoint de saude retornou:

```json
{
  "database": "conectado",
  "status": "ok"
}
```

Nenhuma chave ou valor secreto foi incluido neste relatorio.

## 3. Consulta manual de ISBN

Quando o usuario digita um ISBN manualmente:

```text
Google Books + ISBNsearch + Open Library
```

O Groq nao e chamado nesse caminho. O endpoint continua sendo:

```text
GET /api/books/isbn-lookup?isbn=...&source=manual
```

A regra permanece implementada por:

```python
use_groq = source == "scanner"
```

## 4. Consulta de ISBN pela camera

Foi criado o fluxo de leitura continua no cadastro de livros:

```text
Camera -> frame temporario -> Groq Vision -> ISBN normalizado
      -> validacao -> APIs bibliograficas -> formulario preenchido
```

Foi criado o endpoint:

```text
POST /api/books/isbn-vision
```

O endpoint:

1. recebe o frame em base64;
2. envia a imagem para o Groq Vision;
3. extrai somente o ISBN;
4. normaliza e valida o ISBN;
5. chama Google Books, ISBNsearch e Open Library em paralelo;
6. retorna os dados para o cadastro.

Os frames nao sao salvos permanentemente.

A camera captura frames automaticamente, sem botao de foto e sem seletor de galeria. O intervalo inicial entre analises e de aproximadamente 1 segundo. Nao sao iniciadas requisicoes simultaneas: a proxima analise aguarda a anterior.

Ao encontrar um ISBN valido:

- novas analises sao interrompidas;
- a camera e encerrada;
- as tres APIs bibliograficas continuam a consulta;
- o cadastro e preenchido.

Ao cancelar:

- a camera e parada;
- o `AbortController` cancela a requisicao pendente quando possivel;
- os recursos temporarios sao liberados.

## 5. Prioridade dos dados bibliograficos

O Groq Vision e usado principalmente para:

```text
imagem -> ISBN
```

Ele nao tem prioridade sobre os dados bibliograficos.

Para titulo e autor:

1. consenso de duas ou mais APIs bibliograficas vence;
2. sem consenso, a prioridade e Google Books, ISBNsearch e Open Library;
3. o Groq so e usado como fallback quando nenhuma API fornece o campo.

Para categorias:

- categorias das APIs bibliograficas sao combinadas;
- duplicatas sao removidas;
- categorias do Groq so sao usadas se nenhuma API retornar categorias.

O caso do ISBN `9788532511010` foi corrigido: mesmo quando o Groq retornou `Araucaria`, o resultado final das fontes bibliograficas foi `Harry Potter e a Pedra Filosofal`.

## 6. Desempenho

Foi feita a paralelizacao do Groq com as tres APIs bibliograficas no modo scanner. Tambem foi removida a consulta desnecessaria ao Supabase no caminho normal de matching de genero, usando `generos.json` local.

Foi removida a verificacao previa do Supabase somente das rotas de consulta ISBN, pois elas nao precisam do banco para iniciar a busca.

Medicoes reais anteriores com o ISBN `978-8532511010`:

- Pesquisa manual: aproximadamente `0,421 s`.
- Pesquisa scanner: aproximadamente `0,507 s`.

Ambas ficaram abaixo de 1 segundo naquela execucao.

## 7. Groq Vision

Modelos separados:

```python
_GROQ_DEFAULT_MODEL = "allam-2-7b"
_GROQ_DEFAULT_VISION_MODEL = "qwen/qwen3.8-27b"
```

O modelo Vision pode ser substituido por Secret:

```text
GROQ_VISION_MODEL
```

As credenciais continuam somente no backend e aceitam as variaveis existentes:

```text
GROQ_API_KEY
API_GROQ
GROQ_API
```

Foi testado um frame valido de 100x100 pixels. Sem ISBN na imagem, o retorno foi corretamente:

```json
{
  "encontrado": false,
  "isbn": ""
}
```

Um teste anterior com imagem 1x1 retornou erro porque o Groq exige pelo menos 32x32 pixels. Isso nao era falha do modelo.

Quando o modelo Vision ficou temporariamente indisponivel, o sistema passou a interromper as tentativas repetidas e continuar com os leitores locais do navegador.

## 8. Leitura local de codigo de barras

O scanner existente continua usando:

- `jsQR` para QR Code;
- `BarcodeDetector` do navegador para formatos como EAN-13;
- endpoint `/api/qr/decode` como fallback;
- OpenCV, NumPy, pyzbar e Pillow no backend.

O ambiente virtual `.venv312` possui os pacotes Python necessarios. O pyzbar tambem precisa da biblioteca nativa `zbar` (`libzbar0`). A instalacao via `apt-get` foi tentada, mas o usuario atual nao tem permissao para modificar o sistema.

Com isso, BarcodeDetector do navegador pode funcionar, mas o fallback backend de EAN depende do `libzbar0`.

## 9. Autenticacao

O endpoint de login esta funcionando e alcançando o Supabase, mas o login de `admin` retornou `401` porque a senha `narceu2026` nao corresponde ao hash atual armazenado no banco.

Foi confirmado que:

- o usuario `admin` existe;
- existe hash PBKDF2 configurado;
- o banco esta acessivel;
- nao foi possivel recuperar a senha original;
- nenhum dado do banco foi alterado.

O SQL enviado pelo usuario define credenciais diferentes das encontradas no banco conectado. Como foi solicitado nao alterar o banco, o sistema continua exigindo a senha original atualmente registrada.

## 10. Testes executados

### Testes especificos de ISBN e Vision

```text
24 passed
```

Cobertura inclui:

- validacao ISBN-10 e ISBN-13;
- cache;
- fallback entre provedores;
- consenso e prioridade bibliografica;
- Groq manual nao chamado;
- Groq scanner chamado;
- mesmo ISBN normalizado enviado a todas as fontes;
- extracao Vision de ISBN;
- imagem sem ISBN;
- ISBN invalido vindo do Vision;
- endpoint `/api/books/isbn-vision`;
- fallback de campos e categorias.

### Testes frontend

```text
books ISBN form test passed
qr-scanner callback test passed
```

### Suite completa backend

Resultado no `.venv312`:

```text
30 passed, 7 failed, 3 warnings
```

As 7 falhas sao:

1. quatro testes de autenticacao dependem de mocks antigos e entram em conflito com a verificacao global atual do Supabase;
2. um teste exige `backend/.env`, mas o projeto usa Codespace Secrets;
3. dois testes de reconexao esperam a variavel interna `_offline`, que nao existe na implementacao atual.

Avisos observados:

- deprecacao do modulo Python `crypt`;
- parametros `timeout` e `verify` depreciados no cliente Supabase.

## 11. Arquivos relacionados as alteracoes

- `backend/api/books.py`: modelos Groq separados, Groq Vision, endpoint Vision, composicao de resultados, prioridade, paralelizacao e desempenho ISBN.
- `backend/app.py`: isencao das rotas ISBN da verificacao previa desnecessaria do Supabase.
- `backend/.env.example`: documentacao de `GROQ_VISION_MODEL`.
- `backend/tests/test_isbn_lookup.py`: testes de prioridade, Vision, normalizacao e origem manual/scanner.
- `frontend/assets/js/api.js`: chamada do endpoint Vision.
- `frontend/assets/js/pages/books.js`: integracao exclusiva no Cadastro de Livro.
- `frontend/assets/js/qr-scanner.js`: callback opcional de frames e cancelamento.

As demais telas e funcionalidades nao foram alteradas intencionalmente.

## 12. Pendencias recomendadas

1. Garantir que a conta Groq tenha um modelo Vision habilitado e manter `GROQ_VISION_MODEL` com o ID correto.
2. Instalar `libzbar0` no ambiente para habilitar o fallback backend de codigo de barras.
3. Atualizar os testes antigos de autenticacao, ambiente e reconexao.
4. Definir ou redefinir a senha do usuario `admin` somente se isso for autorizado, pois nenhuma senha foi alterada durante este trabalho.

## Conclusao

O projeto esta operacional para consulta ISBN, cadastro, frontend, Supabase e integracao Groq. O fluxo manual esta preservado sem Groq Vision. O fluxo da camera esta implementado de forma continua e restrita ao Cadastro de Livro, mas a qualidade final da leitura Vision depende do modelo habilitado na conta Groq e o fallback backend de barcode depende da biblioteca nativa `zbar`.
