"""Garante que chips coloridos retornam QTableWidgetItem com label e cor."""
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


def test_risk_chip_uses_pt_br_label():
    from app.ui.widgets.chips import risk_chip

    assert "seguro" in risk_chip("safe").text()
    assert "revisar" in risk_chip("review").text()
    assert "risco" in risk_chip("risky").text()
    assert "bloqueado" in risk_chip("blocked").text()


def test_priority_chip_uses_pt_br_label():
    from app.ui.widgets.chips import priority_chip

    assert "alta" in priority_chip("high").text()
    assert "média" in priority_chip("medium").text()
    assert "baixa" in priority_chip("low").text()
    assert "crítica" in priority_chip("critical").text()


def test_status_chip_uses_pt_br_label():
    from app.ui.widgets.chips import status_chip

    assert "pendente" in status_chip("pending").text()
    assert "aplicada" in status_chip("applied").text()
    assert "ignorada" in status_chip("ignored").text()


def test_category_chip_uses_human_label():
    from app.ui.widgets.chips import category_chip

    assert "BIOS" in category_chip("bios").text()
    assert "Drivers" in category_chip("drivers").text()
    assert "Jogos" in category_chip("games").text()


def test_chip_has_background_color():
    from app.ui.widgets.chips import risk_chip

    chip = risk_chip("safe")
    bg = chip.background().color()
    assert bg.alpha() > 0
    assert bg.red() + bg.green() + bg.blue() > 0


def test_unknown_value_does_not_crash():
    from app.ui.widgets.chips import priority_chip

    chip = priority_chip("desconhecido")
    assert "desconhecido" in chip.text()
