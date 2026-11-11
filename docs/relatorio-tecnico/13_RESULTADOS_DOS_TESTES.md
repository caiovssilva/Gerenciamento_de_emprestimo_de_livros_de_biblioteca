# 13 — Resultados dos testes

Executado duas vezes em 30/10/2026 no workspace atual (execuções anteriores e
repetição da segunda etapa tiveram o mesmo resultado).

## Resumo

| Suíte | Comando/ferramenta | Executados | Passaram | Falharam | Observação |
|---|---|---:|---:|---:|---|
| Python backend | pytest 9.1.1 em `.venv312` | 192 | 180 | 12 | 1 warning; repetição: 2,89 s |
| JavaScript frontend | Node `node --test` | 7 | 7 | 0 | Repetição: sem skipped/cancelled; 1,22 s |
| **Total** |  | **199** | **187** | **12** | Não inclui cenários manuais bloqueados |

## Falhas pytest por teste

1. `test_isbn_lookup.py`: `test_groq_vision_extracts_and_normalizes_isbn`
2. `test_isbn_lookup.py`: `test_groq_vision_returns_empty_when_image_has_no_isbn`
3. `test_isbn_lookup.py`: `test_groq_vision_reports_auth_error`
4. `test_isbn_lookup.py`: `test_groq_vision_rejects_invalid_isbn`
5. `test_qr_id_resolution.py`: `test_get_book_and_student_by_id`
6. `test_qr_id_resolution.py`: `test_qr_decode_resolves_student_by_id`
7. `test_reports_data.py`: `test_report_data_and_csv_remove_duplicate_records`
8. `test_reports_data.py`: `test_student_directory_export_includes_students_without_loans_and_room_details`
9. `test_reports_student_status.py`: `test_student_status_export_includes_borrowed_owing_and_returned`
10. `test_self_service_auth.py`: `test_self_service_card_lookup_normalizes_input_and_false_librarian_flag`
11. `test_self_service_auth.py`: `test_self_service_card_lookup_tolerates_card_formatting`
12. `test_unique_identifiers.py`: `test_create_book_generates_distinct_ids_and_qr_codes_for_same_title`

## Interpretação baseada na evidência

- Os quatro testes de visão encerraram em “Groq Vision não configurado” antes de
  usar o mock de cliente. O código consulta a variável de chave antes da chamada;
  os testes citados não a definem. A falha evidencia um mock incompleto, não um
  resultado de chamada real.
- Os oito testes de rotas observaram 503 onde esperavam sucesso. O middleware
  `require_database_for_api` faz consulta prévia a `livros`; os casos não
  estabeleceram um Supabase disponível/mock no ponto de entrada. Portanto, os
  comportamentos de negócio desses casos não foram alcançados. Não classificar
  esses endpoints como aprovados.
- Essa causa é uma explicação sustentada pelo middleware e pelo status observado,
  mas os oito testes não foram reescritos para isolar o gate; os endpoints não
  receberam validação funcional neste resultado.
- Os 180 restantes passaram dentro do conjunto e ambiente acima.
- O frontend executou sete testes e todos passaram.

## Limites

O teste foi isolado; não carregou o `.env` real e não conectou Supabase nem
provedores. O output foi resumido sem incluir segredos. Cobertura de código não
foi medida. Detalhes metodológicos estão em [14 — Evidências](14_EVIDENCIAS_DOS_TESTES.md).
