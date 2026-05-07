"""Painel de detalhes da recomendação selecionada.

Exibe blocos lado a lado: Evidência, Estado atual, Estado recomendado,
Como validar, Rollback. Usado abaixo da tabela de recomendações.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.ui.tokens import Color, Rounded, Spacing


def _column_qss() -> str:
    return (
        f"QFrame#DetailColumn{{background-color:{Color.SURFACE};"
        f"border:1px solid {Color.BORDER};border-radius:{Rounded.MD}px;}}"
    )


class _DetailColumn(QFrame):
    def __init__(self, title: str, icon: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("DetailColumn")
        self.setStyleSheet(_column_qss())
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.MD, Spacing.SM, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.XS)

        header = QLabel(f"{icon}  {title}")
        header.setStyleSheet(
            f"color:{Color.ON_SURFACE};font-size:12px;font-weight:700;"
            f"background:transparent;"
        )
        layout.addWidget(header)

        self.body = QLabel("—")
        self.body.setWordWrap(True)
        self.body.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.body.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.body.setStyleSheet(
            f"color:{Color.MUTED};font-size:11px;background:transparent;"
        )
        layout.addWidget(self.body, 1)

    def set_text(self, text: str) -> None:
        self.body.setText(text or "—")


class RecommendationDetailsPanel(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("DetailsPanel")
        self.setStyleSheet(
            f"#DetailsPanel{{background-color:{Color.SURFACE};"
            f"border:1px solid {Color.BORDER};"
            f"border-radius:{Rounded.MD}px;}}"
        )
        self.setAccessibleName("Detalhes da recomendação selecionada")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        outer.setSpacing(Spacing.SM)

        header = QLabel("Detalhes da recomendação selecionada")
        header.setStyleSheet(
            f"color:{Color.ON_SURFACE};font-size:14px;font-weight:700;"
            f"background:transparent;"
        )
        outer.addWidget(header)

        # Title row
        self.title_row = QHBoxLayout()
        self.title_row.setSpacing(Spacing.SM)
        self.title_lbl = QLabel("Selecione uma recomendação")
        self.title_lbl.setStyleSheet(
            f"color:{Color.ON_SURFACE};font-size:15px;font-weight:700;"
            f"background:transparent;"
        )
        self.title_row.addWidget(self.title_lbl)
        self.title_row.addStretch(1)
        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet(
            f"background-color:{Color.WARNING};color:{Color.SURFACE};"
            f"padding:4px 10px;border-radius:{Rounded.SM}px;"
            f"font-size:11px;font-weight:700;"
        )
        self.status_lbl.setVisible(False)
        self.title_row.addWidget(self.status_lbl)
        outer.addLayout(self.title_row)

        self.meta_lbl = QLabel("")
        self.meta_lbl.setStyleSheet(
            f"color:{Color.MUTED};font-size:11px;background:transparent;"
        )
        outer.addWidget(self.meta_lbl)

        # Columns
        cols = QHBoxLayout()
        cols.setSpacing(Spacing.SM)
        self.evidence_col = _DetailColumn("Evidência", "🔍")
        self.current_col = _DetailColumn("Estado atual", "📍")
        self.recommended_col = _DetailColumn("Estado recomendado", "🎯")
        self.validate_col = _DetailColumn("Como validar", "✓")
        self.rollback_col = _DetailColumn("Rollback", "↺")
        for col in (
            self.evidence_col,
            self.current_col,
            self.recommended_col,
            self.validate_col,
            self.rollback_col,
        ):
            cols.addWidget(col, 1)
        outer.addLayout(cols, 1)

        self.clear()

    def clear(self) -> None:
        self.title_lbl.setText("Selecione uma recomendação na tabela acima")
        self.meta_lbl.setText("")
        self.status_lbl.setVisible(False)
        for col in (
            self.evidence_col,
            self.current_col,
            self.recommended_col,
            self.validate_col,
            self.rollback_col,
        ):
            col.set_text("—")

    def show_recommendation(self, rec, status: str = "pending") -> None:
        self.title_lbl.setText(rec.title)
        self.meta_lbl.setText(
            f"Categoria: {rec.category.value}  ·  Prioridade: {rec.priority.value}  ·  "
            f"Risco: {rec.risk.value}"
        )
        status_pt = {"pending": "Pendente", "applied": "Aplicada", "ignored": "Ignorada"}.get(
            status, status
        )
        self.status_lbl.setText(status_pt)
        self.status_lbl.setVisible(True)

        evidence_text = "\n".join(f"• {e}" for e in (rec.evidence or [])) or "—"
        manual_text = ""
        if rec.manual_steps:
            manual_text = "\n".join(f"• {s}" for s in rec.manual_steps)

        self.evidence_col.set_text(evidence_text)
        self.current_col.set_text(rec.current_state or "—")
        self.recommended_col.set_text(rec.recommended_state or "—")
        validate = rec.how_to_validate or "—"
        if manual_text:
            validate = f"{validate}\n\nPassos manuais:\n{manual_text}"
        self.validate_col.set_text(validate)
        self.rollback_col.set_text(rec.rollback or "—")
