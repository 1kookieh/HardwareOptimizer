"""Cards de estatística para o dashboard.

Cada card mostra:
- label superior pequeno (ex: "Recomendações")
- valor grande
- subtítulo curto
- borda colorida por tom (info, warning, success, danger)
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

from app.ui.tokens import Color, Rounded, Spacing
from app.ui.widgets.effects import apply_drop_shadow


TONE_COLORS: dict[str, str] = {
    "info": Color.ACCENT,
    "success": Color.SUCCESS,
    "warning": Color.WARNING,
    "danger": Color.DANGER,
    "neutral": Color.BORDER,
}


class StatCard(QFrame):
    def __init__(
        self,
        label: str,
        value: str,
        subtitle: str = "",
        tone: str = "info",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("StatCard")
        accent = TONE_COLORS.get(tone, Color.ACCENT)
        self.setStyleSheet(
            f"#StatCard{{background-color:{Color.SURFACE};"
            f"border:1px solid {Color.BORDER};"
            f"border-left:4px solid {accent};"
            f"border-radius:{Rounded.MD}px;}}"
        )
        self.setMinimumHeight(96)
        self.setAccessibleName(label)
        self.setAccessibleDescription(f"{label}: {value}. {subtitle}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.MD, Spacing.SM, Spacing.MD, Spacing.SM)
        layout.setSpacing(2)

        self.label_lbl = QLabel(label)
        self.label_lbl.setStyleSheet(
            f"color:{accent};font-size:11px;font-weight:700;"
            f"letter-spacing:0.5px;background:transparent;"
        )
        layout.addWidget(self.label_lbl)

        self.value_lbl = QLabel(value)
        self.value_lbl.setStyleSheet(
            f"color:{Color.ON_SURFACE};font-size:28px;font-weight:800;"
            f"background:transparent;"
        )
        layout.addWidget(self.value_lbl)

        self.subtitle_lbl = QLabel(subtitle)
        self.subtitle_lbl.setStyleSheet(
            f"color:{Color.MUTED};font-size:11px;background:transparent;"
        )
        self.subtitle_lbl.setWordWrap(True)
        layout.addWidget(self.subtitle_lbl)
        layout.addStretch(1)
        apply_drop_shadow(self, blur=16, offset_y=3, alpha=65)

    def update_values(self, value: str, subtitle: str = "") -> None:
        self.value_lbl.setText(value)
        if subtitle:
            self.subtitle_lbl.setText(subtitle)
