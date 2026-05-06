"""Dashboard pós-scan com resumo acionável."""
from __future__ import annotations

import os
import sys

import pytest

from app.recommendations import generate_recommendations
from tests.fixtures import make_scan


@pytest.fixture(scope="module", autouse=True)
def _qapp():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(sys.argv)
    yield app


def test_dashboard_summarizes_scan_and_top_priorities():
    from app.ui.main_window import MainWindow

    scan = make_scan(secure_boot="Desabilitado", pending_reboot=True)
    recs = generate_recommendations(scan, "games", games=["valorant"])
    window = MainWindow()

    window._render_dashboard(scan, recs, "games", ["valorant"])
    text = window.dashboard.toPlainText()

    assert "Resumo da análise" in text
    assert "Maior atenção" in text
    assert "Próxima ação segura" in text
    assert "Top 3 prioridades" in text
    assert "Updates disponíveis" in text
    assert "Valorant" in text
