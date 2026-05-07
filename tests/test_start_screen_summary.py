"""Garante que o resumo da tela inicial acompanha seleção local."""
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


def _summary_values(screen) -> list[str]:
    from PySide6.QtWidgets import QLabel

    return [
        label.text()
        for label in screen.session_summary.findChildren(QLabel, "SummaryValue")
    ]


def test_start_screen_summary_defaults_to_games_and_fps():
    from app.ui.start_screen import StartScreen

    screen = StartScreen()
    values = _summary_values(screen)

    assert "Jogos" in values
    assert "Nenhum selecionado" in values
    assert "FPS" in values


def test_start_screen_summary_updates_profile():
    from app.ui.start_screen import StartScreen

    screen = StartScreen()
    screen.profile_picker.set_selected("stability")

    assert "Estabilidade" in _summary_values(screen)
