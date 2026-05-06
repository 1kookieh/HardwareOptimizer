"""Estados vazios básicos da interface."""
from __future__ import annotations

import os
import sys

import pytest


@pytest.fixture(scope="module", autouse=True)
def _qapp():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(sys.argv)
    yield app


def test_recommendation_table_shows_empty_state():
    from app.ui.main_window import MainWindow

    window = MainWindow()
    window._fill_table(window.recs_table, [])

    item = window.recs_table.item(0, 0)
    assert window.recs_table.rowCount() == 1
    assert item is not None
    assert "Nenhuma recomendação" in item.text()
    assert item.data(0x0100) is None  # Qt.UserRole


def test_history_list_shows_empty_state(monkeypatch):
    import app.ui.main_window as main_window

    class EmptyHistoryStore:
        def list_scans(self):
            return []

        def save_scan(self, *args, **kwargs):  # pragma: no cover - não usado neste teste
            return 1

        def update_status(self, *args, **kwargs):  # pragma: no cover - não usado neste teste
            return None

    monkeypatch.setattr(main_window, "HistoryStore", EmptyHistoryStore)

    window = main_window.MainWindow()
    item = window.history_list.item(0)

    assert window.history_list.count() == 1
    assert item is not None
    assert "Nenhuma análise" in item.text()
    assert item.data(0x0100) is None  # Qt.UserRole
