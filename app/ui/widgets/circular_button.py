"""Botão circular grande com animação de pulse contínua.

Usado como CTA primário da tela inicial. Implementado com QAbstractButton
+ paintEvent custom para garantir formato circular real (hit-test e
desenho), respeitando os tokens de DESIGN.md.

Decisões visuais:
- preenchimento sólido com leve gradiente radial para sensação de profundidade;
- texto "INICIAR" centralizado, espaçamento de letras amplo;
- ring externo pulsante em ACCENT (idle) ou SCAN_ACTIVE (running);
- nada de hint dentro do botão — esse rótulo fica em um QLabel externo.
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
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import QAbstractButton, QSizePolicy

from app.ui.tokens import Color, Motion


class CircularStartButton(QAbstractButton):
    """Botão circular com pulso contínuo e estados visuais distintos."""

    pulseChanged = Signal(float)
    abortRequested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setText("ANALISAR PC")
        self._subtitle = "Iniciar análise completa"
        self.setAccessibleName("Iniciar análise")
        self.setAccessibleDescription(
            "Executa a análise local do computador em modo somente leitura."
        )
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)
        self.setMinimumSize(QSize(260, 260))
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.resize(QSize(300, 300))
        self._pulse = 0.0
        self._is_running = False
        self._hover_in_circle = False

        self._anim = QPropertyAnimation(self, b"pulse", self)
        self._anim.setDuration(Motion.PULSE_MS)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.setLoopCount(-1)
        self._anim.start()

        # Quando rodando + clicado: emite abort em vez do clicked padrão
        self.clicked.connect(self._on_internal_clicked)

    def sizeHint(self) -> QSize:
        return QSize(300, 300)

    # --- pulse property -------------------------------------------------
    def get_pulse(self) -> float:
        return self._pulse

    def set_pulse(self, value: float) -> None:
        self._pulse = float(value)
        self.update()
        self.pulseChanged.emit(self._pulse)

    pulse = Property(float, get_pulse, set_pulse, notify=pulseChanged)

    # --- estado ---------------------------------------------------------
    def set_running(self, running: bool) -> None:
        if running == self._is_running:
            return
        self._is_running = running
        self._anim.setDuration(800 if running else Motion.PULSE_MS)
        self._refresh_label()
        self.update()

    def _refresh_label(self) -> None:
        if self._is_running:
            if self._hover_in_circle:
                self.setText("PARAR")
                self._subtitle = "Clique para cancelar"
            else:
                self.setText("Analisando...")
                self._subtitle = ""
        else:
            self.setText("ANALISAR PC")
            self._subtitle = "Iniciar análise completa"

    def is_running(self) -> bool:
        return self._is_running

    def _on_internal_clicked(self) -> None:
        # Quando rodando o clique pede cancelamento; o sinal externo
        # ``clicked`` continua existindo (assinado pelo MainWindow)
        # então o handler de start já checa is_running() e ignora.
        if self._is_running:
            self.abortRequested.emit()

    # --- hover (somente dentro do círculo) -----------------------------
    def mouseMoveEvent(self, event):  # noqa: N802
        inside = self._point_in_circle(event.position().x(), event.position().y())
        if inside != self._hover_in_circle:
            self._hover_in_circle = inside
            self._refresh_label()
            self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):  # noqa: N802
        if self._hover_in_circle:
            self._hover_in_circle = False
            self._refresh_label()
            self.update()
        super().leaveEvent(event)

    def _point_in_circle(self, x: float, y: float) -> bool:
        rect = self.rect()
        cx, cy = rect.center().x(), rect.center().y()
        radius = min(cx, cy) - 26
        dx = x - cx
        dy = y - cy
        return (dx * dx + dy * dy) <= (radius * radius)

    # --- hit-test circular ---------------------------------------------
    def hitButton(self, pos) -> bool:  # noqa: N802
        return self._point_in_circle(pos.x(), pos.y())

    # --- paint ----------------------------------------------------------
    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        cx, cy = rect.center().x(), rect.center().y()
        radius = min(cx, cy) - 26  # margem para o ring externo

        # ----- pulse interno suave (a animação principal vem do orbit em volta)
        if self._is_running:
            inner_ring = QColor(Color.SCAN_ACTIVE)
            inner_ring.setAlphaF(0.30 + 0.25 * (1 - self._pulse))
            painter.setPen(QPen(inner_ring, 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(
                QPointF(cx, cy),
                radius - 2 - 8 * self._pulse,
                radius - 2 - 8 * self._pulse,
            )

        # ----- borda estática fina
        painter.setPen(QPen(QColor(Color.BORDER), 1))
        painter.drawEllipse(QPointF(cx, cy), radius + 3, radius + 3)

        # ----- preenchimento com gradiente radial (profundidade)
        if not self.isEnabled():
            base = QColor(Color.SURFACE_ELEVATED)
        elif self._is_running and self._hover_in_circle:
            # Hover sobre botão rodando = mostrar intenção de parar
            base = QColor(Color.DANGER)
        elif self._is_running:
            base = QColor(Color.SCAN_ACTIVE)
        elif self.isDown():
            base = QColor(Color.PRIMARY_PRESSED)
        elif self.underMouse():
            base = QColor(Color.PRIMARY_HOVER)
        else:
            base = QColor(Color.PRIMARY)

        # Gradient mais profundo: highlight branco no topo-esquerdo,
        # base no meio, sombra escura no canto oposto
        highlight = QColor(255, 255, 255)
        highlight.setAlpha(70)
        bright = base.lighter(135)
        dark = base.darker(140)
        gradient = QRadialGradient(
            QPointF(cx - radius * 0.35, cy - radius * 0.40),
            radius * 1.7,
        )
        gradient.setColorAt(0.0, bright)
        gradient.setColorAt(0.45, base)
        gradient.setColorAt(1.0, dark)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(QPointF(cx, cy), radius, radius)

        # Camada de highlight semi-transparente no topo (efeito vidro)
        sheen = QRadialGradient(
            QPointF(cx - radius * 0.20, cy - radius * 0.55),
            radius * 0.9,
        )
        sheen.setColorAt(0.0, highlight)
        sheen.setColorAt(0.7, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(sheen))
        painter.drawEllipse(QPointF(cx, cy), radius, radius)

        # Borda interna sutil
        inner_border = QColor(0, 0, 0)
        inner_border.setAlpha(60)
        painter.setPen(QPen(inner_border, 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), radius - 1, radius - 1)

        # ----- foco visível por acessibilidade
        if self.hasFocus():
            focus_pen = QPen(QColor(Color.ACCENT), 2)
            painter.setPen(focus_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(cx, cy), radius + 7, radius + 7)

        # ----- label central
        if not self.isEnabled():
            text_color = QColor(Color.MUTED)
        elif self._is_running and self._hover_in_circle:
            text_color = QColor(Color.ON_PRIMARY)
        elif self._is_running:
            text_color = QColor(Color.ON_ACCENT)
        else:
            text_color = QColor(Color.ON_PRIMARY)
        painter.setPen(text_color)

        font_size = 24 if not self._is_running else 20
        font = QFont("Inter, Segoe UI", font_size)
        font.setBold(True)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 1)
        painter.setFont(font)

        # Compute layout: title + optional subtitle
        from PySide6.QtCore import QRect
        title_rect = QRect(rect)
        if self._subtitle:
            title_rect.setHeight(int(rect.height() * 0.55))
            title_rect.translate(0, int(rect.height() * 0.05))
        painter.drawText(title_rect, Qt.AlignCenter, self.text())

        if self._subtitle:
            sub_color = QColor(text_color)
            sub_color.setAlpha(200)
            painter.setPen(sub_color)
            sub_font = QFont("Inter, Segoe UI", 11)
            sub_font.setBold(False)
            painter.setFont(sub_font)
            sub_rect = QRect(rect)
            sub_rect.setTop(int(rect.height() * 0.58))
            painter.drawText(sub_rect, Qt.AlignHCenter | Qt.AlignTop, self._subtitle)
