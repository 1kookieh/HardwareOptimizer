"""Wrapper visual ao redor do CircularStartButton com 4 marcadores de estágio.

Os marcadores ficam posicionados em N, E, S, O e podem assumir três
estados visuais:

- idle: cinza neutro (decorativo)
- active: accent (estágio em execução)
- done: success (estágio concluído)

Os estados são atualizados externamente via :meth:`set_stage`. O mapa
padrão é:

- top    → "system"
- right  → "hardware"
- bottom → "bios"
- left   → "updates"
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.ui.tokens import Color, Spacing
from app.ui.widgets.circular_button import CircularStartButton


STAGE_KEYS = ("system", "hardware", "bios", "updates")
STAGE_CONFIG: dict[str, tuple[str, str]] = {
    "system": ("🖥", "Sistema"),
    "hardware": ("🧬", "Hardware"),
    "bios": ("🎛", "BIOS"),
    "updates": ("⬇", "Updates"),
}


class _StageMarker(QWidget):
    def __init__(self, stage: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.stage = stage
        icon, label = STAGE_CONFIG.get(stage, ("•", stage.title()))
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignCenter)

        self.icon_lbl = QLabel(icon)
        self.icon_lbl.setAlignment(Qt.AlignCenter)
        self.icon_lbl.setFixedSize(28, 28)
        layout.addWidget(self.icon_lbl, 0, Qt.AlignHCenter)

        self.text_lbl = QLabel(label)
        self.text_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.text_lbl, 0, Qt.AlignHCenter)

        self.setFixedSize(80, 60)
        self.set_state("idle")

    def set_state(self, state: str) -> None:
        if state == "active":
            color = Color.ACCENT
            weight = 700
        elif state == "done":
            color = Color.SUCCESS
            weight = 700
        else:
            color = Color.MUTED
            weight = 500
        self.icon_lbl.setStyleSheet(
            f"background-color:{Color.SURFACE_ELEVATED};color:{color};"
            f"border:1px solid {color};border-radius:14px;font-size:14px;"
        )
        self.text_lbl.setStyleSheet(
            f"color:{color};font-size:11px;font-weight:{weight};background:transparent;"
        )


class OrbitalCircle(QWidget):
    """Container que dispõe o botão circular ao centro com 4 marcadores ao redor."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.button = CircularStartButton(self)
        self._markers: dict[str, _StageMarker] = {
            stage: _StageMarker(stage, self) for stage in STAGE_KEYS
        }
        self.setMinimumSize(420, 460)

    def sizeHint(self):  # noqa: D401
        from PySide6.QtCore import QSize
        return QSize(460, 480)

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        btn = self.button
        bw = bh = min(int(min(w, h) * 0.66), 320)
        btn.setFixedSize(bw, bh)
        bx = (w - bw) // 2
        by = (h - bh) // 2
        btn.move(bx, by)

        # Position markers
        cx = w // 2
        cy = h // 2
        offset_x = bw // 2 + 28
        offset_y = bh // 2 + 24

        positions = {
            "system": (cx, cy - offset_y - 30),       # top
            "hardware": (cx + offset_x + 20, cy),     # right
            "bios": (cx, cy + offset_y + 30),         # bottom
            "updates": (cx - offset_x - 20, cy),      # left
        }
        for stage, marker in self._markers.items():
            mx, my = positions[stage]
            marker.move(mx - marker.width() // 2, my - marker.height() // 2)

    # ------------------------------------------------------------------ API
    def set_stage(self, stage: str, state: str) -> None:
        if stage in self._markers:
            self._markers[stage].set_state(state)

    def reset_stages(self) -> None:
        for marker in self._markers.values():
            marker.set_state("idle")

    def mark_stage_active(self, stage: str) -> None:
        """Marca um estágio como ativo, sem alterar os já concluídos."""
        if stage not in self._markers:
            return
        marker = self._markers[stage]
        marker.set_state("active")

    def mark_stage_done(self, stage: str) -> None:
        if stage in self._markers:
            self._markers[stage].set_state("done")
