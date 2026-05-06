"""Garante que tabelas de recomendações têm layout estável e ordenável."""
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


def test_recommendation_tables_have_fixed_sortable_headers():
    from PySide6.QtWidgets import QHeaderView

    from app.ui.main_window import MainWindow, REC_TABLE_COLUMN_WIDTHS

    window = MainWindow()
    for table in (window.recs_table, window.bios_table, window.games_table):
        header = table.horizontalHeader()
        assert header.sectionsMovable() is False
        assert table.isSortingEnabled() is True
        assert header.isSortIndicatorShown() is True
        for column, width in enumerate(REC_TABLE_COLUMN_WIDTHS):
            assert header.sectionResizeMode(column) == QHeaderView.Fixed
            assert table.columnWidth(column) == width


def test_recommendation_table_keeps_fixed_widths_after_render():
    from app.recommendations import generate_recommendations
    from app.ui.main_window import MainWindow, REC_TABLE_COLUMN_WIDTHS
    from tests.fixtures import make_scan

    window = MainWindow()
    recs = generate_recommendations(make_scan(), "games", games=["valorant"])

    window._fill_table(window.recs_table, recs)

    assert window.recs_table.isSortingEnabled() is True
    for column, width in enumerate(REC_TABLE_COLUMN_WIDTHS):
        assert window.recs_table.columnWidth(column) == width
