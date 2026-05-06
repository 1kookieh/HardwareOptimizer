"""Chips coloridos para risco, prioridade e status.

Usados como QTableWidgetItem com background customizado e foreground
contrastante. Cada nível de risco/prioridade/status tem cor própria
extraída de DESIGN.md.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import QTableWidgetItem

from app.ui.tokens import Color


_RISK_PALETTE: dict[str, tuple[str, str, str]] = {
    # value: (label, bg, fg)
    "safe": ("seguro", Color.SUCCESS, "#052E16"),
    "review": ("revisar", Color.WARNING, "#451A03"),
    "risky": ("risco", Color.DANGER, "#FFFFFF"),
    "blocked": ("bloqueado", "#DC2626", Color.ON_PRIMARY),
}

_PRIORITY_PALETTE: dict[str, tuple[str, str, str]] = {
    "critical": ("crítica", "#DC2626", Color.ON_PRIMARY),
    "high": ("alta", Color.DANGER, "#FFFFFF"),
    "medium": ("média", Color.WARNING, "#451A03"),
    "low": ("baixa", Color.MUTED, Color.ON_SURFACE),
}

_STATUS_PALETTE: dict[str, tuple[str, str, str]] = {
    "pending": ("pendente", Color.SURFACE_ELEVATED, Color.ON_SURFACE),
    "applied": ("aplicada", Color.SUCCESS, "#052E16"),
    "ignored": ("ignorada", Color.MUTED, Color.ON_SURFACE),
}

_CATEGORY_PALETTE: dict[str, tuple[str, str, str]] = {
    "bios": ("BIOS", Color.PROFILE_GAMING, Color.ON_PRIMARY),
    "windows": ("Windows", Color.ACCENT, Color.ON_ACCENT),
    "drivers": ("Drivers", Color.PROFILE_POWER, "#451A03"),
    "hardware": ("Hardware", Color.MUTED, Color.ON_SURFACE),
    "games": ("Jogos", Color.PROFILE_GAMING, Color.ON_PRIMARY),
    "energy": ("Energia", Color.PROFILE_POWER, "#451A03"),
    "security": ("Segurança", Color.SUCCESS, "#052E16"),
    "temperature": ("Temperatura", Color.DANGER, "#FFFFFF"),
}


def _make_chip(label: str, bg: str, fg: str) -> QTableWidgetItem:
    item = QTableWidgetItem(f"  {label}  ")
    item.setBackground(QBrush(QColor(bg)))
    item.setForeground(QBrush(QColor(fg)))
    item.setTextAlignment(Qt.AlignCenter)
    return item


def risk_chip(value: str) -> QTableWidgetItem:
    label, bg, fg = _RISK_PALETTE.get(value, (value, Color.MUTED, Color.ON_SURFACE))
    return _make_chip(label, bg, fg)


def priority_chip(value: str) -> QTableWidgetItem:
    label, bg, fg = _PRIORITY_PALETTE.get(value, (value, Color.MUTED, Color.ON_SURFACE))
    return _make_chip(label, bg, fg)


def status_chip(value: str) -> QTableWidgetItem:
    label, bg, fg = _STATUS_PALETTE.get(value, (value, Color.MUTED, Color.ON_SURFACE))
    return _make_chip(label, bg, fg)


def category_chip(value: str) -> QTableWidgetItem:
    label, bg, fg = _CATEGORY_PALETTE.get(value, (value, Color.MUTED, Color.ON_SURFACE))
    return _make_chip(label, bg, fg)
