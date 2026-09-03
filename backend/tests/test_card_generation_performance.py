import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scanner.routes import _build_card


def test_build_card_is_fast_enough_for_repeated_use():
    start = time.perf_counter()
    for i in range(20):
        image = _build_card(
            entity_type="aluno",
            title=f"Aluno Teste {i}",
            subtitle="Turma: INFO3A",
            field1="Sala: Sala 1",
            field2="Carteirinha: 2024001",
            field3="ID: 12345678",
            qr_data=f"ALUNO-QR-{i}",
            badge="INFO3A",
            color="#166534",
        )
        assert image.startswith("data:image/png;base64,")

    elapsed = time.perf_counter() - start
    assert elapsed < 1.5, f"Geração da carteirinha ficou lenta: {elapsed:.3f}s para 20 cartões"
