from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QResizeEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStatusBar,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.collectors import collect_full_scan
from app.models.hardware import FullScan
from app.models.profile import PROFILES, SUPPORTED_GAMES
from app.recommendations import generate_recommendations
from app.reports import build_report_dict, export_html, export_json
from app.storage import HistoryStore

from .theme import DARK_QSS, LIGHT_QSS


COMPACT_BREAKPOINT = 960


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

        self._build_ui()
        self._apply_theme()

    # ---------- layout ----------
    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        self._outer = QHBoxLayout(central)
        self._outer.setContentsMargins(12, 12, 12, 12)
        self._outer.setSpacing(12)

        self._sidebar = self._build_sidebar()
        self._main = self._build_main_area()

        self._outer.addWidget(self._sidebar, 0)
        self._outer.addWidget(self._main, 1)

        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Pronto.")

    def _build_sidebar(self) -> QWidget:
        side = QWidget()
        side.setObjectName("Sidebar")
        side.setFixedWidth(320)
        layout = QVBoxLayout(side)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header_row = QHBoxLayout()
        title = QLabel("HardwareOptimizer")
        title.setObjectName("Title")
        header_row.addWidget(title)
        header_row.addStretch(1)
        self.theme_btn = QToolButton()
        self.theme_btn.setText("☀")
        self.theme_btn.setToolTip("Alternar tema claro/escuro")
        self.theme_btn.clicked.connect(self._toggle_theme)
        header_row.addWidget(self.theme_btn)
        layout.addLayout(header_row)

        subtitle = QLabel("Análise local · Sem alterações automáticas no sistema")
        subtitle.setObjectName("Subtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        layout.addWidget(QLabel("Perfil de otimização"))
        self.profile_combo = QComboBox()
        for key, prof in PROFILES.items():
            self.profile_combo.addItem(prof.label, key)
        self.profile_combo.currentIndexChanged.connect(self._on_profile_changed)
        layout.addWidget(self.profile_combo)

        self.games_group = QGroupBox("Jogos (perfil 'Jogos')")
        gv = QVBoxLayout(self.games_group)
        self.game_checks: dict[str, QCheckBox] = {}
        for key, label in SUPPORTED_GAMES.items():
            cb = QCheckBox(label)
            cb.setEnabled(False)
            self.game_checks[key] = cb
            gv.addWidget(cb)
        layout.addWidget(self.games_group)

        self.scan_btn = QPushButton("Analisar computador")
        self.scan_btn.setObjectName("Primary")
        self.scan_btn.clicked.connect(self._on_scan_clicked)
        layout.addWidget(self.scan_btn)

        self.export_json_btn = QPushButton("Exportar relatório (JSON)")
        self.export_json_btn.setEnabled(False)
        self.export_json_btn.clicked.connect(lambda: self._on_export("json"))
        layout.addWidget(self.export_json_btn)

        self.export_html_btn = QPushButton("Exportar relatório (HTML)")
        self.export_html_btn.setEnabled(False)
        self.export_html_btn.clicked.connect(lambda: self._on_export("html"))
        layout.addWidget(self.export_html_btn)

        layout.addStretch(1)
        notice = QLabel(
            "A coleta é automática e somente leitura. Recomendações sensíveis "
            "(BIOS/UEFI, drivers, etc.) exigem ação manual do usuário."
        )
        notice.setObjectName("Subtitle")
        notice.setWordWrap(True)
        layout.addWidget(notice)
        return side

    def _build_main_area(self) -> QWidget:
        self.tabs = QTabWidget()

        self.dashboard = QTextEdit(readOnly=True)
        self.dashboard.setPlainText(
            "Bem-vindo ao HardwareOptimizer.\n\n"
            "1. Selecione um perfil.\n"
            "2. Se for 'Jogos', selecione os títulos.\n"
            "3. Clique em 'Analisar computador'. A coleta é automática.\n"
            "4. Revise as recomendações e marque-as como aplicadas/ignoradas.\n"
            "5. Exporte o relatório em JSON ou HTML.\n"
        )
        self.tabs.addTab(self.dashboard, "Dashboard")

        self.hardware_text = QTextEdit(readOnly=True)
        self.tabs.addTab(self.hardware_text, "Hardware")

        self.recs_table = self._make_rec_table()
        self.tabs.addTab(self.recs_table, "Recomendações")

        self.bios_table = self._make_rec_table()
        self.tabs.addTab(self.bios_table, "BIOS / UEFI")

        self.games_table = self._make_rec_table()
        self.tabs.addTab(self.games_table, "Jogos")

        self.updates_text = QTextEdit(readOnly=True)
        self.tabs.addTab(self.updates_text, "Atualizações")

        self.history_list = QListWidget()
        self.history_list.itemDoubleClicked.connect(self._on_history_open)
        self.tabs.addTab(self.history_list, "Histórico")
        self._refresh_history()

        return self.tabs

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

    # ---------- theme & layout responsiveness ----------
    def _apply_theme(self) -> None:
        self.setStyleSheet(DARK_QSS if self._dark else LIGHT_QSS)
        self.theme_btn.setText("☀" if self._dark else "🌙")

    def _toggle_theme(self) -> None:
        self._dark = not self._dark
        self._apply_theme()

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._update_compact(event.size().width())

    def _update_compact(self, width: int) -> None:
        compact = width < COMPACT_BREAKPOINT
        if compact == self._compact:
            return
        self._compact = compact
        if compact:
            self._sidebar.setFixedWidth(220)
            self.statusBar().showMessage("Modo compacto ativo.")
        else:
            self._sidebar.setFixedWidth(320)
            self.statusBar().showMessage("Pronto.")

    # ---------- scan ----------
    def _on_profile_changed(self) -> None:
        is_games = self.profile_combo.currentData() == "games"
        for cb in self.game_checks.values():
            cb.setEnabled(is_games)
            if not is_games:
                cb.setChecked(False)

    def _selected_games(self) -> list[str]:
        return [k for k, cb in self.game_checks.items() if cb.isChecked()]

    def _on_scan_clicked(self) -> None:
        self.scan_btn.setEnabled(False)
        self.scan_btn.setText("Analisando…")
        self.statusBar().showMessage("Coletando dados do sistema… (somente leitura)")
        try:
            scan = collect_full_scan()
            profile = self.profile_combo.currentData()
            games = self._selected_games()
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
            self.tabs.setCurrentIndex(2)
            self.statusBar().showMessage(
                f"Análise concluída. {len(recs)} recomendação(ões). "
                f"Avisos de coleta: {len(scan.collection_errors)}."
            )
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Erro na análise", str(exc))
        finally:
            self.scan_btn.setEnabled(True)
            self.scan_btn.setText("Analisar computador")

    # ---------- rendering ----------
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
            lines.append(f"{k}: {v}")

        lines += ["", "Atualizações", "-" * 40]
        for k, v in scan.updates.to_dict().items():
            if k == "outdated_drivers":
                continue
            lines.append(f"{k}: {v}")
        if scan.updates.outdated_drivers:
            lines.append("drivers_antigos:")
            for d in scan.updates.outdated_drivers[:10]:
                row = d if isinstance(d, dict) else d.to_dict()
                lines.append(
                    f"- {row.get('device_name')} | {row.get('provider')} | "
                    f"{row.get('version')} | {row.get('driver_date')}"
                )

        if scan.collection_errors:
            lines += ["", "Avisos de coleta (não bloqueantes)", "-" * 40]
            lines += [f"- {e}" for e in scan.collection_errors]

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
        lines.append(f"Drivers avaliados: {updates.drivers_total}")

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

        if not games:
            self.tabs.setTabText(4, "Jogos")
        else:
            labels = ", ".join(SUPPORTED_GAMES.get(g, g) for g in games)
            self.tabs.setTabText(4, f"Jogos ({labels[:30]}…)" if len(labels) > 30 else f"Jogos ({labels})")

    def _fill_table(self, table: QTableWidget, recs) -> None:
        table.setRowCount(len(recs))
        for row, rec in enumerate(recs):
            cells = [
                rec.title,
                rec.category.value,
                rec.priority.value,
                rec.risk.value,
                self._status_map.get(rec.title, "pending"),
                rec.expected_benefit,
            ]
            for col, val in enumerate(cells):
                item = QTableWidgetItem(str(val))
                item.setData(Qt.UserRole, rec)
                table.setItem(row, col, item)
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
                table.setItem(row, 4, QTableWidgetItem(self._status_map.get(rec.title, "pending")))

    # ---------- recommendation interactions ----------
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

    # ---------- export & history ----------
    def _on_export(self, fmt: str) -> None:
        if not self._scan:
            return
        profile = self.profile_combo.currentData()
        games = self._selected_games()
        report = build_report_dict(self._scan, profile, games, self._recommendations)
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
        for entry in self._store.list_scans():
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
            ("Confirmação manual", "Sim" if rec.manual_confirmation_required else "Não"),
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
