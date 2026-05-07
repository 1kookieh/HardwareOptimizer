"""Worker em QThread que executa ``collect_full_scan`` fora da UI thread.

A coleta tem chamadas a PowerShell, WMI e HTTP que podem somar dezenas
de segundos. Manter a UI responsiva exige rodar em uma thread auxiliar
e reportar progresso via signals.

Suporta cancelamento cooperativo: o callback de progresso checa
``_abort`` entre estágios e levanta :class:`ScanAborted` para abortar
a coleta de forma controlada.
"""
from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from app.collectors import collect_full_scan
from app.logging_setup import get_logger
from app.models.hardware import FullScan

_log = get_logger("ui.scan_worker")


class ScanAborted(Exception):
    """Sinaliza cancelamento solicitado pelo usuário."""


class ScanWorker(QThread):
    """Executa a coleta em background e emite sinais de progresso/conclusão."""

    progress = Signal(str, int)
    finished_ok = Signal(object)  # FullScan
    failed = Signal(str)
    aborted = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._abort = False

    def request_abort(self) -> None:
        """Marca a flag de cancelamento. A coleta para no próximo estágio."""
        self._abort = True

    def is_aborting(self) -> bool:
        return self._abort

    def run(self) -> None:  # noqa: D401
        _log.info("scan iniciado")
        try:
            scan: FullScan = collect_full_scan(on_stage=self._emit_stage)
            self.progress.emit("Concluído", 100)
            _log.info(
                "scan concluído: %d aviso(s) de coleta",
                len(scan.collection_errors),
            )
            for err in scan.collection_errors:
                _log.debug("coleta: %s", err)
            self.finished_ok.emit(scan)
        except ScanAborted:
            _log.info("scan cancelado pelo usuário")
            self.aborted.emit()
        except Exception as exc:  # noqa: BLE001
            _log.exception("falha durante scan")
            self.failed.emit(str(exc))

    def _emit_stage(self, label: str, percent: int) -> None:
        if self._abort:
            raise ScanAborted()
        self.progress.emit(label, percent)
