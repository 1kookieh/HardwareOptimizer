"""Seletor de perfil em cartões clicáveis com accent color por perfil.

Layout em grid 3 colunas: cada card mostra ícone, label, descrição curta
e um indicador de seleção (badge com check) no canto superior direito.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.models.profile import PROFILES
from app.ui.tokens import Color, PROFILE_ACCENTS, Rounded, Spacing


PROFILE_ICONS: dict[str, str] = {
    "games": "🎮",
    "development": "</>",
    "video_editing": "🎬",
    "general": "👤",
    "high_performance": "⚡",
    "stability": "🛡",
    "low_power": "🍃",
}


def _card_qss(accent: str, selected: bool) -> str:
    border_color = accent if selected else Color.BORDER
    bg = Color.SURFACE_ELEVATED if selected else Color.SURFACE
    border_width = 2 if selected else 1
    return (
        f"#ProfileCard{{background-color:{bg};"
        f"border:{border_width}px solid {border_color};"
        f"border-radius:{Rounded.LG}px;}}"
        f"#ProfileCard:hover{{border-color:{accent};"
        f"background-color:{Color.SURFACE_ELEVATED};}}"
        f"#ProfileCard:focus{{outline:none;border-color:{accent};}}"
    )


def _badge_qss(accent: str, visible: bool) -> str:
    if not visible:
        return "background:transparent;border:none;"
    return (
        f"background-color:{accent};color:{Color.ON_PRIMARY};"
        f"border-radius:10px;font-size:11px;font-weight:800;"
    )


class _ProfileCard(QPushButton):
    def __init__(self, key: str, label: str, description: str, accent: str, parent=None) -> None:
        super().__init__(parent)
        self.key = key
        self.accent = accent
        self.setObjectName("ProfileCard")
        self.setCheckable(True)
        self.setAccessibleName(f"Perfil {label}")
        self.setAccessibleDescription(description)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(140)
        self.setText("")  # we draw children manually

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.XS)

        # Top row: icon + check badge
        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(0)

        icon_lbl = QLabel(PROFILE_ICONS.get(key, "•"))
        icon_lbl.setStyleSheet(
            f"color:{accent};font-size:24px;font-weight:800;background:transparent;"
        )
        icon_lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        top.addWidget(icon_lbl, 0)
        top.addStretch(1)

        self.badge = QLabel("✓")
        self.badge.setFixedSize(20, 20)
        self.badge.setAlignment(Qt.AlignCenter)
        self.badge.setStyleSheet(_badge_qss(accent, False))
        top.addWidget(self.badge, 0, Qt.AlignTop | Qt.AlignRight)
        layout.addLayout(top)

        layout.addSpacing(Spacing.SM)

        title_lbl = QLabel(label)
        title_lbl.setStyleSheet(
            f"color:{Color.ON_SURFACE};font-size:15px;font-weight:700;background:transparent;"
        )
        layout.addWidget(title_lbl)

        desc_lbl = QLabel(description)
        desc_lbl.setStyleSheet(
            f"color:{Color.MUTED};font-size:11px;background:transparent;"
        )
        desc_lbl.setWordWrap(True)
        layout.addWidget(desc_lbl)

        layout.addStretch(1)
        self._apply_style(False)

    def _apply_style(self, selected: bool) -> None:
        self.setStyleSheet(_card_qss(self.accent, selected))
        self.badge.setStyleSheet(_badge_qss(self.accent, selected))


class ProfilePicker(QWidget):
    profileChanged = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAccessibleName("Seletor de perfil de otimização")
        self.setAccessibleDescription(
            "Escolha o foco da análise para priorizar recomendações."
        )
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._cards: dict[str, _ProfileCard] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.SM)

        title = QLabel("Selecione o perfil")
        title.setStyleSheet(
            f"color:{Color.ON_SURFACE};font-size:18px;font-weight:700;"
        )
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(Spacing.MD)
        grid.setVerticalSpacing(Spacing.MD)
        grid.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(grid, 1)

        cols = 3
        for index, (key, prof) in enumerate(PROFILES.items()):
            accent = PROFILE_ACCENTS.get(key, Color.ACCENT)
            card = _ProfileCard(key, prof.label, prof.description, accent, self)
            card.toggled.connect(self._on_card_toggled)
            self._group.addButton(card)
            self._cards[key] = card
            grid.addWidget(card, index // cols, index % cols)

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
