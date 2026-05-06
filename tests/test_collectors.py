from app.collectors import collect_full_scan
from app.models.hardware import FullScan


def test_collect_returns_fullscan():
    scan = collect_full_scan()
    assert isinstance(scan, FullScan)
    assert scan.collected_at
    assert scan.system.os_name


def test_collect_does_not_raise_on_missing_wmi(monkeypatch):
    """Mesmo sem WMI/Windows, a coleta deve retornar um FullScan com avisos em collection_errors."""
    scan = collect_full_scan()
    assert isinstance(scan.collection_errors, list)
