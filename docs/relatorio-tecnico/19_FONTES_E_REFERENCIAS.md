# 19 — Fontes e referências

Consulta realizada em 30/10/2026. A versão do pacote no workspace pode diferir
da versão atualmente publicada na documentação online.

## APIs e serviços

| Tecnologia | Informação consultada | Fonte oficial |
|---|---|---|
| Google Books API | Busca de volumes e autenticação por API key/OAuth | [Using the API](https://developers.google.com/books/docs/v1/using) |
| Open Library | Formatos, uso, rate limits e APIs | [Developer API](https://openlibrary.org/developers/api) |
| Groq | Compatibilidade de clientes OpenAI e base URL | [OpenAI compatibility](https://console.groq.com/docs/openai) |
| OpenAI Vision | Entrada de imagem e Chat Completions/Responses | [Images and vision](https://developers.openai.com/api/docs/guides/images-vision) |
| ISBNdb | Endpoint identificado no código; documentação oficial não carregou (HTTP 403 nesta consulta) | [API docs](https://isbndb.com/apidocs/v2) |
| ISBNsearch | Página pública consultada; não foi localizada documentação oficial de API | [ISBN Search](https://isbnsearch.org/) |
| Supabase Python | Inicialização, leitura/escrita e filtros | [Python reference](https://supabase.com/docs/reference/python/introduction) |
| Render | URL/uso são evidenciados por README/workflow do repositório; nenhum console remoto acessado | [Site](https://render.com/) |

## Bibliotecas Python

| Pacote | Fonte oficial consultada |
|---|---|
| Flask 3.0.3 | [Documentação Flask](https://flask.palletsprojects.com/en/stable/) |
| Flask-Cors 4.0.1 | [Documentação Flask-CORS](https://flask-cors.readthedocs.io/en/latest/) |
| python-dotenv 1.0.1 | [PyPI 1.0.1](https://pypi.org/project/python-dotenv/1.0.1/) |
| qrcode 7.4.2 | [Repositório python-qrcode](https://github.com/lincolnloop/python-qrcode) |
| Pillow | [Documentação Pillow](https://pillow.readthedocs.io/en/stable/) |
| OpenCV | [Documentação OpenCV 4.x](https://docs.opencv.org/4.x/) |
| pyzbar 0.1.9 | [Repositório pyzbar](https://github.com/NaturalHistoryMuseum/pyzbar) |
| NumPy | [Documentação NumPy](https://numpy.org/doc/stable/) |
| Supabase Python 2.31.0 | [Python reference](https://supabase.com/docs/reference/python/introduction) |
| openai | [SDK Python](https://github.com/openai/openai-python) |
| groq | [SDK Python](https://github.com/groq/groq-python) |
| Gunicorn 22.0.0 | [Documentação](https://gunicorn.org/) |
| Passlib 1.7.4 | [Documentação](https://passlib.readthedocs.io/en/stable/) |
| bcrypt 5.0.0 | [Projeto pyca/bcrypt](https://github.com/pyca/bcrypt) |

## Frontend e ferramentas

| Tecnologia | Fonte oficial consultada |
|---|---|
| Chart.js 4.4.4 | [Documentação](https://www.chartjs.org/docs/latest/) |
| jsQR 1.4.0 | [Repositório jsQR](https://github.com/cozmo/jsQR) |
| Tabler Icons | [Catálogo/documentação](https://tabler.io/icons) |
| Node test runner | [node:test](https://nodejs.org/api/test.html) |
| GitHub Actions | [Documentação](https://docs.github.com/actions) |

## Limitações das fontes

- As páginas oficiais podem documentar versões mais recentes que as fixadas no
  projeto; a tabela de versões locais está em 06.
- ISBNdb retornou bloqueio HTTP 403 ao tentar consultar a documentação; não se
  afirma ter validado seus detalhes de autenticação com a documentação.
- ISBNsearch é consumido via HTML scraping no código; não foi comprovado contrato
  de API.
- Não se consultou página de CVEs/vulnerabilidades e nenhuma vulnerabilidade de
  pacote é declarada neste relatório.
