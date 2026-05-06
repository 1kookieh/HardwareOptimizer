"""Regressão de encoding: garante que nenhum literal PT-BR em ``app/`` ou
``tests/`` contenha sequências mojibake (UTF-8 duplo-codificado).

A presença de ``\\xc3\\x83`` em bytes UTF-8 representa o caractere
U+00C3 (a letra A maiúscula com til), indicador clássico de mojibake
em texto PT-BR (não aparece em escrita correta). Bytes ``\\xc2``
isolados são UTF-8 válido e não são checados aqui.
"""
from __future__ import annotations

from pathlib import Path

import pytest

ROOTS = (Path("app"), Path("tests"))
SUSPECT_BYTES = b"\xc3\x83"  # U+00C3 em UTF-8 — sinal de mojibake em PT-BR


def _python_files() -> list[Path]:
    files: list[Path] = []
    for root in ROOTS:
        if root.exists():
            files.extend(root.rglob("*.py"))
    return files


@pytest.mark.parametrize("path", _python_files(), ids=lambda p: str(p))
def test_no_mojibake_sequences(path: Path) -> None:
    raw = path.read_bytes()
    count = raw.count(SUSPECT_BYTES)
    assert count == 0, (
        f"{path}: {count} sequência(s) mojibake (b'\\xc3\\x83') encontrada(s). "
        f"Rode `py scripts/fix_mojibake.py app tests` para corrigir."
    )
