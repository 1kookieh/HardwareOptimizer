"""Seletor segmentado de objetivo de análise (visual-only por enquanto).

Mostra 4 botões mutuamente exclusivos: FPS, Input lag, Estabilidade e
Balanceado. A intenção é alimentar a engine futuramente; por ora apenas
expõe a escolha via :meth:`selected` para registro/relatório.

Aparece só quando o perfil "Jogos" está ativo.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.ui.tokens import Color, Rounded, Spacing


OBJECTIVES: list[tuple[str, str, str]] = [
    # key, label, icon
    ("fps", "FPS", "◉"),
    ("input_lag", "Input lag", "ϟ"),
    ("stability", "Estabilidade", "⬟"),
    ("balanced", "Balanceado", "⚖"),
]


def _btn_qss(selected: bool) -> str:
    if selected:
        return (
            f"QPushButton{{background-color:{Color.PRIMARY};"
            f"color:{Color.ON_PRIMARY};border:1px solid {Color.PRIMARY};"
            f"border-radius:{Rounded.SM}px;padding:10px 14px;font-weight:800;font-size:13px;}}"
        )
    return (
        f"QPushButton{{background-color:transparent;"
        f"color:{Color.MUTED};border:1px solid {Color.BORDER};"
        f"border-radius:{Rounded.SM}px;padding:10px 14px;font-weight:700;font-size:13px;}}"
        f"QPushButton:hover{{color:{Color.ON_SURFACE};border-color:{Color.ACCENT};}}"
    )


class ObjectiveSelector(QWidget):
    objectiveChanged = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAccessibleName("Objetivo da análise")
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._buttons: dict[str, QPushButton] = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(Spacing.XS)

        title = QLabel("3. Objetivo da análise")
        title.setStyleSheet(
            f"color:{Color.ON_SURFACE};font-size:14px;font-weight:700;"
        )
        outer.addWidget(title)

        subtitle = QLabel(
            "Defina o objetivo principal para orientar as recomendações."
        )
        subtitle.setStyleSheet(f"color:{Color.MUTED};font-size:12px;")
        subtitle.setWordWrap(True)
        outer.addWidget(subtitle)

        row = QHBoxLayout()
        row.setSpacing(Spacing.SM)
        for key, label, icon in OBJECTIVES:
            btn = QPushButton(f"{icon}  {label}")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setAccessibleName(f"Objetivo {label}")
            btn.toggled.connect(self._on_toggled)
            btn.setProperty("objective_key", key)
            btn.setStyleSheet(_btn_qss(False))
            self._group.addButton(btn)
            self._buttons[key] = btn
            row.addWidget(btn, 1)
        outer.addLayout(row)

        # default = fps
        self._buttons["fps"].setChecked(True)

    def _on_toggled(self, checked: bool) -> None:
        sender = self.sender()
        if not isinstance(sender, QPushButton):
            return
        sender.setStyleSheet(_btn_qss(checked))
        if checked:
            key = sender.property("objective_key")
            if key:
                self.objectiveChanged.emit(str(key))

    def selected(self) -> str:
        for key, btn in self._buttons.items():
            if btn.isChecked():
                return key
        return "fps"
