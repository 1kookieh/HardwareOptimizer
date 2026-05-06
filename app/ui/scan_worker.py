"""Worker em QThread que executa ``collect_full_scan`` fora da UI thread.

A coleta tem chamadas a PowerShell, WMI e HTTP que podem somar dezenas
de segundos. Manter a UI responsiva exige rodar em uma thread auxiliar
e reportar progresso via signals.
"""
from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from app.collectors import collect_full_scan
from app.models.hardware import FullScan


class ScanWorker(QThread):
    """Executa a coleta em background e emite sinais de progresso/conclusão."""

    progress = Signal(str, int)
    finished_ok = Signal(object)  # FullScan
    failed = Signal(str)

    def run(self) -> None:  # noqa: D401
        try:
            scan: FullScan = collect_full_scan(on_stage=self._emit_stage)
            self.progress.emit("Concluído", 100)
            self.finished_ok.emit(scan)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))

    def _emit_stage(self, label: str, percent: int) -> None:
        self.progress.emit(label, percent)
