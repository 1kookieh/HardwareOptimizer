"""Dashboard pós-scan com cards de estatística e detalhes."""
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


def test_dashboard_stat_cards_reflect_scan_and_recommendations():
    from app.ui.main_window import MainWindow

    scan = make_scan(secure_boot="Desabilitado", pending_reboot=True)
    recs = generate_recommendations(scan, "games", games=["valorant"])
    window = MainWindow()

    window._render_dashboard(scan, recs, "games", ["valorant"])

    # Recomendações: número total
    assert window.stat_recs.value_lbl.text() == str(len(recs))
    # Updates: bate com scan
    assert window.stat_updates.value_lbl.text() == str(scan.updates.available_windows_updates)
    # Drivers: bate com lista de drivers antigos
    assert window.stat_drivers.value_lbl.text() == str(len(scan.updates.outdated_drivers))
    # Risco maior: deve ter algum label PT-BR válido quando há recs
    if recs:
        assert window.stat_risk.value_lbl.text() in {
            "Seguro", "Revisar", "Risco", "Bloqueado", "—"
        }
