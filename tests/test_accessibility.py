"""Cobertura mínima para semântica acessível dos controles principais."""
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


def test_main_window_core_controls_have_accessible_names():
    from app.ui.main_window import MainWindow

    window = MainWindow()
    widgets = [
        window.start_screen,
        window.start_screen.start_button,
        window.start_screen.profile_picker,
        window.start_screen.games_panel,
        window.stack,
        window.tabs,
        window.recs_table,
        window.bios_table,
        window.games_table,
        window.history_list,
        window.back_btn,
        window.export_json_btn,
        window.export_html_btn,
        window.theme_btn,
    ]
    missing = [type(widget).__name__ for widget in widgets if not widget.accessibleName()]
    assert not missing


def test_profile_cards_and_game_checks_have_accessible_names():
    from PySide6.QtWidgets import QCheckBox, QPushButton

    from app.ui.main_window import MainWindow

    window = MainWindow()
    profile_cards = [
        button
        for button in window.start_screen.profile_picker.findChildren(QPushButton)
        if button.isCheckable()
    ]
    game_checks = window.start_screen.games_panel.findChildren(QCheckBox)

    assert profile_cards
    assert game_checks
    assert all(card.accessibleName().startswith("Perfil ") for card in profile_cards)
    assert all(check.accessibleName().startswith("Jogo ") for check in game_checks)
