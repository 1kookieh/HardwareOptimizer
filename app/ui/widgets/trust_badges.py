"""Cards decorativos de confiança exibidos na coluna direita da tela inicial.

Não interativos. Servem como reforço visual das garantias do app:
local-first, sem UAC, somente leitura.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.ui.tokens import Color, Rounded, Spacing
from app.ui.widgets.effects import apply_drop_shadow


BADGES: list[tuple[str, str, str, str]] = [
    # icon, title, subtitle, accent color
    ("💾", "Local-first", "100% local", Color.ACCENT),
    ("✓", "Sem UAC", "Sem elevação", Color.SUCCESS),
    ("🔒", "Read-only", "Apenas leitura", Color.WARNING),
]


class _TrustCard(QFrame):
    def __init__(self, icon: str, title: str, subtitle: str, accent: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("TrustCard")
        self.setStyleSheet(
            f"#TrustCard{{background-color:{Color.SURFACE};"
            f"border:1px solid {Color.BORDER};"
            f"border-radius:{Rounded.MD}px;}}"
        )
        self.setAccessibleName(f"{title}: {subtitle}")

        row = QHBoxLayout(self)
        row.setContentsMargins(Spacing.MD, Spacing.SM, Spacing.MD, Spacing.SM)
        row.setSpacing(Spacing.SM)

        icon_lbl = QLabel(icon)
        icon_lbl.setFixedSize(28, 28)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet(
            f"color:{accent};font-size:16px;background:transparent;"
        )
        row.addWidget(icon_lbl)

        text_box = QVBoxLayout()
        text_box.setContentsMargins(0, 0, 0, 0)
        text_box.setSpacing(0)

        t = QLabel(title)
        t.setStyleSheet(
            f"color:{Color.ON_SURFACE};font-size:13px;font-weight:700;background:transparent;"
        )
        text_box.addWidget(t)

        s = QLabel(subtitle)
        s.setStyleSheet(f"color:{Color.MUTED};font-size:11px;background:transparent;")
        text_box.addWidget(s)

        row.addLayout(text_box, 1)
        apply_drop_shadow(self, blur=14, offset_y=2, alpha=55)


class TrustBadgesColumn(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.SM)
        for icon, title, subtitle, accent in BADGES:
            layout.addWidget(_TrustCard(icon, title, subtitle, accent))
        layout.addStretch(1)
