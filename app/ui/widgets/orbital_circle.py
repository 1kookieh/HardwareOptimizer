"""Botão circular envolto por um anel orbital animado e visível.

Desenha um anel base mais grosso, um arco de cometa brilhante girando
continuamente em loop, e quatro marcadores grandes nos pontos cardinais
que refletem o estado de cada estágio (idle / active / done).
"""
from __future__ import annotations

import math
from pathlib import Path

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
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget

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

MARKER_RADIUS = 22  # raio dos marcadores
RING_WIDTH = 5       # espessura do anel base
ASSET_DIR = Path(__file__).resolve().parents[1] / "assets" / "orbit"


class OrbitalCircle(QWidget):
    """Container com anel animado + botão circular ao centro."""

    phaseChanged = Signal(float)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, False)
        self.setMinimumSize(440, 480)

        self.button = CircularStartButton(self)

        self._states: dict[str, str] = {k: "idle" for k in STAGE_KEYS}
        self._pixmap_cache: dict[str, QPixmap | None] = {}

        self._phase = 0.0
        self._anim = QPropertyAnimation(self, b"phase", self)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.Linear)
        self._anim.setLoopCount(-1)
        self._set_idle_speed()
        self._anim.start()

    def sizeHint(self) -> QSize:
        return QSize(480, 500)

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
        self._anim.setDuration(5000)

    def _set_scan_speed(self) -> None:
        self._anim.setDuration(1800)

    # --- layout ---------------------------------------------------------
    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        # Botão central — proporção fixa, ocupa ~55% do menor lado
        bw = bh = max(200, int(min(w, h) * 0.50))
        self.button.setFixedSize(bw, bh)
        self.button.move((w - bw) // 2, (h - bh) // 2)

    def _ring_radius(self) -> float:
        bw = self.button.width()
        return bw / 2 + 32

    def _load_marker_pixmap(self, stage_key: str) -> QPixmap | None:
        if stage_key in self._pixmap_cache:
            return self._pixmap_cache[stage_key]

        for suffix in (".png", ".svg", ".jpg", ".jpeg"):
            candidate = ASSET_DIR / f"{stage_key}{suffix}"
            if not candidate.exists():
                continue
            pixmap = QPixmap(str(candidate))
            if not pixmap.isNull():
                self._pixmap_cache[stage_key] = pixmap
                return pixmap

        self._pixmap_cache[stage_key] = None
        return None

    # --- paint ----------------------------------------------------------
    def paintEvent(self, _event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        cx = self.width() / 2
        cy = self.height() / 2
        radius = self._ring_radius()
        running = self.button.is_running()

        rect = QRectF(cx - radius, cy - radius, radius * 2, radius * 2)

        # 0) Glow externo atrás do botão (camadas de halo)
        btn_radius = self.button.width() / 2 if self.button.width() else 100
        glow_base = QColor(Color.SCAN_ACTIVE if running else Color.PRIMARY)
        for offset, alpha in ((38, 22), (24, 36), (12, 60)):
            color = QColor(glow_base)
            color.setAlpha(alpha)
            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            painter.drawEllipse(QPointF(cx, cy), btn_radius + offset, btn_radius + offset)

        # 1) Anel base — mais grosso e com leve translucência
        base_color = QColor(Color.BORDER)
        base_color.setAlphaF(0.85)
        base_pen = QPen(base_color, RING_WIDTH)
        base_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(base_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(rect)

        # 2) Cometa: arco com gradiente de alpha simulando rastro
        sweep_color = QColor(Color.SCAN_ACTIVE if running else Color.ACCENT)
        steps = 24
        arc_total = 100.0  # comprimento do trail
        head_angle_deg = 90.0 - self._phase * 360.0
        for i in range(steps):
            t = i / (steps - 1) if steps > 1 else 0
            length = arc_total / steps
            start = head_angle_deg - i * length
            # alpha forte na cabeça, suave no trail
            alpha = int(240 * (1 - t) ** 1.4)
            if alpha < 8:
                continue
            color = QColor(sweep_color)
            color.setAlpha(alpha)
            pen = QPen(color, RING_WIDTH + 2, Qt.SolidLine, Qt.RoundCap)
            painter.setPen(pen)
            painter.drawArc(
                rect,
                int(start * 16),
                int(-length * 16),
            )

        # Cabeça do cometa — disco brilhante na frente do trail
        head_rad = math.radians(head_angle_deg - 90)
        hx = cx + math.cos(head_rad) * radius
        hy = cy + math.sin(head_rad) * radius
        glow = QColor(sweep_color)
        glow.setAlpha(120)
        painter.setPen(Qt.NoPen)
        painter.setBrush(glow)
        painter.drawEllipse(QPointF(hx, hy), 9, 9)
        bright = QColor(sweep_color)
        bright.setAlpha(255)
        painter.setBrush(bright)
        painter.drawEllipse(QPointF(hx, hy), 5, 5)

        # 3) Marcadores nos 4 pontos cardinais
        emoji_font = QFont("Segoe UI Emoji, Apple Color Emoji, Noto Color Emoji", 14)
        painter.setFont(emoji_font)
        for key, (icon, _label, angle_deg) in STAGE_INFO.items():
            state = self._states.get(key, "idle")
            mx, my = self._point_at(cx, cy, radius, angle_deg)

            if state == "active":
                fill = QColor(Color.ACCENT)
                ring = QColor(Color.ACCENT)
                halo_factor = 0.5 + 0.5 * math.sin(self._phase * math.tau * 3)
                halo_radius = MARKER_RADIUS + 6 + 10 * halo_factor
                halo_color = QColor(Color.ACCENT)
                halo_color.setAlphaF(0.30 + 0.30 * (1 - halo_factor))
                painter.setPen(Qt.NoPen)
                painter.setBrush(halo_color)
                painter.drawEllipse(QPointF(mx, my), halo_radius, halo_radius)
            elif state == "done":
                fill = QColor(Color.SUCCESS)
                ring = QColor(Color.SUCCESS)
            else:
                fill = QColor(Color.SURFACE_ELEVATED)
                ring = QColor(Color.BORDER)

            # Disco do marcador (mais largo: 22px raio)
            painter.setPen(QPen(ring, 2))
            painter.setBrush(fill)
            painter.drawEllipse(QPointF(mx, my), MARKER_RADIUS, MARKER_RADIUS)

            # Ícone interno: PNG/SVG customizado, com fallback para emoji.
            text_color = (
                QColor(Color.ON_PRIMARY) if state in {"active", "done"}
                else QColor(Color.MUTED)
            )
            pixmap = self._load_marker_pixmap(key)
            icon_size = MARKER_RADIUS * 2 - 8
            icon_rect = QRectF(
                mx - icon_size / 2,
                my - icon_size / 2,
                icon_size,
                icon_size,
            )
            if state == "done":
                painter.setPen(text_color)
                painter.drawText(icon_rect, Qt.AlignCenter, "✓")
            elif pixmap is not None:
                source = QRectF(0, 0, pixmap.width(), pixmap.height())
                painter.drawPixmap(icon_rect, pixmap, source)
            else:
                painter.setPen(text_color)
                painter.drawText(icon_rect, Qt.AlignCenter, icon)

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
