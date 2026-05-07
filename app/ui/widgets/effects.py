"""Helpers de efeitos visuais reutilizáveis (drop-shadow etc.)."""
from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QWidget

from app.ui.tokens import Color


def apply_drop_shadow(
    widget: QWidget,
    blur: int = 20,
    offset_y: int = 4,
    alpha: int = 90,
) -> QGraphicsDropShadowEffect:
    """Aplica sombra suave abaixo do widget. Retorna o efeito.

    Usa cor preta com alpha variável; funciona bem em dark e light.
    """
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(0, offset_y)
    color = QColor(0, 0, 0)
    color.setAlpha(alpha)
    effect.setColor(color)
    widget.setGraphicsEffect(effect)
    return effect


def apply_glow(
    widget: QWidget,
    color_hex: str | None = None,
    blur: int = 28,
    alpha: int = 110,
) -> QGraphicsDropShadowEffect:
    """Aplica glow centrado (drop-shadow sem offset, na cor accent)."""
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(0, 0)
    base = color_hex or Color.ACCENT
    qcolor = QColor(base)
    qcolor.setAlpha(alpha)
    effect.setColor(qcolor)
    widget.setGraphicsEffect(effect)
    return effect
