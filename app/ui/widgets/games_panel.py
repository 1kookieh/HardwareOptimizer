"""Painel de jogos com grid de cards e reveal animado.

Visível apenas quando o perfil 'games' está ativo. Cada jogo é um card
com badge, label e checkbox. Slide-down via QPropertyAnimation.
"""
from __future__ import annotations

from PySide6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    Qt,
    Signal,
)
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from app.models.profile import SUPPORTED_GAMES
from app.ui.tokens import Color, Motion, Rounded, Spacing


GAME_BADGES: dict[str, tuple[str, str]] = {
    # key: (short_label, accent_hex)
    "valorant": ("VAL", "#FF4655"),
    "league_of_legends": ("LoL", "#C89B3C"),
    "cod_warzone": ("WZ", "#F5A524"),
    "marvel_rivals": ("MR", "#E11D48"),
    "fortnite": ("F", "#7C3AED"),
    "cs2": ("CS", "#22C55E"),
}


def _card_qss(selected: bool) -> str:
    border = Color.PROFILE_GAMING if selected else Color.BORDER
    bg = Color.SURFACE_ELEVATED if selected else Color.SURFACE
    return (
        f"#GameCard{{background-color:{bg};"
        f"border:1px solid {border};border-radius:{Rounded.MD}px;}}"
        f"#GameCard:hover{{border-color:{Color.PROFILE_GAMING};}}"
    )


class _GameCard(QFrame):
    toggled_changed = Signal(str, bool)

    def __init__(self, key: str, label: str, parent=None) -> None:
        super().__init__(parent)
        self.key = key
        self.setObjectName("GameCard")
        self.setMinimumHeight(56)
        self.setCursor(Qt.PointingHandCursor)
        short, accent = GAME_BADGES.get(key, (label[:2].upper(), Color.ACCENT))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(Spacing.MD, Spacing.SM, Spacing.MD, Spacing.SM)
        layout.setSpacing(Spacing.SM)

        badge = QLabel(short)
        badge.setFixedSize(36, 36)
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet(
            f"background-color:{accent};color:{Color.ON_PRIMARY};"
            f"border-radius:{Rounded.SM}px;font-weight:800;font-size:11px;"
        )
        layout.addWidget(badge)

        text = QLabel(label)
        text.setStyleSheet(
            f"color:{Color.ON_SURFACE};font-size:13px;font-weight:600;background:transparent;"
        )
        text.setWordWrap(True)
        layout.addWidget(text, 1)

        self.checkbox = QCheckBox()
        self.checkbox.setAccessibleName(f"Jogo {label}")
        self.checkbox.setAccessibleDescription(
            "Inclui este jogo na análise de recomendações para perfil Jogos."
        )
        self.checkbox.toggled.connect(self._on_toggled)
        layout.addWidget(self.checkbox, 0, Qt.AlignRight)

        self._apply_style(False)

    def mousePressEvent(self, event):  # noqa: N802
        if event.button() == Qt.LeftButton:
            self.checkbox.toggle()
            event.accept()
            return
        super().mousePressEvent(event)

    def _on_toggled(self, checked: bool) -> None:
        self._apply_style(checked)
        self.toggled_changed.emit(self.key, checked)

    def _apply_style(self, selected: bool) -> None:
        self.setStyleSheet(_card_qss(selected))

    def is_checked(self) -> bool:
        return self.checkbox.isChecked()

    def set_checked(self, checked: bool) -> None:
        self.checkbox.setChecked(checked)


class GamesPanel(QFrame):
    selectionChanged = Signal(list)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAccessibleName("Seleção de jogos")
        self.setAccessibleDescription(
            "Selecione os jogos usados para priorizar recomendações do perfil Jogos."
        )
        self.setObjectName("GamesPanelContainer")
        self.setStyleSheet(
            f"#GamesPanelContainer{{background-color:transparent;border:none;}}"
        )
        self._is_visible = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.SM)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(Spacing.XS)
        title = QLabel("Jogos")
        title.setStyleSheet(
            f"color:{Color.ON_SURFACE};font-size:15px;font-weight:700;"
        )
        header_row.addWidget(title)
        opt = QLabel("(opcional)")
        opt.setStyleSheet(f"color:{Color.MUTED};font-size:13px;")
        header_row.addWidget(opt)
        header_row.addStretch(1)
        layout.addLayout(header_row)

        subtitle = QLabel(
            "Selecione os jogos que você joga para receber recomendações específicas."
        )
        subtitle.setStyleSheet(f"color:{Color.MUTED};font-size:12px;")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        grid = QGridLayout()
        grid.setHorizontalSpacing(Spacing.MD)
        grid.setVerticalSpacing(Spacing.SM)
        layout.addLayout(grid)

        self._cards: dict[str, _GameCard] = {}
        cols = 4
        for index, (key, label) in enumerate(SUPPORTED_GAMES.items()):
            card = _GameCard(key, label, self)
            card.toggled_changed.connect(self._on_card_changed)
            self._cards[key] = card
            grid.addWidget(card, index // cols, index % cols)

        self._anim = QPropertyAnimation(self, b"maximumHeight", self)
        self._anim.setDuration(Motion.NORMAL_MS)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self.setMaximumHeight(0)
        self.setVisible(False)

    def _on_card_changed(self, _key: str, _checked: bool) -> None:
        self.selectionChanged.emit(self.selected_games())

    def selected_games(self) -> list[str]:
        return [k for k, c in self._cards.items() if c.is_checked()]

    def reveal(self, show: bool) -> None:
        if show == self._is_visible:
            return
        self._is_visible = show
        if show:
            self.setVisible(True)
            target = max(self.sizeHint().height(), 200)
            self._anim.stop()
            self._anim.setStartValue(self.maximumHeight())
            self._anim.setEndValue(target)
            self._anim.start()
        else:
            self._anim.stop()
            self._anim.setStartValue(self.maximumHeight())
            self._anim.setEndValue(0)
            self._anim.finished.connect(self._after_collapse)
            self._anim.start()

    def _after_collapse(self) -> None:
        try:
            self._anim.finished.disconnect(self._after_collapse)
        except (RuntimeError, TypeError):
            pass
        if not self._is_visible:
            self.setVisible(False)
            for card in self._cards.values():
                card.set_checked(False)
