"""Painel de jogos com grid de cards e botão de gerenciamento.

Os jogos disponíveis vêm de :class:`app.storage.GamesRegistry`. Cada
card tenta carregar um arquivo de logo de
``app/ui/assets/games/{key}.(png|svg)``; quando ausente, usa um
emoji-fallback configurável e o badge curto vem do registry.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.storage import GameEntry, GamesRegistry
from app.ui.tokens import Color, Rounded, Spacing
from app.ui.widgets.effects import apply_drop_shadow
from app.ui.widgets.icon_asset import load_icon_pixmap


GAME_BADGE_ACCENTS: dict[str, str] = {
    "valorant": "#FF4655",
    "league_of_legends": "#C89B3C",
    "cod_warzone": "#F5A524",
    "marvel_rivals": "#E11D48",
    "fortnite": "#7C3AED",
    "cs2": "#22C55E",
}

# Emoji fallback quando não há arquivo de logo. Genéricos / temáticos.
GAME_FALLBACK_EMOJI: dict[str, str] = {
    "valorant": "game-valorant",
    "league_of_legends": "game-league",
    "cod_warzone": "game-warzone",
    "marvel_rivals": "game-marvel",
    "fortnite": "game-fortnite",
    "cs2": "game-cs2",
}


_ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets" / "games"


def _load_icon_pixmap(key: str, size: int = 36) -> QPixmap | None:
    for suffix in (".png", ".svg", ".jpg", ".jpeg"):
        candidate = _ASSETS_DIR / f"{key}{suffix}"
        if candidate.exists():
            pix = QPixmap(str(candidate))
            if not pix.isNull():
                return pix.scaled(
                    QSize(size, size),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
    return None


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

    def __init__(self, entry: GameEntry, parent=None) -> None:
        super().__init__(parent)
        self.key = entry.key
        self.setObjectName("GameCard")
        self.setMinimumHeight(60)
        self.setCursor(Qt.PointingHandCursor)
        accent = GAME_BADGE_ACCENTS.get(entry.key, Color.ACCENT)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(Spacing.MD, Spacing.SM, Spacing.MD, Spacing.SM)
        layout.setSpacing(Spacing.SM)

        icon_widget = self._build_icon(entry, accent)
        layout.addWidget(icon_widget)

        text = QLabel(entry.label)
        text.setStyleSheet(
            f"color:{Color.ON_SURFACE};font-size:13px;font-weight:600;background:transparent;"
        )
        text.setWordWrap(True)
        layout.addWidget(text, 1)

        self.checkbox = QCheckBox()
        self.checkbox.setAccessibleName(f"Jogo {entry.label}")
        self.checkbox.setAccessibleDescription(
            "Inclui este jogo na análise de recomendações para perfil Jogos."
        )
        self.checkbox.toggled.connect(self._on_toggled)
        layout.addWidget(self.checkbox, 0, Qt.AlignRight)

        self._apply_style(False)
        apply_drop_shadow(self, blur=14, offset_y=2, alpha=60)

    def _build_icon(self, entry: GameEntry, accent: str) -> QWidget:
        pix = _load_icon_pixmap(entry.key, size=36)
        if pix is not None:
            container = QFrame()
            container.setFixedSize(40, 40)
            container.setStyleSheet(
                f"background-color:{Color.SURFACE};"
                f"border:1px solid {accent};"
                f"border-radius:{Rounded.SM}px;"
            )
            inner = QVBoxLayout(container)
            inner.setContentsMargins(2, 2, 2, 2)
            inner.setSpacing(0)
            label = QLabel()
            label.setPixmap(pix)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("background:transparent;border:none;")
            inner.addWidget(label)
            return container

        # Fallback local: SVG simbólico, sem asset remoto.
        fallback_pix = load_icon_pixmap(GAME_FALLBACK_EMOJI.get(entry.key, ""), size=36)
        if fallback_pix is not None:
            container = QFrame()
            container.setFixedSize(40, 40)
            container.setStyleSheet(
                f"background-color:{Color.SURFACE};"
                f"border:1px solid {accent};"
                f"border-radius:{Rounded.SM}px;"
            )
            inner = QVBoxLayout(container)
            inner.setContentsMargins(2, 2, 2, 2)
            inner.setSpacing(0)
            label = QLabel()
            label.setPixmap(fallback_pix)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("background:transparent;border:none;")
            inner.addWidget(label)
            return container

        container = QFrame()
        container.setFixedSize(40, 40)
        container.setStyleSheet(
            f"background-color:{accent};"
            f"border-radius:{Rounded.SM}px;"
        )
        inner = QVBoxLayout(container)
        inner.setContentsMargins(0, 0, 0, 0)
        inner.setSpacing(0)
        badge_lbl = QLabel("G")
        badge_lbl.setAlignment(Qt.AlignCenter)
        badge_lbl.setStyleSheet(
            f"color:{Color.ON_PRIMARY};font-size:13px;font-weight:900;"
            f"background:transparent;border:none;"
        )
        inner.addWidget(badge_lbl)
        return container

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


class GamesPanel(QWidget):
    selectionChanged = Signal(list)
    manageRequested = Signal()

    def __init__(self, registry: GamesRegistry | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setAccessibleName("Seleção de jogos")
        self.setAccessibleDescription(
            "Selecione os jogos usados para priorizar recomendações do perfil Jogos."
        )
        self._registry = registry or GamesRegistry()
        self._cards: dict[str, _GameCard] = {}

        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(0, 0, 0, 0)
        self._outer.setSpacing(Spacing.SM)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(Spacing.XS)
        title = QLabel("2. Jogos selecionados")
        title.setStyleSheet(
            f"color:{Color.ON_SURFACE};font-size:14px;font-weight:700;"
        )
        header.addWidget(title)
        header.addStretch(1)
        self.manage_btn = QPushButton("Gerenciar lista")
        self.manage_btn.setCursor(Qt.PointingHandCursor)
        self.manage_btn.setAccessibleName("Gerenciar lista de jogos")
        self.manage_btn.setStyleSheet(
            f"QPushButton{{background-color:transparent;color:{Color.MUTED};"
            f"border:1px solid {Color.BORDER};border-radius:{Rounded.SM}px;"
            f"padding:5px 12px;font-size:12px;}}"
            f"QPushButton:hover{{color:{Color.ON_SURFACE};border-color:{Color.ACCENT};}}"
        )
        self.manage_btn.clicked.connect(self.manageRequested.emit)
        header.addWidget(self.manage_btn)
        self._outer.addLayout(header)

        subtitle = QLabel(
            "Selecione os jogos que você joga para receber recomendações específicas."
        )
        subtitle.setStyleSheet(f"color:{Color.MUTED};font-size:12px;")
        subtitle.setWordWrap(True)
        self._outer.addWidget(subtitle)

        self._grid_container = QWidget()
        self._grid = QGridLayout(self._grid_container)
        self._grid.setHorizontalSpacing(Spacing.MD)
        self._grid.setVerticalSpacing(Spacing.SM)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._outer.addWidget(self._grid_container)

        self._populate()

    def _populate(self) -> None:
        for card in self._cards.values():
            card.setParent(None)
            card.deleteLater()
        self._cards.clear()
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item is not None and item.widget() is not None:
                item.widget().setParent(None)

        cols = 3
        for index, entry in enumerate(self._registry.entries()):
            card = _GameCard(entry, self._grid_container)
            card.toggled_changed.connect(self._on_card_changed)
            self._cards[entry.key] = card
            self._grid.addWidget(card, index // cols, index % cols)

    def refresh(self) -> None:
        self._populate()
        self.selectionChanged.emit(self.selected_games())

    def _on_card_changed(self, _key: str, _checked: bool) -> None:
        self.selectionChanged.emit(self.selected_games())

    def selected_games(self) -> list[str]:
        return [k for k, c in self._cards.items() if c.is_checked()]

    def set_visible_panel(self, visible: bool) -> None:
        self._grid_container.setVisible(visible)

    def reveal(self, show: bool) -> None:
        self.setVisible(show)
