# 📚 Biblioteca IFES — Campus Aracruz v3

## Novidades desta versão

| Funcionalidade | Descrição |
|---|---|
| **QR Code inteligente** | Ao escanear, o sistema identifica automaticamente se é livro ou aluno e busca as informações |
| **QR gerado no cadastro** | Ao criar livro ou aluno, o QR Code é gerado automaticamente e exibido |
| **Cartão imprimível** | Gera cartão PNG (livro) ou carteirinha (aluno) com QR Code para impressão |
| **Salas** | Crie salas físicas e associe alunos a elas |
| **Gêneros de livro** | Categorize o acervo por tipo (Comédia, Ficção, Técnico...) com cor e ícone |
| **Dashboard melhorado** | Mostra sala e gênero nas devoluções pendentes |

## Estrutura

```
biblioteca/
├── database.sql              ← Execute PRIMEIRO no Supabase
├── backend/
│   ├── app.py
│   ├── api/
│   │   ├── books.py          ← + genero_id + QR no POST
│   │   ├── students.py       ← + sala_id + QR no POST
│   │   ├── loans.py
│   │   ├── reports.py
│   │   ├── rooms.py          ← NOVO: CRUD de salas
│   │   └── genres.py         ← NOVO: CRUD de gêneros
│   ├── scanner/
│   │   └── routes.py         ← + resolve QR → tipo + cartão PNG
│   └── utils/
└── frontend/
    ├── index.html
    └── assets/js/
        ├── pages/
        │   ├── books.js      ← + filtro gênero, QR, impressão
        │   ├── students.js   ← + sala, QR, carteirinha
        │   ├── loans.js      ← + sala/gênero no dashboard
        │   ├── rooms.js      ← NOVO
        │   └── genres.js     ← NOVO
        └── qr-scanner.js     ← + resolve tipo automaticamente
```

## Início rápido

```bash
# 1. Supabase — cole database.sql no SQL Editor e clique Run

# 2. Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python app.py   # → http://localhost:5000

# 3. Frontend
cd frontend
python -m http.server 8080   # → http://localhost:8080
```

## Login
| Usuário | Senha |
|---|---|
| `admin` | `ifes2024` |
| `biblioteca` | `ifes2024` |

## Como funciona o QR Code

1. **Cadastrar livro/aluno** → QR Code é gerado automaticamente com o UUID do registro
2. **Escanear na tela de empréstimo** → câmera captura, backend decodifica e identifica se é livro ou aluno, preenche o campo automaticamente
3. **Botão QR** (🔲) na lista → exibe o QR Code com opção de baixar PNG
4. **Botão Imprimir** (🖨️) → abre nova aba com cartão profissional para impressão
