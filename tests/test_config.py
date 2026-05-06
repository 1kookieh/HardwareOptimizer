"""Garante que ``app.config`` expõe constantes públicas estáveis."""
from __future__ import annotations

from app import config


def test_config_exposes_expected_constants() -> None:
    expected = {
        "XMP_HEURISTIC_MHZ": int,
        "RAM_COMFORTABLE_GB": (int, float),
        "OUTDATED_DRIVER_DAYS": int,
        "STALE_HOTFIX_DAYS": int,
        "OUTDATED_DRIVERS_REPORT_LIMIT": int,
        "DISK_USAGE_HIGH_RATIO": float,
        "ONLINE_SOURCE_TIMEOUT_SECONDS": int,
        "POWERSHELL_TIMEOUT_DEFAULT": int,
        "POWERSHELL_TIMEOUT_HOTFIX": int,
        "POWERSHELL_TIMEOUT_DRIVERS": int,
        "POWERSHELL_TIMEOUT_WINDOWS_UPDATE": int,
    }
    for name, types in expected.items():
        assert hasattr(config, name), f"app.config sem {name}"
        assert isinstance(getattr(config, name), types), name


def test_thresholds_have_sane_values() -> None:
    assert config.XMP_HEURISTIC_MHZ >= 2400
    assert config.RAM_COMFORTABLE_GB >= 8
    assert 0 < config.DISK_USAGE_HIGH_RATIO <= 1
    assert config.OUTDATED_DRIVER_DAYS >= 365
    assert config.STALE_HOTFIX_DAYS >= 30
