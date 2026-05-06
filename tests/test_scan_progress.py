"""Garante que ``collect_full_scan`` reporta progresso quando ``on_stage``
é fornecido e que mantém compatibilidade quando não é.

Os testes que disparam um scan real estão marcados como ``integration`` e
ficam fora do default (``pytest -m integration`` para rodá-los). O teste
de tolerância a exceção do callback usa mock para evitar I/O.
"""
from __future__ import annotations

import subprocess
import sys

import pytest

from app.collectors import collect_full_scan


@pytest.mark.integration
def test_collect_full_scan_without_callback_runs() -> None:
    scan = collect_full_scan()
    assert scan is not None
    assert scan.collected_at


@pytest.mark.integration
def test_collect_full_scan_emits_progress_stages() -> None:
    stages: list[tuple[str, int]] = []
    scan = collect_full_scan(on_stage=lambda label, pct: stages.append((label, pct)))
    assert scan is not None
    labels = [s for s, _ in stages]
    expected = [
        "Sistema",
        "Hardware",
        "BIOS / UEFI",
        "Atualizações locais",
        "Fontes oficiais online",
        "Finalizando",
    ]
    for stage in expected:
        assert stage in labels, f"stage {stage!r} ausente em {labels!r}"
    percents = [p for _, p in stages]
    assert percents == sorted(percents), "percent não é monotônico"
    assert all(0 <= p <= 100 for p in percents)


def test_collect_full_scan_tolerates_callback_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    # Bloqueia I/O para manter o teste rápido e determinístico
    monkeypatch.setattr(
        subprocess, "run",
        lambda *a, **kw: type("R", (), {"stdout": "", "stderr": "", "returncode": 0})(),
    )
    monkeypatch.setattr(
        "app.collectors.updates.urlopen",
        lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("rede bloqueada")),
    )
    fake_wmi = type(sys)("wmi")

    class _FakeWMI:
        def __init__(self, *a, **kw): ...
        def __getattr__(self, name): return lambda *a, **kw: []

    fake_wmi.WMI = _FakeWMI  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "wmi", fake_wmi)

    def boom(label: str, pct: int) -> None:
        raise RuntimeError("UI quebrou")

    scan = collect_full_scan(on_stage=boom)
    assert scan is not None
