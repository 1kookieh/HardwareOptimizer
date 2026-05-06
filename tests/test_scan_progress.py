"""Garante que ``collect_full_scan`` reporta progresso quando ``on_stage``
é fornecido e que mantém compatibilidade quando não é."""
from __future__ import annotations

from app.collectors import collect_full_scan


def test_collect_full_scan_without_callback_runs() -> None:
    scan = collect_full_scan()
    assert scan is not None
    assert scan.collected_at


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


def test_collect_full_scan_tolerates_callback_exception() -> None:
    def boom(label: str, pct: int) -> None:
        raise RuntimeError("UI quebrou")

    scan = collect_full_scan(on_stage=boom)
    assert scan is not None
