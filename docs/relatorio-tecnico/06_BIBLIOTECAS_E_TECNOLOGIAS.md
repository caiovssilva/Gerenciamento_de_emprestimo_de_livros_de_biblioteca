# 06 — Bibliotecas e tecnologias

Versões declaradas vêm de `backend/requirements.txt`; versões “instaladas” são
apenas as encontradas no ambiente `.venv312` no dia da auditoria e não formam
lock de produção.

## Python declaradas

| Pacote | Declarado | Instalado no workspace | Uso confirmado |
|---|---:|---:|---|
| Flask | 3.0.3 | 3.0.3 | App, blueprints, request/response, sessão e test client |
| Flask-Cors | 4.0.1 | 4.0.1 | CORS `/api/*` |
| python-dotenv | 1.0.1 | 1.0.1 | `load_dotenv` para `backend/.env` |
| qrcode[pil] | 7.4.2 | 7.4.2 | Gera QR de registros e cartões |
| Pillow | `>=11.3.0` | 12.3.0 | Abre imagem de QR e gera cartões |
| opencv-python-headless | `>=4.10.0.84` | 4.10.0.84 | Processamento e leitura de imagem/câmera |
| pyzbar | 0.1.9 | 0.1.9 | Decodificação de códigos de barras/QR; requer libzbar do sistema |
| numpy | `>=2.1.0` | 2.5.3 | Converte imagem para arrays usados pelo OpenCV |
| supabase | 2.31.0 | 2.31.0 | Acesso a tabelas Supabase/PostgREST |
| groq | sem versão | 1.7.0 | Declarado, mas não há import/usagem direta confirmada |
| openai | sem versão | 3.19.0 | Cliente usado para OpenAI e interface compatível Groq |
| gunicorn | 22.0.0 | 22.0.0 | Servidor WSGI recomendado no README |
| passlib | 1.7.4 | 1.7.4 | `CryptContext` para validar/hash de senha |
| bcrypt | 5.0.0 | 5.0.0 | Verificação bcrypt alternativa |

`requirements.txt` na raiz inclui `backend/requirements.txt`. Não existe
`package.json`; o `package-lock.json` tem `packages: {}`. `pytest` está instalado
no ambiente, porém não aparece nos requirements. Não foi executada análise de
vulnerabilidades das dependências.

## JavaScript/CSS servidos por CDN

| Tecnologia | Versão da URL | Uso |
|---|---:|---|
| Chart.js | 4.4.4 | Gráficos em `charts.js` |
| jsQR | 1.4.0 | Leitura de QR no browser |
| Tabler Icons Webfont | 3.19.0 | Ícones CSS/HTML |
| Google Fonts Inter | URL sem versão fixa | Tipografia |
| `BarcodeDetector` | API nativa do navegador | Scanner quando suportado |

As versões remotas não são dependências npm bloqueadas. A disponibilidade e
integridade dos CDNs não foram testadas.

## Outras tecnologias

- **Python 3.14.2** e **Node.js 24.22.2** foram as versões reportadas no ambiente.
- **PostgreSQL** é a base indicada pelo SQL e pelo Supabase.
- **HTML/CSS/JavaScript vanilla** formam a interface, sem compilação confirmada.
- **GitHub Actions** executa workflows de manutenção.
- **Render** aparece em URL e instruções de deploy; o deploy foi inferido da
  configuração, não validado remotamente.

## Função e limitações por dependência

- **Flask:** servidor WSGI e roteamento; não implementa autorização de negócio por
  si só.
- **Flask-Cors:** adiciona cabeçalhos CORS; a configuração do projeto permite
  origem `*` em `/api/*`.
- **python-dotenv:** carrega pares chave/valor do arquivo indicado; não é cofre de
  segredos nem substitui Secret Manager.
- **qrcode:** cria QR; o conteúdo precisa ser tratado como dado público se impresso.
- **Pillow:** leitura/renderização de imagens; validação de conteúdo/tamanho deve
  ser feita pela aplicação.
- **OpenCV:** operações de visão, imagem e câmera; requer recursos nativos.
- **pyzbar:** integração Python com zbar; leitura pode faltar se `libzbar` não
  estiver instalada.
- **NumPy:** arrays e transformações numéricas para imagem.
- **supabase-py:** cliente PostgREST; não substitui política de acesso segura.
- **openai:** SDK de chat completions/imagem; recebe key e base URL configuráveis.
- **groq:** pacote declarado sem import direto; a integração observada usa
  `openai` com base URL Groq.
- **Passlib/bcrypt:** verificação de hashes; o código também preserva fallback
  legado de senha em texto.
- **Gunicorn:** servidor WSGI de produção; parâmetros de workers/timeouts não
  estão especificados no comando documentado.
- **Chart.js/jsQR/Tabler:** gráficos, leitura QR e ícones; carregados via CDN.

Criadores, versões precisas e links oficiais consultados estão em [19 — Fontes](19_FONTES_E_REFERENCIAS.md). Para dependências transitivas, o ambiente não
possui lock Python; a árvore transitiva completa não foi inventariada.
