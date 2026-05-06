"""Botão circular grande com animação de pulse contínua.

Usado como CTA primário da tela inicial. Implementado com QAbstractButton
+ paintEvent custom para garantir formato circular real (hit-test e
desenho), respeitando os tokens de DESIGN.md.
"""
from __future__ import annotations

from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QPointF,
    QPropertyAnimation,
    QSize,
    Qt,
    Signal,
)
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QAbstractButton

from app.ui.tokens import Color, Motion


class CircularStartButton(QAbstractButton):
    """Botão circular com pulso contínuo e estados visuais.

    Estados:
    - idle: cor primária, pulso suave em ACCENT
    - running: cor SCAN_ACTIVE, pulso mais rápido
    - disabled: dessaturado, sem pulso
    """

    pulseChanged = Signal(float)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setText("INICIAR")
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumSize(QSize(280, 280))
        self.setSizePolicy(*self._equal_policy())
        self._pulse = 0.0
        self._is_running = False

        self._anim = QPropertyAnimation(self, b"pulse", self)
        self._anim.setDuration(Motion.PULSE_MS)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.setLoopCount(-1)
        self._anim.start()

    @staticmethod
    def _equal_policy():
        from PySide6.QtWidgets import QSizePolicy

        return (QSizePolicy.Preferred, QSizePolicy.Preferred)

    def sizeHint(self) -> QSize:
        return QSize(320, 320)

    # --- pulse property ---
    def get_pulse(self) -> float:
        return self._pulse

    def set_pulse(self, value: float) -> None:
        self._pulse = float(value)
        self.update()
        self.pulseChanged.emit(self._pulse)

    pulse = Property(float, get_pulse, set_pulse, notify=pulseChanged)

    def set_running(self, running: bool) -> None:
        if running == self._is_running:
            return
        self._is_running = running
        self._anim.setDuration(800 if running else Motion.PULSE_MS)
        self.setText("ANALISANDO" if running else "INICIAR")
        self.update()

    def is_running(self) -> bool:
        return self._is_running

    # --- hit-test circular ---
    def hitButton(self, pos) -> bool:  # noqa: N802
        rect = self.rect()
        cx, cy = rect.center().x(), rect.center().y()
        radius = min(cx, cy) - 30
        dx = pos.x() - cx
        dy = pos.y() - cy
        return (dx * dx + dy * dy) <= (radius * radius)

    # --- paint ---
    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        cx, cy = rect.center().x(), rect.center().y()
        radius = min(cx, cy) - 30

        # Outer pulsing ring
        ring_color_hex = Color.SCAN_ACTIVE if self._is_running else Color.ACCENT
        ring_color = QColor(ring_color_hex)
        ring_color.setAlpha(int(180 * (1 - self._pulse)))
        ring_radius = radius + 6 + 26 * self._pulse
        ring_pen = QPen(ring_color, 3)
        painter.setPen(ring_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), ring_radius, ring_radius)

        # Static border ring
        border = QPen(QColor(Color.BORDER), 1)
        painter.setPen(border)
        painter.drawEllipse(QPointF(cx, cy), radius + 4, radius + 4)

        # Inner filled circle
        if not self.isEnabled():
            fill = QColor(Color.SURFACE_ELEVATED)
        elif self._is_running:
            fill = QColor(Color.SCAN_ACTIVE)
        elif self.isDown():
            fill = QColor(Color.PRIMARY_PRESSED)
        elif self.underMouse():
            fill = QColor(Color.PRIMARY_HOVER)
        else:
            fill = QColor(Color.PRIMARY)
        painter.setPen(Qt.NoPen)
        painter.setBrush(fill)
        painter.drawEllipse(QPointF(cx, cy), radius, radius)

        # Inner subtle highlight
        highlight = QColor(255, 255, 255, 18)
        painter.setBrush(highlight)
        painter.drawEllipse(
            QPointF(cx, cy - radius * 0.25),
            radius * 0.85,
            radius * 0.45,
        )

        # Label
        text_color = (
            QColor(Color.ON_ACCENT)
            if self._is_running
            else QColor(Color.ON_PRIMARY)
        )
        if not self.isEnabled():
            text_color = QColor(Color.MUTED)
        painter.setPen(text_color)
        font = QFont("Inter, Segoe UI", 22)
        font.setBold(True)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 3)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, self.text())

        # Subtle hint below label
        hint_font = QFont("Inter, Segoe UI", 10)
        hint_font.setLetterSpacing(QFont.AbsoluteSpacing, 2)
        painter.setFont(hint_font)
        hint = "Coleta automática · somente leitura" if not self._is_running else "aguarde"
        painter.setPen(QColor(255, 255, 255, 160))
        painter.drawText(
            rect.adjusted(0, int(radius * 0.45), 0, 0),
            Qt.AlignHCenter | Qt.AlignTop,
            hint,
        )
