# 13 — Evidências

## Testes repetidos nesta etapa

### Backend

Harness temporário executou `pytest.main(['-q', 'backend/tests'])` e substituiu
`dotenv.load_dotenv` apenas quando recebia o caminho absoluto do `backend/.env`
real, impedindo sua leitura. Não foi preservado um comando literal reutilizável
do harness; por isso, não se apresenta um snippet incompleto como se fosse
comando executado.

Saída da repetição: `12 failed, 180 passed, 1 warning in 2.89s`.

Falhas:

```text
test_isbn_lookup.py:
  test_groq_vision_extracts_and_normalizes_isbn
  test_groq_vision_returns_empty_when_image_has_no_isbn
  test_groq_vision_reports_auth_error
  test_groq_vision_rejects_invalid_isbn
test_qr_id_resolution.py:
  test_get_book_and_student_by_id
  test_qr_decode_resolves_student_by_id
test_reports_data.py:
  test_report_data_and_csv_remove_duplicate_records
  test_student_directory_export_includes_students_without_loans_and_room_details
test_reports_student_status.py:
  test_student_status_export_includes_borrowed_owing_and_returned
test_self_service_auth.py:
  test_self_service_card_lookup_normalizes_input_and_false_librarian_flag
  test_self_service_card_lookup_tolerates_card_formatting
test_unique_identifiers.py:
  test_create_book_generates_distinct_ids_and_qr_codes_for_same_title
```

Quatro casos Groq terminaram em configuração ausente antes do mock. Oito casos
HTTP receberam 503. O gate pré-requisição em `backend/app.py` torna essa
explicação plausível, mas os testes não foram repetidos com o gate isolado; a
lógica endpoint testada continua sem resultado.

### Frontend

Comando: `node --test frontend/tests/*.test.js`.

Saída: 7 tests, 7 pass, 0 fail, 0 skipped; 1,22 s na segunda execução.

### Sintaxe e whitespace

- `.venv312/bin/python -m compileall -q backend` → exit 0.
- `node --check` para scripts JS principais/pages/lib → exit 0.
- `git diff --check` → sem saída de erro.

## Não são evidências desta auditoria

Resultados HTTP de documentos de setembro/outubro anteriores, execução externa
de Groq/ISBN, medições antigas e status de serviço hospedado não foram
reproduzidos. Não houve log bruto persistido como artefato; os resultados acima
foram obtidos diretamente do runner.
