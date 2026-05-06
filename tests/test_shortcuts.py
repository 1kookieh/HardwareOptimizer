"""Garante que MainWindow registra atalhos de teclado esperados."""
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


def _shortcut_strings(window) -> set[str]:
    from PySide6.QtGui import QShortcut

    return {sc.key().toString() for sc in window.findChildren(QShortcut)}


def test_main_window_registers_expected_shortcuts():
    from app.ui.main_window import MainWindow

    w = MainWindow()
    keys = _shortcut_strings(w)
    expected = {"F5", "Ctrl+R", "Esc", "Ctrl+T", "Ctrl+E", "Ctrl+Shift+E"}
    assert expected <= keys, f"faltando atalhos: {expected - keys}"


def test_back_button_has_tooltip_with_esc():
    from app.ui.main_window import MainWindow

    w = MainWindow()
    assert "Esc" in w.back_btn.toolTip()


def test_circular_button_has_tooltip_with_shortcut():
    from app.ui.main_window import MainWindow

    w = MainWindow()
    tip = w.start_screen.start_button.toolTip()
    assert "F5" in tip or "Ctrl+R" in tip
