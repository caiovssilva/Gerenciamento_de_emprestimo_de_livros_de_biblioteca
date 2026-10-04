# Relatorio atual do projeto - atualizado em 04/10/2026

## Registro de atualizacao

**Data e hora:** domingo, 04/10/2026, 20:59:52 UTC.

**Branch/revisao:** `fix/login-error-message` / `71eab32`.

Este registro atualiza fatos verificados nesta data. As secoes seguintes preservam o snapshot de 02/10/2026 e nao foram todas retestadas em 04/10. Quando houver divergencia, este registro e as secoes de testes e Vision abaixo prevalecem. Nenhuma chave ou valor de Secret foi registrado.

- `backend/.env` nao e necessario no Codespace: `load_environment()` usa `override=False`, preserva variaveis injetadas pelo ambiente e aceita `.env` como fallback. O teste correspondente passou com arquivo temporario e valores ficticios.
- Testes atuais: backend ISBN/Vision `25 passed`; frontend `books ISBN form test passed` e `qr-scanner callback test passed`; backend completo `32 passed, 6 failed, 3 warnings`.
- As seis falhas do backend completo estao em quatro testes de login e dois de reconexao do Supabase. O teste antigo que exigia `backend/.env` foi adaptado e passou.
- Uma chamada real isolada ao Groq Vision em 04/10 reconheceu `9788532511010` em um frame sintetico criado em memoria. Isso nao comprova leitura pela camera fisica.
- O navegador reportou limite de chamadas do Groq; uma chamada Vision isolada posterior funcionou. O scanner agora consulta a cada 5 segundos e aplica espera crescente apos erros. A leitura local continua disponivel.
- Os endpoints POST de QR decode e ISBN Vision existem no codigo atual. Antes de iniciar o Flask local, a porta 5000 recusou conexao; depois do inicio, ambos responderam `400` a payload invalido, nao `404`. Uma sondagem sem sessao da URL publica do Codespace respondeu `401`; a origem exata dos `404` do navegador nao foi confirmada.
- Em consulta real registrada em 02/10, o ISBN `9788532511010` nos modos manual e scanner respondeu HTTP 200 e retornou o mesmo titulo e autor. No modo scanner, os dados podem combinar Groq e fontes bibliograficas; nao e possivel atribuir cada campo exclusivamente ao Groq.

## 1. Resumo executivo

Em 04/10/2026, os testes focados de ISBN/Vision passaram, assim como os dois testes frontend disponiveis. Uma chamada isolada ao Groq Vision reconheceu o ISBN de um frame sintetico; isso nao comprova leitura com webcam real. A suite backend completa teve 32 aprovados, 6 falhas e 3 avisos; as falhas estao em testes de login e reconexao do Supabase.

O navegador havia reportado excesso de chamadas ao Groq. O scanner foi ajustado para aguardar 5 segundos entre requisicoes Vision e usar espera crescente apos falhas. O estado da camera fisica e da URL publica do Codespace permanece nao confirmado.

## 2. Estado atual do ambiente

- Branch: `fix/login-error-message`
- Revisao de referencia desta atualizacao: `71eab32`.
- O Flask foi iniciado na porta 5000 durante a verificacao; os endpoints locais foram testados depois da inicializacao.
- O valor do Secret nao foi lido nem incluido neste relatorio. Uma chamada real ao endpoint de chat do Groq respondeu HTTP 200 em verificacao registrada em 02/10; isso confirma a chamada textual naquele momento, nao todas as capacidades da conta.
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

A camera captura frames automaticamente, sem botao de foto e sem seletor de galeria. O intervalo configurado entre chamadas Vision e de 5 segundos. As chamadas sao sequenciais; depois de erros, ha espera crescente para reduzir chamadas repetidas e respeitar limites do provedor. A leitura local continua enquanto Vision aguarda.

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

Em 04/10, uma chamada real isolada ao Groq Vision recebeu um frame sintetico com `9788532511010` e retornou o ISBN normalizado. Isso confirma uma chamada funcional naquele momento, mas nao testa a webcam real nem a leitura continua no navegador.

O navegador havia reportado HTTP 502 com mensagem de limite de chamadas. Uma chamada isolada posterior foi bem-sucedida. O scanner passou a usar intervalo de 5 segundos e backoff crescente apos falhas.

