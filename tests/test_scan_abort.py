"""Regressões para cancelamento cooperativo da análise."""
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


def test_scan_worker_emit_stage_raises_when_abort_requested():
    from app.ui.scan_worker import ScanAborted, ScanWorker

    worker = ScanWorker()
    worker.request_abort()

    with pytest.raises(ScanAborted):
        worker._emit_stage("Sistema", 10)


def test_start_screen_keeps_scan_button_enabled_while_running():
    from app.ui.start_screen import StartScreen

    screen = StartScreen()
    screen.set_running(True)

    assert screen.start_button.isEnabled() is True
    assert screen.profile_picker.isEnabled() is False
    assert screen.games_panel.isEnabled() is False
    assert screen.objective_selector.isEnabled() is False


def test_main_window_abort_request_marks_worker_and_status(monkeypatch):
    from app.ui.main_window import MainWindow

    class FakeWorker:
        def __init__(self) -> None:
            self.aborting = False

        def isRunning(self) -> bool:  # noqa: N802
            return True

        def is_aborting(self) -> bool:
            return self.aborting

        def request_abort(self) -> None:
            self.aborting = True

    window = MainWindow()
    worker = FakeWorker()
    window._scan_worker = worker  # type: ignore[assignment]

    window._request_scan_abort()

    assert worker.aborting is True
    assert "Cancelando" in window.start_screen.status_label.text()
