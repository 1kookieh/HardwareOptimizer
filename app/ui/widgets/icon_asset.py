"""Helpers para ícones locais usados na UI PySide6."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel

from app.ui.tokens import Color


ICON_ROOT = Path(__file__).resolve().parents[1] / "assets" / "icons"


def load_icon_pixmap(name: str, size: int = 32) -> QPixmap | None:
    """Carrega um ícone SVG/PNG local e retorna pixmap escalado."""
    for suffix in (".svg", ".png", ".jpg", ".jpeg"):
        candidate = ICON_ROOT / f"{name}{suffix}"
        if not candidate.exists():
            continue
        pixmap = QPixmap(str(candidate))
        if pixmap.isNull():
            continue
        return pixmap.scaled(QSize(size, size), Qt.KeepAspectRatio, Qt.SmoothTransformation)
    return None


class AssetIcon(QLabel):
    """Label com pixmap local e fallback textual simples."""

    def __init__(self, name: str, fallback: str = "•", size: int = 28, parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(
            f"background:transparent;border:none;color:{Color.ACCENT};"
            f"font-size:{max(11, size // 2)}px;font-weight:900;"
        )
        pixmap = load_icon_pixmap(name, size)
        if pixmap is None:
            self.setText(fallback)
        else:
            self.setPixmap(pixmap)