Teste anterior com resposta simulada, sem ISBN na imagem:

```json
{
  "encontrado": false,
  "isbn": ""
}
```

Um teste anterior com imagem 1x1 retornou erro porque o Groq exige pelo menos 32x32 pixels. Isso nao era falha do modelo.

Os leitores locais do navegador permanecem disponiveis. As tentativas Vision nao sao encerradas permanentemente na primeira falha.

## 8. Leitura local de codigo de barras

O scanner existente continua usando:

- `jsQR` para QR Code;
- `BarcodeDetector` do navegador para formatos como EAN-13;
- endpoint `/api/qr/decode` como fallback;
- OpenCV, NumPy, pyzbar e Pillow no backend.

O ambiente virtual `.venv312` possui os pacotes Python necessarios. O pyzbar tambem precisa da biblioteca nativa `zbar` (`libzbar0`). A instalacao via `apt-get` foi tentada, mas o usuario atual nao tem permissao para modificar o sistema.

Com isso, BarcodeDetector do navegador pode funcionar, mas o fallback backend de EAN depende do `libzbar0`.

### Verificacao dos endpoints 404 em 04/10

O codigo atual registra `POST /api/qr/decode` e `POST /api/books/isbn-vision`. Antes de iniciar o Flask local, uma conexao na porta 5000 foi recusada. Depois da inicializacao, os dois endpoints responderam `400` a payloads deliberadamente invalidos, demonstrando que o processo local reconheceu as rotas. A sondagem da URL publica do Codespace sem sessao retornou `401`; nao foi possivel confirmar se o host publicado servia a mesma revisao nem determinar a origem exata dos `404` vistos no navegador.

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
25 passed (04/10/2026)
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
32 passed, 6 failed, 3 warnings (04/10/2026)
```

As 6 falhas da execucao de 04/10 sao:

1. quatro testes de autenticacao falham com os clientes simulados usados por esses testes;
2. dois testes de reconexao esperam atributos offline que nao existem no cliente Supabase atual.

O teste `test_env_loading.py`, que antes exigia o arquivo real `backend/.env`, foi atualizado para testar Secrets e fallback dotenv sem valores reais e passou.

Avisos observados:

- deprecacao do modulo Python `crypt`;
- parametros `timeout` e `verify` depreciados no cliente Supabase.

## 11. Arquivos relacionados as alteracoes

- `backend/api/books.py`: modelos Groq separados, Groq Vision, endpoint Vision, composicao de resultados, prioridade, paralelizacao e desempenho ISBN.
- `backend/app.py`: prioridade para Secrets ja presentes no ambiente (`override=False`) e isencao das rotas ISBN da verificacao previa desnecessaria do Supabase.
- `backend/.env.example`: documentacao de `GROQ_VISION_MODEL`.
- `backend/tests/test_isbn_lookup.py`: testes de prioridade, Vision, normalizacao, erros de autenticacao e origem manual/scanner.
- `frontend/assets/js/api.js`: chamada do endpoint Vision.
- `frontend/assets/js/pages/books.js`: integracao no Cadastro de Livro, intervalo Vision de 5 segundos e backoff crescente apos erros/limites.
- `frontend/assets/js/qr-scanner.js`: callback opcional de frames e cancelamento.

As demais telas e funcionalidades nao foram alteradas intencionalmente.

## 12. Pendencias recomendadas

1. Garantir que a conta Groq tenha um modelo Vision habilitado e manter `GROQ_VISION_MODEL` com o ID correto.
2. Instalar `libzbar0` no ambiente para habilitar o fallback backend de codigo de barras.
3. Atualizar os testes antigos de autenticacao, ambiente e reconexao.
4. Definir ou redefinir a senha do usuario `admin` somente se isso for autorizado, pois nenhuma senha foi alterada durante este trabalho.

## Conclusao

Em 04/10, os testes focados de ISBN/Vision e os dois testes frontend passaram; a suite backend completa ainda teve seis falhas descritas acima. Uma chamada isolada real ao Groq Vision reconheceu ISBN em frame sintetico, mas a camera fisica nao foi testada. O fallback backend de barcode depende da biblioteca nativa `zbar`. A origem dos `404` vistos na URL publica permanece nao confirmada: o codigo local tem as rotas, e o Flask iniciado respondeu `400` aos payloads de teste invalidos.
