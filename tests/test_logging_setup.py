"""Garante que setup_logging cria log file rotativo e get_logger devolve
logger filho do logger raiz."""
from __future__ import annotations

import logging
from pathlib import Path

import pytest


@pytest.fixture
def isolated_log_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    # Reseta flag de configuração para permitir reconfigurar no teste
    import app.logging_setup as ls

    monkeypatch.setattr(ls, "_configured", False)
    # Limpa handlers prévios do logger raiz do app
    root = logging.getLogger("hardware_optimizer")
    for h in list(root.handlers):
        root.removeHandler(h)
    return tmp_path


def test_setup_creates_log_file(isolated_log_dir: Path) -> None:
    from app.logging_setup import get_logger, setup_logging

    setup_logging()
    log = get_logger("test")
    log.info("hello world")

    expected = isolated_log_dir / "HardwareOptimizer" / "logs" / "app.log"
    assert expected.exists()
    content = expected.read_text(encoding="utf-8")
    assert "hello world" in content
    assert "INFO" in content


def test_get_logger_is_child_of_root(isolated_log_dir: Path) -> None:
    from app.logging_setup import get_logger, setup_logging

    setup_logging()
    log = get_logger("foo")
    assert log.name == "hardware_optimizer.foo"


def test_setup_idempotent(isolated_log_dir: Path) -> None:
    from app.logging_setup import setup_logging

    log1 = setup_logging()
    handlers_before = len(log1.handlers)
    log2 = setup_logging()
    handlers_after = len(log2.handlers)
    assert handlers_before == handlers_after
