"""Diálogo para adicionar e remover jogos da lista de seleção.

Usa :class:`app.storage.games_registry.GamesRegistry` para persistir
alterações em ``games.json``. Defaults nunca são apagados de fato —
ficam ocultos via lista ``hidden`` e podem ser reativados.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.models.profile import SUPPORTED_GAMES
from app.storage import GamesRegistry
from app.ui.tokens import Color, Rounded, Spacing


class ManageGamesDialog(QDialog):
    def __init__(self, registry: GamesRegistry, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._registry = registry
        self.setWindowTitle("Gerenciar lista de jogos")
        self.setMinimumSize(520, 420)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        outer.setSpacing(Spacing.SM)

        title = QLabel("Adicionar ou remover jogos")
        title.setStyleSheet(
            f"color:{Color.ON_SURFACE};font-size:15px;font-weight:700;"
        )
        outer.addWidget(title)

        subtitle = QLabel(
            "Jogos padrão podem ser ocultados ou reativados. Jogos personalizados "
            "ficam salvos localmente em games.json."
        )
        subtitle.setStyleSheet(f"color:{Color.MUTED};font-size:12px;")
        subtitle.setWordWrap(True)
        outer.addWidget(subtitle)

        # Lista
        self.list_widget = QListWidget()
        self.list_widget.setAccessibleName("Lista de jogos")
        self.list_widget.setStyleSheet(
            f"QListWidget{{background-color:{Color.SURFACE};"
            f"border:1px solid {Color.BORDER};"
            f"border-radius:{Rounded.SM}px;color:{Color.ON_SURFACE};}}"
            f"QListWidget::item{{padding:{Spacing.SM}px;}}"
            f"QListWidget::item:selected{{background-color:{Color.SURFACE_ELEVATED};"
            f"color:{Color.ACCENT};}}"
        )
        outer.addWidget(self.list_widget, 1)

        # Linha de adicionar
        add_row = QHBoxLayout()
        add_row.setSpacing(Spacing.SM)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nome do jogo (ex.: Apex Legends)")
        self.name_input.setAccessibleName("Nome do novo jogo")
        self.name_input.setStyleSheet(
            f"QLineEdit{{background-color:{Color.SURFACE};color:{Color.ON_SURFACE};"
            f"border:1px solid {Color.BORDER};border-radius:{Rounded.SM}px;padding:6px 10px;}}"
        )
        add_row.addWidget(self.name_input, 1)

        self.badge_input = QLineEdit()
        self.badge_input.setPlaceholderText("Sigla")
        self.badge_input.setMaxLength(4)
        self.badge_input.setMaximumWidth(80)
        self.badge_input.setAccessibleName("Sigla do novo jogo")
        self.badge_input.setStyleSheet(self.name_input.styleSheet())
        add_row.addWidget(self.badge_input, 0)

        self.add_btn = QPushButton("Adicionar")
        self.add_btn.clicked.connect(self._on_add)
        add_row.addWidget(self.add_btn, 0)
        outer.addLayout(add_row)

        # Linha de ação remover
        action_row = QHBoxLayout()
        action_row.addStretch(1)
        self.remove_btn = QPushButton("Remover selecionado")
        self.remove_btn.clicked.connect(self._on_remove)
        action_row.addWidget(self.remove_btn, 0)
        outer.addLayout(action_row)

        bb = QDialogButtonBox(QDialogButtonBox.Close)
        bb.rejected.connect(self.accept)
        outer.addWidget(bb)

        self._reload()

    def _reload(self) -> None:
        self.list_widget.clear()
        for entry in self._registry.entries():
            origin = "personalizado" if entry.custom else "padrão"
            item = QListWidgetItem(f"[{entry.badge}]  {entry.label}   ·  {origin}")
            item.setData(Qt.UserRole, entry.key)
            item.setData(Qt.UserRole + 1, entry.custom)
            self.list_widget.addItem(item)

        # Lista também jogos padrão ocultos para o usuário poder reativar
        hidden_defaults = [
            (key, label)
            for key, label in SUPPORTED_GAMES.items()
            if key in self._registry._hidden
        ]
        for key, label in hidden_defaults:
            item = QListWidgetItem(f"(oculto)  {label}   ·  padrão")
            item.setData(Qt.UserRole, key)
            item.setData(Qt.UserRole + 1, False)
            item.setData(Qt.UserRole + 2, "hidden_default")
            item.setForeground(Qt.gray)
            self.list_widget.addItem(item)

    def _on_add(self) -> None:
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.information(self, "Adicionar jogo", "Informe o nome do jogo.")
            return
        try:
            self._registry.add_custom(name, self.badge_input.text().strip() or None)
        except ValueError as exc:
            QMessageBox.warning(self, "Não foi possível adicionar", str(exc))
            return
        self.name_input.clear()
        self.badge_input.clear()
        self._reload()

    def _on_remove(self) -> None:
        item = self.list_widget.currentItem()
        if item is None:
            return
        key = item.data(Qt.UserRole)
        flag = item.data(Qt.UserRole + 2)
        if flag == "hidden_default":
            # Reativar default
            self._registry._hidden.discard(key)
            self._registry._save()
        else:
            self._registry.remove(key)
        self._reload()
