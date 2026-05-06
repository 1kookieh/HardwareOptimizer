"""Testes do coletor.

Os testes rápidos (default) usam mocks para PowerShell, WMI, HTTP e
``winreg``. O caminho real é exercitado apenas pelos testes marcados
com ``integration``, executados sob demanda com ``pytest -m integration``.
"""
from __future__ import annotations

import subprocess
import sys

import pytest

from app.collectors import collect_full_scan
from app.models.hardware import FullScan


# --------- testes rápidos (mocks) ---------

class _FakeCompletedProcess:
    def __init__(self, stdout: str = "", stderr: str = "", returncode: int = 0) -> None:
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


@pytest.fixture
def isolated_collectors(monkeypatch: pytest.MonkeyPatch) -> None:
    """Bloqueia I/O real (subprocess, HTTP, winreg, WMI) durante a coleta."""
    monkeypatch.setattr(
        subprocess, "run",
        lambda *a, **kw: _FakeCompletedProcess(stdout="", stderr="", returncode=0),
    )

    # urllib.request.urlopen — bloqueia HTTP
    def _no_http(*_a, **_kw):
        raise RuntimeError("rede bloqueada no teste")

    monkeypatch.setattr("app.collectors.updates.urlopen", _no_http)

    # winreg pode não existir fora do Windows; só substitui se importável
    try:
        import winreg  # type: ignore  # noqa: F401

        def _missing_key(*_a, **_kw):
            raise FileNotFoundError("winreg mockado")

        monkeypatch.setattr("winreg.OpenKey", _missing_key)
    except ImportError:
        pass

    # wmi — substitui import dentro de cada coletor
    class _FakeWMI:
        def __init__(self, *_a, **_kw): ...
        def Win32_Processor(self): return []
        def Win32_VideoController(self): return []
        def Win32_BaseBoard(self): return []
        def Win32_PhysicalMemory(self): return []
        def Win32_BIOS(self): return []
        def Win32_IDEController(self): return []

    fake_wmi_module = type(sys)("wmi")
    fake_wmi_module.WMI = _FakeWMI  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "wmi", fake_wmi_module)


def test_collect_returns_fullscan_quickly(isolated_collectors) -> None:
    scan = collect_full_scan()
    assert isinstance(scan, FullScan)
    assert scan.collected_at
    assert scan.system.os_name


def test_collect_emits_collection_errors_list(isolated_collectors) -> None:
    scan = collect_full_scan()
    assert isinstance(scan.collection_errors, list)


def test_collect_progress_callback_invoked(isolated_collectors) -> None:
    seen: list[str] = []
    scan = collect_full_scan(on_stage=lambda label, _pct: seen.append(label))
    assert isinstance(scan, FullScan)
    assert "Sistema" in seen
    assert "Finalizando" in seen


# --------- teste de integração real (opt-in) ---------

@pytest.mark.integration
def test_collect_real_system() -> None:
    """Toca WMI, PowerShell, registro e HTTP reais. Lento (~30–60s)."""
    scan = collect_full_scan()
    assert isinstance(scan, FullScan)
    assert scan.collected_at
