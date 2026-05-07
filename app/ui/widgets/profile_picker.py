"""Seletor de perfil em cartões com ícone destacado e accent por perfil.

Cada card mostra:
- ícone em container colorido (accent transparente) à esquerda
- título + descrição curta no centro
- badge ✓ visível APENAS no card selecionado
- barra de gradient horizontal no rodapé do card selecionado
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.models.profile import PROFILES
from app.ui.tokens import Color, PROFILE_ACCENTS, Rounded, Spacing
from app.ui.widgets.effects import apply_drop_shadow
from app.ui.widgets.icon_asset import AssetIcon


PROFILE_ICONS: dict[str, str] = {
    "games": "profile-games",
    "development": "profile-development",
    "video_editing": "profile-video",
    "general": "profile-general",
    "high_performance": "profile-performance",
    "stability": "profile-stability",
    "low_power": "profile-low-power",
}


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r = int(h[0:2], 16)
    g = int(h[2:4], 16)
    b = int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


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


def _icon_box_qss(accent: str) -> str:
    return (
        f"background-color:{_hex_to_rgba(accent, 0.15)};"
        f"border-radius:{Rounded.MD}px;"
        f"color:{accent};"
    )


def _gradient_qss(accent: str, visible: bool) -> str:
    if not visible:
        return "background:transparent;border:none;"
    return (
        f"background:qlineargradient(x1:0, y1:0, x2:1, y2:0, "
        f"stop:0 transparent, stop:0.4 {_hex_to_rgba(accent, 0.4)}, "
        f"stop:1 {accent});"
        f"border-radius:2px;border:none;"
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
        self.setMinimumHeight(96)
        self.setText("")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.SM)
        layout.setSpacing(Spacing.SM)

        # Linha principal: icon container + texto + badge
        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(Spacing.MD)

        # Icon container (caixa colorida com transparência)
        self.icon_box = QFrame()
        self.icon_box.setFixedSize(48, 48)
        self.icon_box.setStyleSheet(_icon_box_qss(accent))
        ib_layout = QVBoxLayout(self.icon_box)
        ib_layout.setContentsMargins(0, 0, 0, 0)
        icon_lbl = AssetIcon(PROFILE_ICONS.get(key, "profile-general"), fallback="•", size=34)
        ib_layout.addWidget(icon_lbl)
        top.addWidget(self.icon_box, 0, Qt.AlignVCenter)

        # Texto
        text_box = QVBoxLayout()
        text_box.setContentsMargins(0, 0, 0, 0)
        text_box.setSpacing(2)
        title_lbl = QLabel(label)
        title_lbl.setStyleSheet(
            f"color:{Color.ON_SURFACE};font-size:15px;font-weight:700;"
            f"background:transparent;border:none;"
        )
        text_box.addWidget(title_lbl)
        desc_lbl = QLabel(description)
        desc_lbl.setStyleSheet(
            f"color:{Color.MUTED};font-size:11px;"
            f"background:transparent;border:none;"
        )
        desc_lbl.setWordWrap(True)
        text_box.addWidget(desc_lbl)
        top.addLayout(text_box, 1)

        # Badge ✓ — INVISÍVEL e SEM TEXTO até estar selecionado
        self.badge = QLabel("")
        self.badge.setFixedSize(22, 22)
        self.badge.setAlignment(Qt.AlignCenter)
        self.badge.setStyleSheet("background:transparent;border:none;")
        top.addWidget(self.badge, 0, Qt.AlignTop | Qt.AlignRight)
        layout.addLayout(top)

        layout.addStretch(1)

        self.gradient_bar = QFrame()
        self.gradient_bar.setFixedHeight(3)
        self.gradient_bar.setStyleSheet(_gradient_qss(accent, False))
        layout.addWidget(self.gradient_bar)

        self._apply_style(False)
        apply_drop_shadow(self, blur=18, offset_y=3, alpha=70)

    def _apply_style(self, selected: bool) -> None:
        self.setStyleSheet(_card_qss(self.accent, selected))
        if selected:
            self.badge.setText("✓")
            self.badge.setStyleSheet(
                f"background-color:{self.accent};color:{Color.ON_PRIMARY};"
                f"border-radius:11px;font-size:12px;font-weight:800;"
                f"border:none;"
            )
        else:
            # CRUCIAL: remover o texto, não só o background
            self.badge.setText("")
            self.badge.setStyleSheet("background:transparent;border:none;")
        self.gradient_bar.setStyleSheet(_gradient_qss(self.accent, selected))


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

        title = QLabel("1. Escolha o perfil de análise")
        title.setStyleSheet(
            f"color:{Color.ON_SURFACE};font-size:16px;font-weight:700;"
        )
        layout.addWidget(title)

        subtitle = QLabel(
            "O perfil define o foco da análise e as recomendações prioritárias."
        )
        subtitle.setStyleSheet(f"color:{Color.MUTED};font-size:12px;")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        grid = QGridLayout()
        grid.setHorizontalSpacing(Spacing.MD)
        grid.setVerticalSpacing(Spacing.MD)
        grid.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(grid, 1)

        cols = 2
        for index, (key, prof) in enumerate(PROFILES.items()):
            accent = PROFILE_ACCENTS.get(key, Color.ACCENT)
            card = _ProfileCard(key, prof.label, prof.description, accent, self)
            card.toggled.connect(self._on_card_toggled)
            self._group.addButton(card)
            self._cards[key] = card
            grid.addWidget(card, index // cols, index % cols)

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
