"""Sidebar de navegação para a tela de resultados.

Lista vertical com itens (ícone + label). Emite sinal currentChanged(int)
quando o usuário troca a página.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QListWidget, QListWidgetItem

from app.ui.tokens import Color, Rounded, Spacing


SIDEBAR_QSS = f"""
QListWidget#Sidebar {{
    background-color: {Color.SURFACE};
    border: none;
    border-right: 1px solid {Color.BORDER};
    padding: {Spacing.SM}px;
    outline: 0;
}}
QListWidget#Sidebar::item {{
    color: {Color.MUTED};
    padding: {Spacing.SM}px {Spacing.MD}px;
    border-radius: {Rounded.SM}px;
    margin-bottom: 2px;
    font-size: 13px;
}}
QListWidget#Sidebar::item:hover {{
    background-color: {Color.SURFACE_ELEVATED};
    color: {Color.ON_SURFACE};
}}
QListWidget#Sidebar::item:selected {{
    background-color: {Color.SURFACE_ELEVATED};
    color: {Color.ACCENT};
    border-left: 2px solid {Color.ACCENT};
    font-weight: 700;
}}
"""


class SidebarNav(QListWidget):
    pageChanged = Signal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setAccessibleName("Navegação de resultados")
        self.setAccessibleDescription("Selecione a seção dos resultados.")
        self.setStyleSheet(SIDEBAR_QSS)
        self.setFrameShape(QListWidget.NoFrame)
        self.setFixedWidth(220)
        self.setSpacing(0)
        self.currentRowChanged.connect(self.pageChanged.emit)

    def add_section(self, icon: str, label: str, badge: str | None = None) -> QListWidgetItem:
        text = f"  {icon}   {label}"
        if badge:
            text += f"   ({badge})"
        item = QListWidgetItem(text)
        item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.addItem(item)
        return item

    def update_badge(self, row: int, label: str, icon: str, badge: str | None = None) -> None:
        text = f"  {icon}   {label}"
        if badge:
            text += f"   ({badge})"
        item = self.item(row)
        if item:
            item.setText(text)
