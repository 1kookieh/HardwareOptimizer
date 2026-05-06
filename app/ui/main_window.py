from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence, QResizeEvent, QShortcut
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QStatusBar,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.models.hardware import FullScan
from app.models.profile import PROFILES, SUPPORTED_GAMES
from app.recommendations import generate_recommendations
from app.reports import build_report_dict, export_html, export_json
from app.storage import HistoryStore

from .scan_worker import ScanWorker
from .start_screen import StartScreen
from .theme import DARK_QSS, LIGHT_QSS
from .tokens import Color, Spacing
from .widgets import category_chip, priority_chip, risk_chip, status_chip


COMPACT_BREAKPOINT = 960
PAGE_START = 0
PAGE_RESULTS = 1


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("HardwareOptimizer — Local-first MVP")
        self.resize(1280, 800)
        self.setMinimumSize(720, 560)

        self._scan: FullScan | None = None
        self._recommendations = []
        self._store = HistoryStore()
        self._current_scan_id: int | None = None
        self._status_map: dict[str, str] = {}
        self._dark = True
        self._compact = False
        self._scan_worker: ScanWorker | None = None
        self._last_profile: str | None = None
        self._last_games: list[str] = []
        self._games_tab_index: int = -1

        self._build_ui()
        self._apply_theme()
        self._wire_shortcuts()

    # ------------------------------------------------------------------ build
    def _build_ui(self) -> None:
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.start_screen = StartScreen()
        self.start_screen.startRequested.connect(self._on_start_requested)
        self.stack.addWidget(self.start_screen)

        self.results_view = self._build_results_view()
        self.stack.addWidget(self.results_view)
        self._apply_accessibility()

        self.stack.setCurrentIndex(PAGE_START)

        self.setStatusBar(QStatusBar())
        self._progress_bar = QProgressBar()
        self._progress_bar.setAccessibleName("Progresso da análise")
        self._progress_bar.setAccessibleDescription("Mostra o progresso da coleta por etapa.")
        self._progress_bar.setMaximumWidth(220)
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setVisible(False)
        self.statusBar().addPermanentWidget(self._progress_bar)
        self.statusBar().showMessage("Pronto.")

    def _build_results_view(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.MD)
        layout.addLayout(self._build_top_bar())

        self.tabs = QTabWidget()
        self.dashboard = QTextEdit(readOnly=True)
        self.dashboard.setPlainText(
            "Análise concluída.\n\n"
            "Use as abas para navegar por hardware, recomendações, BIOS/UEFI, "
            "jogos, atualizações e histórico. Duplo clique numa recomendação "
            "abre os detalhes; clique direito permite marcar status."
        )
        self.tabs.addTab(self.dashboard, "Dashboard")

        self.hardware_text = QTextEdit(readOnly=True)
        self.tabs.addTab(self.hardware_text, "Hardware")

        self.recs_table = self._make_rec_table()
        self.tabs.addTab(self.recs_table, "Recomendações")

        self.bios_table = self._make_rec_table()
        self.tabs.addTab(self.bios_table, "BIOS / UEFI")

        self.games_table = self._make_rec_table()
        self._games_tab_index = self.tabs.addTab(self.games_table, "Jogos")

        self.updates_text = QTextEdit(readOnly=True)
        self.tabs.addTab(self.updates_text, "Atualizações")

        self.history_list = QListWidget()
        self.history_list.itemDoubleClicked.connect(self._on_history_open)
        self.tabs.addTab(self.history_list, "Histórico")
        self._refresh_history()

        layout.addWidget(self.tabs, 1)
        return page

    def _build_top_bar(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(Spacing.SM)

        self.back_btn = QPushButton("← Nova análise")
        self.back_btn.setAccessibleName("Nova análise")
        self.back_btn.setAccessibleDescription("Volta para a tela inicial sem apagar o histórico salvo.")
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.setToolTip("Voltar à tela inicial (Esc)")
        self.back_btn.clicked.connect(self._go_to_start)
        row.addWidget(self.back_btn)

        self.profile_label = QLabel("")
        self.profile_label.setStyleSheet(
            f"color:{Color.MUTED};font-size:13px;padding-left:{Spacing.MD}px;"
        )
        row.addWidget(self.profile_label)

        row.addStretch(1)

        self.export_json_btn = QPushButton("Exportar JSON")
        self.export_json_btn.setAccessibleName("Exportar relatório JSON")
        self.export_json_btn.setAccessibleDescription(
            "Exporta a última análise em arquivo JSON local."
        )
        self.export_json_btn.setEnabled(False)
        self.export_json_btn.setToolTip("Exportar relatório em JSON (Ctrl+E)")
        self.export_json_btn.clicked.connect(lambda: self._on_export("json"))
        row.addWidget(self.export_json_btn)

        self.export_html_btn = QPushButton("Exportar HTML")
        self.export_html_btn.setAccessibleName("Exportar relatório HTML")
        self.export_html_btn.setAccessibleDescription(
            "Exporta a última análise em relatório HTML local."
        )
        self.export_html_btn.setEnabled(False)
        self.export_html_btn.setToolTip("Exportar relatório em HTML (Ctrl+Shift+E)")
        self.export_html_btn.clicked.connect(lambda: self._on_export("html"))
        row.addWidget(self.export_html_btn)

        self.theme_btn = QToolButton()
        self.theme_btn.setAccessibleName("Alternar tema")
        self.theme_btn.setAccessibleDescription("Alterna entre tema claro e escuro.")
        self.theme_btn.setText("☀")
        self.theme_btn.setToolTip("Alternar tema claro/escuro (Ctrl+T)")
        self.theme_btn.clicked.connect(self._toggle_theme)
        row.addWidget(self.theme_btn)
        return row

    def _make_rec_table(self) -> QTableWidget:
        table = QTableWidget(0, 6)
        table.setHorizontalHeaderLabels(
            ["Título", "Categoria", "Prioridade", "Risco", "Status", "Resumo"]
        )
        table.horizontalHeader().setStretchLastSection(True)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setAlternatingRowColors(True)
        table.cellDoubleClicked.connect(lambda r, _c, t=table: self._show_rec_details(t, r))
        table.setContextMenuPolicy(Qt.CustomContextMenu)
        table.customContextMenuRequested.connect(lambda pos, t=table: self._on_rec_context(t, pos))
        return table

    def _apply_accessibility(self) -> None:
        self.stack.setAccessibleName("Navegação principal")
        self.stack.setAccessibleDescription("Alterna entre tela inicial e resultados da análise.")
        self.results_view.setAccessibleName("Resultados da análise")
        self.results_view.setAccessibleDescription(
            "Área com dashboard, hardware, recomendações, BIOS, jogos, atualizações e histórico."
        )
        self.tabs.setAccessibleName("Abas de resultados")
        self.tabs.setAccessibleDescription("Use as abas para navegar pelas seções do diagnóstico.")
        self.dashboard.setAccessibleName("Dashboard da análise")
        self.dashboard.setAccessibleDescription("Resumo inicial dos resultados da análise.")
        self.hardware_text.setAccessibleName("Dados de hardware")
        self.hardware_text.setAccessibleDescription("Lista dados detectados de sistema, hardware e BIOS.")
        self.recs_table.setAccessibleName("Tabela de recomendações")
        self.recs_table.setAccessibleDescription(
            "Lista recomendações com categoria, prioridade, risco, status e resumo."
        )
        self.bios_table.setAccessibleName("Tabela de recomendações de BIOS e UEFI")
        self.bios_table.setAccessibleDescription(
            "Lista recomendações relacionadas a BIOS, UEFI e firmware."
        )
        self.games_table.setAccessibleName("Tabela de recomendações de jogos")
        self.games_table.setAccessibleDescription(
            "Lista recomendações específicas para jogos selecionados."
        )
        self.updates_text.setAccessibleName("Dados de atualizações")
        self.updates_text.setAccessibleDescription(
            "Mostra atualizações do Windows, fontes oficiais e drivers antigos detectados."
        )
        self.history_list.setAccessibleName("Histórico de análises")
        self.history_list.setAccessibleDescription("Lista análises salvas localmente neste computador.")

    # ------------------------------------------------------ shortcuts
    def _wire_shortcuts(self) -> None:
        # F5 ou Ctrl+R: dispara nova análise (na start screen)
        for seq in ("F5", "Ctrl+R"):
            sc = QShortcut(QKeySequence(seq), self)
            sc.activated.connect(self._shortcut_run_scan)

        # Esc: voltar para start screen
        sc_esc = QShortcut(QKeySequence("Escape"), self)
        sc_esc.activated.connect(self._shortcut_back)

        # Ctrl+T: alternar tema
        sc_theme = QShortcut(QKeySequence("Ctrl+T"), self)
        sc_theme.activated.connect(self._toggle_theme)

        # Ctrl+E: exportar JSON
        sc_export_json = QShortcut(QKeySequence("Ctrl+E"), self)
        sc_export_json.activated.connect(lambda: self._on_export("json") if self._scan else None)

        # Ctrl+Shift+E: exportar HTML
        sc_export_html = QShortcut(QKeySequence("Ctrl+Shift+E"), self)
        sc_export_html.activated.connect(lambda: self._on_export("html") if self._scan else None)

    def _shortcut_run_scan(self) -> None:
        if self.stack.currentIndex() != PAGE_START:
            return
        self.start_screen._on_start_clicked()

    def _shortcut_back(self) -> None:
        if self.stack.currentIndex() == PAGE_RESULTS:
            self._go_to_start()

    # --------------------------------------------------------------- theme
    def _apply_theme(self) -> None:
        self.setStyleSheet(DARK_QSS if self._dark else LIGHT_QSS)
        if hasattr(self, "theme_btn"):
            self.theme_btn.setText("☀" if self._dark else "🌙")

    def _toggle_theme(self) -> None:
        self._dark = not self._dark
        self._apply_theme()

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802
        super().resizeEvent(event)
        compact = event.size().width() < COMPACT_BREAKPOINT
        if compact != self._compact:
            self._compact = compact
            self.statusBar().showMessage(
                "Modo compacto ativo." if compact else "Pronto."
            )

    # --------------------------------------------------------------- scan
    def _on_start_requested(self, profile: str, games: list[str]) -> None:
        if self._scan_worker is not None and self._scan_worker.isRunning():
            return
        self._last_profile = profile
        self._last_games = list(games)

        self.start_screen.set_running(True)
        self.start_screen.set_status("Iniciando coleta…")
        self.statusBar().showMessage("Coletando dados do sistema… (somente leitura)")
        self._progress_bar.setValue(0)
        self._progress_bar.setVisible(True)

        worker = ScanWorker(self)
        worker.progress.connect(self._on_scan_progress)
        worker.finished_ok.connect(self._on_scan_finished)
        worker.failed.connect(self._on_scan_failed)
        worker.finished.connect(worker.deleteLater)
        self._scan_worker = worker
        worker.start()

    def _on_scan_progress(self, label: str, percent: int) -> None:
        self.statusBar().showMessage(f"Coletando: {label}…")
        self.start_screen.set_status(f"{label} ({percent}%)")
        self._progress_bar.setValue(percent)

    def _on_scan_failed(self, message: str) -> None:
        self._progress_bar.setVisible(False)
        self.start_screen.set_running(False)
        self.start_screen.set_status("Falha na análise.")
        QMessageBox.critical(self, "Erro na análise", message)
        self._scan_worker = None

    def _on_scan_finished(self, scan: FullScan) -> None:
        try:
            profile = self._last_profile or "general"
            games = self._last_games
            recs = generate_recommendations(scan, profile, games)
            self._scan = scan
            self._recommendations = recs
            self._status_map = {r.title: "pending" for r in recs}

            self._render_hardware(scan)
            self._render_recommendations(recs, games)

            self.export_json_btn.setEnabled(True)
            self.export_html_btn.setEnabled(True)

            report = build_report_dict(scan, profile, games, recs)
            self._current_scan_id = self._store.save_scan(
                profile, games, scan.to_dict(), report["recommendations"]
            )
            self._refresh_history()

            profile_label = PROFILES.get(profile).label if profile in PROFILES else profile
            games_text = f" · jogos: {', '.join(SUPPORTED_GAMES.get(g, g) for g in games)}" if games else ""
            self.profile_label.setText(f"Perfil: {profile_label}{games_text}")

            self.statusBar().showMessage(
                f"Análise concluída. {len(recs)} recomendação(ões). "
                f"Avisos de coleta: {len(scan.collection_errors)}."
            )
            self.tabs.setCurrentIndex(2)
            self.stack.setCurrentIndex(PAGE_RESULTS)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Erro ao processar resultado", str(exc))
        finally:
            self._progress_bar.setVisible(False)
            self.start_screen.set_running(False)
            self.start_screen.reset_status()
            self._scan_worker = None

    def _go_to_start(self) -> None:
        if self._scan_worker is not None and self._scan_worker.isRunning():
            return
        if self._last_profile:
            self.start_screen.profile_picker.set_selected(self._last_profile)
        self.stack.setCurrentIndex(PAGE_START)
        self.statusBar().showMessage("Pronto.")

    # ----------------------------------------------------------- rendering
    def _render_hardware(self, scan: FullScan) -> None:
        lines = ["Sistema", "-" * 40]
        for k, v in scan.system.to_dict().items():
            lines.append(f"{k}: {v}")

        lines += ["", "Hardware", "-" * 40]
        for k, v in scan.hardware.to_dict().items():
            if k in ("storage", "ram_modules", "sensors"):
                continue
            lines.append(f"{k}: {v}")

        if scan.hardware.ram_modules:
            lines += ["", "Módulos de RAM", "-" * 40]
            for m in scan.hardware.ram_modules:
                d = m if isinstance(m, dict) else m.to_dict()
                lines.append(
                    f"- {d.get('manufacturer','?')} {d.get('part_number','?')} "
                    f"{d.get('capacity_gb','?')}GB @ {d.get('configured_clock_mhz','?')}MHz "
                    f"({d.get('form_factor','?')})"
                )

        if scan.hardware.storage:
            lines += ["", "Armazenamento", "-" * 40]
            for d in scan.hardware.storage:
                lines.append(
                    f"- {d.get('mountpoint')} {d.get('fstype')} "
                    f"{d.get('used_gb',0):.1f}/{d.get('total_gb',0):.1f} GB"
                )

        if scan.hardware.sensors:
            lines += ["", "Sensores (LibreHardwareMonitor)", "-" * 40]
            for stype, items in scan.hardware.sensors.items():
                top = sorted(items, key=lambda x: -float(x.get("value", 0)))[:5]
                for it in top:
                    lines.append(
                        f"- [{stype}] {it.get('parent','')} {it.get('name','')}: "
                        f"{it.get('value')}"
                    )
        else:
            lines += [
                "",
                "Sensores: LibreHardwareMonitor não detectado em execução. "
                "Inicie o LHM para habilitar leituras de temperatura/voltagem/clock.",
            ]

        lines += ["", "BIOS / UEFI", "-" * 40]
        for k, v in scan.bios.to_dict().items():
            if k == "exposed_settings":
                continue
            lines.append(f"{k}: {v}")
        if scan.bios.exposed_settings:
            lines += ["", "Configurações de BIOS expostas pelo fabricante", "-" * 40]
            for name, value in sorted(scan.bios.exposed_settings.items()):
                lines.append(f"{name}: {value}")
        else:
            lines.append(f"configurações detalhadas: {scan.bios.exposure_note}")

        if scan.collection_errors:
            lines += ["", "Avisos de coleta (não bloqueantes)", "-" * 40]
            lines += [f"- {e}" for e in scan.collection_errors]

        if scan.detection_sources:
            lines += ["", "Fontes de detecção", "-" * 40]
            for area, sources in scan.detection_sources.items():
                lines.append(f"{area}: {', '.join(sources)}")

        self.hardware_text.setPlainText("\n".join(lines))
        self._render_updates(scan)

    def _render_updates(self, scan: FullScan) -> None:
        updates = scan.updates
        lines = ["Atualizações do Windows", "-" * 40]
        lines.append(f"Reinicialização pendente: {updates.pending_reboot}")
        lines.append(f"Último hotfix: {updates.last_hotfix_id}")
        lines.append(f"Data do último hotfix: {updates.last_hotfix_date}")
        lines.append(f"Idade do último hotfix (dias): {updates.last_hotfix_age_days}")
        lines.append(f"Updates disponíveis: {updates.available_windows_updates}")
        lines.append(f"Status da checagem: {updates.update_check_status}")
        lines.append(f"Status online: {updates.online_check_status}")
        lines.append(f"URL BIOS/suporte: {updates.bios_lookup_url}")
        lines.append(f"Drivers avaliados: {updates.drivers_total}")

        if updates.official_sources:
            lines += ["", "Fontes oficiais consultadas", "-" * 40]
            lines += [f"- {url}" for url in updates.official_sources]
        if updates.driver_lookup_urls:
            lines += ["", "URLs oficiais de drivers", "-" * 40]
            lines += [f"- {kind}: {url}" for kind, url in updates.driver_lookup_urls.items()]

        lines += ["", "Drivers antigos (>3 anos)", "-" * 40]
        if updates.outdated_drivers:
            for driver in updates.outdated_drivers:
                d = driver if isinstance(driver, dict) else driver.to_dict()
                lines.append(
                    f"- {d.get('device_name')} | {d.get('provider')} | "
                    f"{d.get('version')} | {d.get('driver_date')} | {d.get('age_days')} dias"
                )
        else:
            lines.append("Nenhum driver antigo detectado automaticamente ou coleta indisponível.")

        self.updates_text.setPlainText("\n".join(lines))

    def _render_recommendations(self, recs, games: list[str]) -> None:
        bios_recs = [r for r in recs if r.category.value == "bios"]
        game_recs = [r for r in recs if r.category.value == "games"]

        self._fill_table(self.recs_table, recs)
        self._fill_table(self.bios_table, bios_recs)
        self._fill_table(self.games_table, game_recs)

        if self._games_tab_index >= 0:
            if not games:
                self.tabs.setTabText(self._games_tab_index, "Jogos")
            else:
                labels = ", ".join(SUPPORTED_GAMES.get(g, g) for g in games)
                title = f"Jogos ({labels})" if len(labels) <= 30 else f"Jogos ({labels[:30]}…)"
                self.tabs.setTabText(self._games_tab_index, title)

    def _fill_table(self, table: QTableWidget, recs) -> None:
        table.clearSpans()
        if not recs:
            table.setRowCount(1)
            item = QTableWidgetItem("Nenhuma recomendação nesta categoria.")
            item.setTextAlignment(Qt.AlignCenter)
            item.setFlags(Qt.ItemIsEnabled)
            item.setData(Qt.UserRole, None)
            table.setItem(0, 0, item)
            table.setSpan(0, 0, 1, table.columnCount())
            table.resizeColumnsToContents()
            return

        table.setRowCount(len(recs))
        for row, rec in enumerate(recs):
            current_status = self._status_map.get(rec.title, "pending")
            title_item = QTableWidgetItem(rec.title)
            cat_item = category_chip(rec.category.value)
            prio_item = priority_chip(rec.priority.value)
            risk_item = risk_chip(rec.risk.value)
            stat_item = status_chip(current_status)
            summary_item = QTableWidgetItem(rec.expected_benefit)

            for item in (title_item, cat_item, prio_item, risk_item, stat_item, summary_item):
                item.setData(Qt.UserRole, rec)
            table.setItem(row, 0, title_item)
            table.setItem(row, 1, cat_item)
            table.setItem(row, 2, prio_item)
            table.setItem(row, 3, risk_item)
            table.setItem(row, 4, stat_item)
            table.setItem(row, 5, summary_item)
        table.resizeColumnsToContents()

    def _refresh_status_cells(self) -> None:
        for table in (self.recs_table, self.bios_table, self.games_table):
            for row in range(table.rowCount()):
                title_item = table.item(row, 0)
                if not title_item:
                    continue
                rec = title_item.data(Qt.UserRole)
                if rec is None:
                    continue
                chip = status_chip(self._status_map.get(rec.title, "pending"))
                chip.setData(Qt.UserRole, rec)
                table.setItem(row, 4, chip)

    # ---------------------------------------- recommendation interactions
    def _show_rec_details(self, table: QTableWidget, row: int) -> None:
        item = table.item(row, 0)
        if item is None:
            return
        rec = item.data(Qt.UserRole)
        if rec is None:
            return
        dlg = RecommendationDialog(self, rec, self._status_map.get(rec.title, "pending"))
        result = dlg.exec()
        if result == QDialog.Accepted and dlg.chosen_status:
            self._set_status(rec.title, dlg.chosen_status)

    def _on_rec_context(self, table: QTableWidget, pos) -> None:
        index = table.indexAt(pos)
        if not index.isValid():
            return
        row = index.row()
        item = table.item(row, 0)
        rec = item.data(Qt.UserRole) if item else None
        if rec is None:
            return
        menu = QMenu(table)
        a_pending = QAction("Marcar como pendente", menu)
        a_applied = QAction("Marcar como aplicada", menu)
        a_ignored = QAction("Marcar como ignorada", menu)
        a_pending.triggered.connect(lambda: self._set_status(rec.title, "pending"))
        a_applied.triggered.connect(lambda: self._set_status(rec.title, "applied"))
        a_ignored.triggered.connect(lambda: self._set_status(rec.title, "ignored"))
        menu.addAction(a_pending)
        menu.addAction(a_applied)
        menu.addAction(a_ignored)
        menu.exec(table.viewport().mapToGlobal(pos))

    def _set_status(self, title: str, status: str) -> None:
        self._status_map[title] = status
        if self._current_scan_id is not None:
            try:
                self._store.update_status(self._current_scan_id, title, status)
            except Exception as exc:  # noqa: BLE001
                self.statusBar().showMessage(f"Erro ao salvar status: {exc}")
                return
        self._refresh_status_cells()
        self.statusBar().showMessage(f"Status atualizado: {title} → {status}")

    # ------------------------------------------------------ export & history
    def _on_export(self, fmt: str) -> None:
        if not self._scan or not self._last_profile:
            return
        report = build_report_dict(
            self._scan, self._last_profile, self._last_games, self._recommendations
        )
        suffix = ".json" if fmt == "json" else ".html"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar relatório",
            f"hardware_optimizer_report{suffix}",
            f"{fmt.upper()} (*{suffix})",
        )
        if not path:
            return
        if fmt == "json":
            export_json(report, Path(path))
        else:
            export_html(report, Path(path))
        QMessageBox.information(self, "Relatório exportado", f"Salvo em: {path}")

    def _refresh_history(self) -> None:
        self.history_list.clear()
        entries = self._store.list_scans()
        if not entries:
            item = QListWidgetItem("Nenhuma análise salva ainda. Execute uma análise para criar histórico.")
            item.setFlags(Qt.ItemIsEnabled)
            item.setData(Qt.UserRole, None)
            self.history_list.addItem(item)
            return

        for entry in entries:
            label = (
                f"#{entry['id']} · {entry['created_at']} · "
                f"{PROFILES.get(entry['profile']).label if entry['profile'] in PROFILES else entry['profile']}"
            )
            if entry["games"]:
                label += f" · jogos: {', '.join(entry['games'])}"
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, entry)
            self.history_list.addItem(item)

    def _on_history_open(self, item: QListWidgetItem) -> None:
        entry = item.data(Qt.UserRole)
        if not entry:
            return
        QMessageBox.information(
            self,
            f"Análise #{entry['id']}",
            f"Perfil: {entry['profile']}\nJogos: {entry['games']}\nData: {entry['created_at']}",
        )


