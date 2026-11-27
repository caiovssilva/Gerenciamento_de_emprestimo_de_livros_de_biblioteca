# Relatorio: leitura de ISBN com Groq ou pyzbar

## Objetivo

Disponibilizar, no cadastro de livros, duas formas de ler o ISBN pela camera:

- **Groq Vision:** usa IA para analisar a imagem e extrair o ISBN.
- **Python (pyzbar):** decodifica o codigo de barras no backend Python, sem usar IA para a leitura.

A opcao OpenAI foi removida do seletor do cadastro. O suporte legado a OpenAI que existe no backend e nas dependencias nao foi removido nesta alteracao.

## O que mudou

- O seletor de leitura do cadastro agora oferece somente `Python (pyzbar)` e `Groq Vision`.
- A opcao escolhida e salva no navegador. Se houver um valor antigo ou invalido salvo, o sistema volta para Groq.
- O fluxo pyzbar envia os frames da camera para a rota de decodificacao Python ja existente.
- O ISBN lido e normalizado e so segue para a busca quando tem 10 ou 13 caracteres.
- Foi atualizado o teste do frontend para verificar o caminho pyzbar.

## Logica da leitura

### Python (pyzbar)

1. O scanner do navegador captura um frame da camera.
2. O frontend envia a imagem para `POST /api/qr/decode`.
3. O backend tenta decodificar o codigo com `pyzbar`. O processamento testa a imagem original e variacoes em tons de cinza, ampliadas e com contraste ajustado.
4. O frontend normaliza o valor retornado e verifica se ele tem tamanho de ISBN-10 ou ISBN-13.
5. Com o codigo lido, o formulario consulta os catalogos bibliograficos e preenche os dados encontrados. Esse passo nao chama Groq.

### Groq Vision

1. O scanner do navegador captura um frame da camera.
2. O frontend envia a imagem para `POST /api/books/isbn-vision`.
3. O backend pede ao Groq que identifique o ISBN na imagem.
4. Com o ISBN extraido, o backend consulta as fontes bibliograficas e devolve os dados para preencher o formulario.
5. Falhas temporarias e limites de chamadas do Groq sao tratados com novas tentativas e espera progressiva.

Em ambos os modos, ler o codigo e localizar os metadados sao etapas diferentes. O pyzbar decodifica o ISBN, mas a busca por titulo, autor e categorias continua dependendo das fontes bibliograficas configuradas.

## Dependencias e requisitos

- `pyzbar==0.1.9`, OpenCV e NumPy ja constavam em `backend/requirements.txt`; nenhuma dependencia Python nova foi adicionada para esta alteracao.
- Em Linux, o pyzbar tambem requer a biblioteca nativa `libzbar`. Ela estava presente no ambiente usado para iniciar o sistema.
- O modo pyzbar executa no backend: a imagem da camera e enviada do navegador ao servidor. Ele nao usa IA, mas ainda precisa que o backend esteja ativo.
- A consulta de metadados pode depender de conexao com os catalogos bibliograficos.

## Arquivos do fluxo

- `frontend/index.html`: opcoes apresentadas no cadastro.
- `frontend/assets/js/pages/books.js`: selecao do modo, leitura dos frames e preenchimento do formulario.
- `frontend/assets/js/api.js`: chamadas do frontend para as rotas de consulta e decodificacao.
- `backend/scanner/routes.py`: decodificacao das imagens no backend com pyzbar.
- `backend/api/books.py`: extracao do ISBN por Groq e consulta de metadados.
- `frontend/tests/books-isbn.test.js`: teste do fluxo de cadastro e leitura.

## Verificacao realizada

- Os testes JavaScript do frontend passaram; apos limitar o seletor a Groq e pyzbar, o teste focado de ISBN tambem passou.
- `git diff --check` passou sem apontar problemas de formatacao.
- Ao iniciar a aplicacao pelo ambiente virtual `.venv312`, o Flask subiu e o Supabase respondeu ao health check.
- Durante o uso da camera, as chamadas para `/api/qr/decode` retornaram HTTP 200. Tambem foram observadas respostas HTTP 429 em chamadas ao Groq, indicando limite temporario do provedor; o modo pyzbar evita essas chamadas de visao.
- A suite de testes backend nao foi executada nesta verificacao.

## Observacao de escopo

Esta alteracao removeu OpenAI das opcoes do cadastro, mas nao apagou o endpoint legado, a implementacao correspondente no backend nem a dependencia `openai`. Portanto, a interface do cadastro oferece somente Groq e pyzbar, embora ainda exista codigo de OpenAI fora desse seletor.