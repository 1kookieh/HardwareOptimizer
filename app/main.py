from __future__ import annotations

import sys

from app.logging_setup import get_logger, setup_logging


def main() -> int:
    setup_logging()
    log = get_logger("main")
    log.info("HardwareOptimizer iniciando")

    from PySide6.QtWidgets import QApplication

    from app.ui import MainWindow

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    code = app.exec()
    log.info("HardwareOptimizer finalizando com código %s", code)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
