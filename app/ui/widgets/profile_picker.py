"""Seletor de perfil em cartões clicáveis com accent color por perfil.

Cada cartão expõe label e descrição curta. O perfil selecionado emite
``profileChanged(key)``. Usado na tela inicial.
"""
from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.models.profile import PROFILES
from app.ui.tokens import Color, PROFILE_ACCENTS, Rounded, Spacing


def _card_qss(accent: str, selected: bool) -> str:
    border_color = accent if selected else Color.BORDER
    bg = Color.SURFACE_ELEVATED if selected else Color.SURFACE
    return (
        f"QPushButton{{background-color:{bg};color:{Color.ON_SURFACE};"
        f"border:2px solid {border_color};border-radius:{Rounded.LG}px;"
        f"padding:{Spacing.MD}px {Spacing.MD}px;text-align:left;font-weight:600;}}"
        f"QPushButton:hover{{border-color:{Color.ACCENT};background-color:{Color.SURFACE_ELEVATED};}}"
        f"QPushButton:focus{{outline:none;border-color:{Color.ACCENT};}}"
    )


class _ProfileCard(QPushButton):
    def __init__(self, key: str, label: str, description: str, accent: str, parent=None) -> None:
        super().__init__(parent)
        self.key = key
        self.accent = accent
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(64)
        self._label_text = label
        self._description_text = description
        self.setText(f"{label}\n{description}")
        self._apply_style(False)

    def _apply_style(self, selected: bool) -> None:
        self.setStyleSheet(_card_qss(self.accent, selected))


class ProfilePicker(QWidget):
    profileChanged = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._cards: dict[str, _ProfileCard] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.SM)

        title = QLabel("Perfil de otimização")
        title.setStyleSheet(
            f"color:{Color.ON_SURFACE};font-size:18px;font-weight:700;"
            f"margin-bottom:{Spacing.XS}px;"
        )
        layout.addWidget(title)

        subtitle = QLabel("Escolha um foco. Você pode trocar a qualquer momento.")
        subtitle.setStyleSheet(f"color:{Color.MUTED};font-size:12px;margin-bottom:{Spacing.SM}px;")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        for key, prof in PROFILES.items():
            accent = PROFILE_ACCENTS.get(key, Color.ACCENT)
            card = _ProfileCard(key, prof.label, prof.description, accent, self)
            card.toggled.connect(self._on_card_toggled)
            self._group.addButton(card)
            self._cards[key] = card
            layout.addWidget(card)

        layout.addStretch(1)

        # Default selection
        first_key = next(iter(PROFILES.keys()))
        self._cards[first_key].setChecked(True)

    def _on_card_toggled(self, checked: bool) -> None:
        sender = self.sender()
        if not isinstance(sender, _ProfileCard):
            return
        sender._apply_style(checked)
        if checked:
            self.profileChanged.emit(sender.key)

    def selected_profile(self) -> str:
        for key, card in self._cards.items():
            if card.isChecked():
                return key
        return next(iter(self._cards.keys()))

    def set_selected(self, key: str) -> None:
        if key in self._cards:
            self._cards[key].setChecked(True)
