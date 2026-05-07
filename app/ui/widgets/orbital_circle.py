"""Botão circular envolto por um anel orbital animado.

Desenha um anel base ao redor do CircularStartButton e um arco de
"cometa" girando continuamente em loop. Quatro marcadores embutidos
no anel — Sistema, Hardware, BIOS, Updates — refletem o estágio
atual da análise via :meth:`set_stage` (idle / active / done).

Idle: cometa gira lentamente e os marcadores ficam neutros.
Durante scan: cometa acelera e os marcadores acendem em sequência.
"""
from __future__ import annotations

import math

from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QPointF,
    QPropertyAnimation,
    QRectF,
    QSize,
    Qt,
    Signal,
)
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QLabel, QWidget

from app.ui.tokens import Color
from app.ui.widgets.circular_button import CircularStartButton


STAGE_KEYS = ("system", "hardware", "bios", "updates")
STAGE_INFO: dict[str, tuple[str, str, float]] = {
    # key: (icon, label, angle in degrees, 0=top, clockwise)
    "system":   ("🖥", "Sistema",  0.0),
    "hardware": ("🧬", "Hardware", 90.0),
    "bios":     ("🎛", "BIOS",     180.0),
    "updates":  ("⬇", "Updates",  270.0),
}


class OrbitalCircle(QWidget):
    """Container com anel animado + botão circular ao centro."""

    phaseChanged = Signal(float)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, False)
        self.setMinimumSize(420, 460)

        self.button = CircularStartButton(self)

        self._states: dict[str, str] = {k: "idle" for k in STAGE_KEYS}
        self._labels: dict[str, QLabel] = {}
        for key, (_icon, label_text, _angle) in STAGE_INFO.items():
            lbl = QLabel(label_text, self)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
            lbl.setStyleSheet(
                f"color:{Color.MUTED};font-size:11px;font-weight:600;"
                f"background:transparent;"
            )
            self._labels[key] = lbl

        # Animação de fase contínua (cometa rotacionando)
        self._phase = 0.0
        self._anim = QPropertyAnimation(self, b"phase", self)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.Linear)
        self._anim.setLoopCount(-1)
        self._set_idle_speed()
        self._anim.start()

    def sizeHint(self) -> QSize:
        return QSize(460, 480)

    # --- phase property -------------------------------------------------
    def get_phase(self) -> float:
        return self._phase

    def set_phase(self, value: float) -> None:
        self._phase = float(value)
        self.update()
        self.phaseChanged.emit(self._phase)

    phase = Property(float, get_phase, set_phase, notify=phaseChanged)

    # --- speed control --------------------------------------------------
    def _set_idle_speed(self) -> None:
        self._anim.setDuration(6000)

    def _set_scan_speed(self) -> None:
        self._anim.setDuration(2200)

    # --- layout ---------------------------------------------------------
    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        # Botão central — ~50% da menor dimensão
        bw = bh = max(180, int(min(w, h) * 0.45))
        self.button.setFixedSize(bw, bh)
        self.button.move((w - bw) // 2, (h - bh) // 2)

        # Posicionar labels fora do anel
        cx = w / 2
        cy = h / 2
        ring_radius = self._ring_radius()
        label_distance = ring_radius + 30
        for key, lbl in self._labels.items():
            angle_deg = STAGE_INFO[key][2]
            rad = math.radians(angle_deg - 90)  # 0° = topo
            lx = cx + math.cos(rad) * label_distance
            ly = cy + math.sin(rad) * label_distance
            lbl.adjustSize()
            lbl.move(int(lx - lbl.width() / 2), int(ly - lbl.height() / 2))

    def _ring_radius(self) -> float:
        # Raio do anel orbital (entre o botão e a borda do widget)
        bw = self.button.width()
        return bw / 2 + 26

    # --- paint ----------------------------------------------------------
    def paintEvent(self, _event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        cx = self.width() / 2
        cy = self.height() / 2
        radius = self._ring_radius()
        running = self.button.is_running()

        rect = QRectF(cx - radius, cy - radius, radius * 2, radius * 2)

        # 1) Anel base (faint)
        base_pen = QPen(QColor(Color.BORDER), 2)
        painter.setPen(base_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(rect)

        # 2) Cometa: arco curto seguindo a fase atual
        sweep_color = QColor(Color.SCAN_ACTIVE if running else Color.ACCENT)
        # Várias partições para simular um trail com alphas decrescentes
        steps = 18
        arc_total = 70.0  # graus de comprimento total do trail
        # Qt: ângulos em 16ths de grau, 0° = 3h, sentido anti-horário positivo
        head_angle_deg = 90.0 - self._phase * 360.0  # começa no topo, anti-horário
        for i in range(steps):
            t = i / (steps - 1)
            length = arc_total / steps
            start = head_angle_deg - i * length
            alpha = int(255 * (1 - t) * (1 - t))  # quadrático
            color = QColor(sweep_color)
            color.setAlpha(alpha)
            pen = QPen(color, 4, Qt.SolidLine, Qt.RoundCap)
            painter.setPen(pen)
            painter.drawArc(
                rect,
                int(start * 16),
                int(-length * 16),  # negativo = sentido horário
            )

        # 3) Marcadores nos 4 pontos cardinais
        marker_radius = 14
        emoji_font = QFont("Segoe UI Emoji, Apple Color Emoji, Noto Color Emoji", 11)
        painter.setFont(emoji_font)
        for key, (icon, _label, angle_deg) in STAGE_INFO.items():
            state = self._states.get(key, "idle")
            mx, my = self._point_at(cx, cy, radius, angle_deg)

            if state == "active":
                fill = QColor(Color.ACCENT)
                ring = QColor(Color.ACCENT)
                ring.setAlphaF(0.55)
                # Halo pulsante (fração da fase em senoide)
                halo_factor = 0.5 + 0.5 * math.sin(self._phase * math.tau * 3)
                halo_radius = marker_radius + 4 + 6 * halo_factor
                halo_color = QColor(Color.ACCENT)
                halo_color.setAlphaF(0.20 + 0.25 * (1 - halo_factor))
                painter.setPen(Qt.NoPen)
                painter.setBrush(halo_color)
                painter.drawEllipse(QPointF(mx, my), halo_radius, halo_radius)
            elif state == "done":
                fill = QColor(Color.SUCCESS)
                ring = QColor(Color.SUCCESS)
            else:
                fill = QColor(Color.SURFACE_ELEVATED)
                ring = QColor(Color.BORDER)

            # Disco do marcador
            painter.setPen(QPen(ring, 2))
            painter.setBrush(fill)
            painter.drawEllipse(QPointF(mx, my), marker_radius, marker_radius)

            # Ícone dentro
            if state == "done":
                painter.setPen(QColor(Color.ON_PRIMARY))
                painter.drawText(
                    QRectF(mx - marker_radius, my - marker_radius,
                           marker_radius * 2, marker_radius * 2),
                    Qt.AlignCenter,
                    "✓",
                )
            else:
                painter.setPen(
                    QColor(Color.ON_PRIMARY) if state == "active" else QColor(Color.MUTED)
                )
                painter.drawText(
                    QRectF(mx - marker_radius, my - marker_radius,
                           marker_radius * 2, marker_radius * 2),
                    Qt.AlignCenter,
                    icon,
                )

            # Label color follow state
            lbl = self._labels.get(key)
            if lbl is not None:
                if state == "active":
                    lc = Color.ACCENT
                elif state == "done":
                    lc = Color.SUCCESS
                else:
                    lc = Color.MUTED
                lbl.setStyleSheet(
                    f"color:{lc};font-size:11px;font-weight:700;"
                    f"background:transparent;"
                )

        painter.end()

    @staticmethod
    def _point_at(cx: float, cy: float, radius: float, angle_deg: float) -> tuple[float, float]:
        rad = math.radians(angle_deg - 90)
        return cx + math.cos(rad) * radius, cy + math.sin(rad) * radius

    # ------------------------------------------------------------------ API
    def set_stage(self, stage: str, state: str) -> None:
        if stage not in self._states:
            return
        self._states[stage] = state
        # Ajusta velocidade caso haja algum ativo
        any_active = any(s == "active" for s in self._states.values())
        any_pending = any(s in {"active", "idle"} for s in self._states.values())
        if any_active:
            self._set_scan_speed()
        elif not any_pending:
            self._set_idle_speed()
        self.update()

    def reset_stages(self) -> None:
        for k in self._states:
            self._states[k] = "idle"
        self._set_idle_speed()
        self.update()

    def mark_stage_active(self, stage: str) -> None:
        self.set_stage(stage, "active")

    def mark_stage_done(self, stage: str) -> None:
        self.set_stage(stage, "done")