class RecommendationDialog(QDialog):
    def __init__(self, parent, rec, current_status: str) -> None:
        super().__init__(parent)
        self.setWindowTitle(rec.title)
        self.resize(640, 560)
        self.chosen_status: str | None = None

        outer = QVBoxLayout(self)

        header = QLabel(
            f"<b>{rec.title}</b><br>"
            f"<span>Categoria: {rec.category.value} · Prioridade: {rec.priority.value} · "
            f"Risco: {rec.risk.value}</span>"
        )
        header.setWordWrap(True)
        outer.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        body = QWidget()
        bl = QVBoxLayout(body)
        for label, value in [
            ("Estado atual", rec.current_state),
            ("Estado recomendado", rec.recommended_state),
            ("Justificativa", rec.rationale),
            ("Benefício esperado", rec.expected_benefit),
            ("Impacto", rec.expected_impact),
            ("Quando não aplicar", rec.when_not_to_apply),
            ("Como validar", rec.how_to_validate),
            ("Segurança", rec.safety_note),
            ("Rollback", rec.rollback),
            ("Ação sensível", "Sim" if rec.manual_confirmation_required else "Não"),
        ]:
            if not value:
                continue
            row = QLabel(f"<b>{label}:</b> {value}")
            row.setWordWrap(True)
            bl.addWidget(row)
        if rec.manual_steps:
            bl.addWidget(QLabel("<b>Passos manuais:</b>"))
            for i, step in enumerate(rec.manual_steps, 1):
                lab = QLabel(f"{i}. {step}")
                lab.setWordWrap(True)
                bl.addWidget(lab)
        if rec.evidence:
            bl.addWidget(QLabel("<b>Evidência:</b>"))
            for e in rec.evidence:
                lab = QLabel(f"• {e}")
                lab.setWordWrap(True)
                bl.addWidget(lab)
        bl.addStretch(1)
        scroll.setWidget(body)
        outer.addWidget(scroll, 1)

        status_row = QHBoxLayout()
        status_row.addWidget(QLabel(f"Status atual: <b>{current_status}</b>"))
        status_row.addStretch(1)

        btn_pending = QPushButton("Marcar pendente")
        btn_apply = QPushButton("Marcar aplicada")
        btn_apply.setObjectName("Success")
        btn_ignore = QPushButton("Marcar ignorada")
        btn_pending.clicked.connect(lambda: self._choose("pending"))
        btn_apply.clicked.connect(lambda: self._choose("applied"))
        btn_ignore.clicked.connect(lambda: self._choose("ignored"))
        status_row.addWidget(btn_pending)
        status_row.addWidget(btn_apply)
        status_row.addWidget(btn_ignore)
        outer.addLayout(status_row)

        bb = QDialogButtonBox(QDialogButtonBox.Close)
        bb.rejected.connect(self.reject)
        outer.addWidget(bb)

    def _choose(self, status: str) -> None:
        self.chosen_status = status
        self.accept()
