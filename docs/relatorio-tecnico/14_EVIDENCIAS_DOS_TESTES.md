# 14 — Evidências dos testes

## Comandos

### Python

`pytest` foi executado duas vezes a partir da raiz usando `.venv312/bin/python`. Um wrapper
temporário substituiu `dotenv.load_dotenv` apenas quando o argumento era o caminho
absoluto do `backend/.env` do workspace. Caminhos temporários usados pelo próprio
teste `test_env_loading.py` continuaram delegando para a implementação original.
Assim, a suíte não leu o arquivo real.

Resultados do runner: primeira execução `12 failed, 180 passed, 1 warning in
6.01s`; repetição `12 failed, 180 passed, 1 warning in 2.89s`.

### JavaScript

`node --test frontend/tests/*.test.js`

Resultado em ambas as execuções: 7 tests, 7 pass, 0 fail, 0 skipped. Duração:
aproximadamente 1,53 s e 1,22 s. Arquivos cobertos pelo runner: `api-retry`, `books-isbn`, `catalog-crud`,
`modal-interaction`, `navigation`, `qr-scanner`, `reports`.

## Evidência sanitizada das falhas

- Groq Vision: erro explícito de configuração ausente, antes da requisição/mocks.
- Oito rotas: status observado `503 SERVICE UNAVAILABLE`, incompatível com o
  status de sucesso esperado nos testes.
- Nenhuma chave, conteúdo de ambiente ou dado real de aluno foi registrado neste
  documento.

## Estado do workspace

Após os testes, `git status --short` não indicou artefatos adicionais dos runners.
Na segunda etapa, `compileall` executou; arquivos de bytecode são ignorados pelo
Git. As alterações visíveis pertencem à documentação/auditoria e ao exemplo
`.env.example`; nenhuma operação de escrita foi executada no banco.

Não foi guardado o log bruto: ele contém rastros internos de teste e não é
necessário para reproduzir o resumo. Comandos e falhas estão identificados nos
relatórios 12 e 13.
