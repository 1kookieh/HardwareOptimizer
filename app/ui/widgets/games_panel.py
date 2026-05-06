"""Painel de jogos com reveal animado.

Visível apenas quando o perfil 'games' está ativo. Usa
QPropertyAnimation em ``maximumHeight`` para slide-down suave.
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
    QLabel,
    QVBoxLayout,
    QWidget,
)

from app.models.profile import SUPPORTED_GAMES
from app.ui.tokens import Color, Motion, Rounded, Spacing


class GamesPanel(QFrame):
    selectionChanged = Signal(list)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAccessibleName("Seleção de jogos")
        self.setAccessibleDescription(
            "Selecione os jogos usados para priorizar recomendações do perfil Jogos."
        )
        self.setObjectName("GamesPanel")
        self.setStyleSheet(
            f"#GamesPanel{{background-color:{Color.SURFACE};"
            f"border:1px solid {Color.PROFILE_GAMING};"
            f"border-radius:{Rounded.LG}px;}}"
            f"QCheckBox{{color:{Color.ON_SURFACE};font-size:13px;padding:{Spacing.XS}px 0;}}"
            f"QCheckBox::indicator{{width:18px;height:18px;}}"
        )
        self._target_height = 0
        self._is_visible = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.SM)

        title = QLabel("Quais jogos você joga?")
        title.setStyleSheet(
            f"color:{Color.PROFILE_GAMING};font-size:14px;font-weight:700;"
        )
        layout.addWidget(title)

        subtitle = QLabel("As recomendações vão priorizar FPS, frametime e input lag para os títulos selecionados.")
        subtitle.setStyleSheet(f"color:{Color.MUTED};font-size:12px;")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        grid = QGridLayout()
        grid.setHorizontalSpacing(Spacing.MD)
        grid.setVerticalSpacing(Spacing.XS)
        layout.addLayout(grid)

        self._checks: dict[str, QCheckBox] = {}
        for index, (key, label) in enumerate(SUPPORTED_GAMES.items()):
            cb = QCheckBox(label)
            cb.setAccessibleName(f"Jogo {label}")
            cb.setAccessibleDescription(
                "Inclui este jogo na análise de recomendações para perfil Jogos."
            )
            cb.toggled.connect(self._emit_selection)
            self._checks[key] = cb
            grid.addWidget(cb, index // 2, index % 2)

        self._anim = QPropertyAnimation(self, b"maximumHeight", self)
        self._anim.setDuration(Motion.NORMAL_MS)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self.setMaximumHeight(0)
        self.setVisible(False)

    def _emit_selection(self, _: bool) -> None:
        self.selectionChanged.emit(self.selected_games())

    def selected_games(self) -> list[str]:
        return [k for k, cb in self._checks.items() if cb.isChecked()]

    def reveal(self, show: bool) -> None:
        if show == self._is_visible:
            return
        self._is_visible = show
        if show:
            self.setVisible(True)
            target = self.sizeHint().height()
            self._anim.stop()
            self._anim.setStartValue(self.maximumHeight())
            self._anim.setEndValue(max(target, 220))
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
            for cb in self._checks.values():
                cb.setChecked(False)
