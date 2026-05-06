"""Configuração centralizada de logging com rotação.

O app escreve logs em ``%LOCALAPPDATA%/HardwareOptimizer/logs/app.log``
(ou ``~/.local/share/HardwareOptimizer/logs`` fora do Windows). Mantém
até 5 arquivos rotacionados de 1 MB cada. O console recebe apenas WARN+
para não poluir o stdout durante uso normal.
"""
from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

_LOGGER_NAME = "hardware_optimizer"
_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_MAX_BYTES = 1_000_000
_BACKUP_COUNT = 5

_configured = False


def _log_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~/.local/share")
    folder = Path(base) / "HardwareOptimizer" / "logs"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configura root logger uma única vez. Retorna logger raiz do app."""
    global _configured
    logger = logging.getLogger(_LOGGER_NAME)
    if _configured:
        return logger

    logger.setLevel(level)
    logger.propagate = False

    formatter = logging.Formatter(_FORMAT)

    file_handler = RotatingFileHandler(
        _log_dir() / "app.log",
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console = logging.StreamHandler()
    console.setLevel(logging.WARNING)
    console.setFormatter(formatter)
    logger.addHandler(console)

    _configured = True
    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """Devolve um logger filho do logger raiz do app."""
    if name is None:
        return logging.getLogger(_LOGGER_NAME)
    return logging.getLogger(f"{_LOGGER_NAME}.{name}")
