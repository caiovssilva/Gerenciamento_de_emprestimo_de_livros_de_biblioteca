# 11 — Qualidade e dependências

## Verificações executadas

| Verificação | Comando/ferramenta | Resultado |
|---|---|---|
| Sintaxe Python | `.venv312/bin/python -m compileall -q backend` | PASSOU |
| Sintaxe JavaScript | `node --check` nos scripts em `frontend/assets/js/`, `pages/`, `lib/` | PASSOU |
| Testes Python | pytest 9.1.1 em `.venv312` | 180 pass, 12 fail, 1 warning |
| Testes Node | `node --test frontend/tests/*.test.js` | 7 pass, 0 fail |
| Diff whitespace | `git diff --check` | PASSOU |

## Manifestos e dependências

`backend/requirements.txt` declara Flask, Flask-Cors, python-dotenv, qrcode,
Pillow, OpenCV, pyzbar, NumPy, Supabase, Groq, OpenAI, Gunicorn, Passlib e bcrypt.
`pytest` não está nesse manifesto. `requirements.txt` raiz inclui a lista do
backend. `package-lock.json` possui `packages: {}` e não há `package.json`.

Várias versões estão fixadas, mas `groq` e `openai` não têm versão declarada e
não há lock de dependências Python. `pip show` foi consultado para algumas
versões instaladas; isso não é análise da árvore inteira.

## Não executado

Lint, formatter, build frontend, análise estática tipada, auditoria CVE/SCA,
compatibilidade em múltiplos ambientes, prova de imports não usados. Nenhuma
dependência foi instalada ou atualizada nesta etapa.
