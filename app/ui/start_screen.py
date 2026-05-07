"""Tela inicial: orbit + perfis + jogos + objetivo + badges de confiança.

Layout em 3 colunas (esquerda/centro/direita) acima de uma barra de
informação no rodapé. Botão "Configurações" no topo é placeholder por
enquanto. "Gerenciar lista" na seção de jogos abre diálogo persistido.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.models.profile import PROFILES
from app.storage import GamesRegistry
from app.ui.tokens import Color, Rounded, Spacing
from app.ui.widgets import (
    AssetIcon,
    GamesPanel,
    ManageGamesDialog,
    ObjectiveSelector,
    OrbitalCircle,
    ProfilePicker,
    TrustBadgesColumn,
)


def _info_card_qss(border: str) -> str:
    return (
        f"#InfoCard{{background-color:rgba(17,24,39,0.78);"
        f"border:1px solid {border};border-radius:{Rounded.LG}px;}}"
    )


def _section_card_qss(border: str | None = None) -> str:
    border_color = border or Color.BORDER
    return (
        f"#SectionCard{{"
        f"background:qlineargradient(x1:0, y1:0, x2:1, y2:1,"
        f"stop:0 rgba(15, 23, 42, 0.96),"
        f"stop:0.55 rgba(17, 24, 39, 0.90),"
        f"stop:1 rgba(8, 47, 73, 0.42));"
        f"border:1px solid {border_color};"
        f"border-radius:{Rounded.XL}px;}}"
    )


OBJECTIVE_LABELS = {
    "fps": "FPS",
    "input_lag": "Input lag",
    "stability": "Estabilidade",
    "balanced": "Balanceado",
}


class SessionSummaryPanel(QFrame):
    """Resumo visual da seleção atual na coluna direita."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("StartScreen")
        self.setObjectName("SectionCard")
        self.setStyleSheet(_section_card_qss())
        self.setAccessibleName("Resumo da sessão")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        layout.setSpacing(Spacing.MD)

        title = QLabel("Resumo da sessão")
        title.setStyleSheet(f"color:{Color.ON_SURFACE};font-size:16px;font-weight:800;")
        layout.addWidget(title)

        status = QLabel("●  Sessão pronta")
        status.setStyleSheet(f"color:{Color.SUCCESS};font-size:14px;font-weight:800;")
        layout.addWidget(status)

        hint = QLabel("Tudo pronto para iniciar sua análise.")
        hint.setStyleSheet(f"color:{Color.MUTED};font-size:12px;")
        layout.addWidget(hint)

        self.profile_row = self._meta_row("profile-games", "Perfil", "Jogos")
        self.games_row = self._meta_row("game-valorant", "Jogos", "Nenhum selecionado")
        self.objective_row = self._meta_row("orbit-system", "Objetivo", "FPS")
        layout.addWidget(self.profile_row)
        layout.addWidget(self.games_row)
        layout.addWidget(self.objective_row)

        layout.addStretch(1)

        self.safe_mark = AssetIcon("safe-check", fallback="✓", size=128)
        self.safe_mark.setFixedSize(128, 128)
        self.safe_mark.setAlignment(Qt.AlignCenter)
        self.safe_mark.setStyleSheet("background:transparent;border:none;")
        layout.addWidget(self.safe_mark, 0, Qt.AlignHCenter)

        safe_title = QLabel("Ambiente seguro")
        safe_title.setAlignment(Qt.AlignCenter)
        safe_title.setStyleSheet(f"color:{Color.SUCCESS};font-size:15px;font-weight:900;")
        layout.addWidget(safe_title)

        safe_sub = QLabel("Pronto para análise local")
        safe_sub.setAlignment(Qt.AlignCenter)
        safe_sub.setStyleSheet(f"color:{Color.MUTED};font-size:12px;")
        layout.addWidget(safe_sub)

    def _meta_row(self, icon: str, label: str, value: str) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.SM)
        icon_lbl = AssetIcon(icon, fallback="•", size=18)
        layout.addWidget(icon_lbl)
        label_lbl = QLabel(label)
        label_lbl.setStyleSheet(f"color:{Color.ON_SURFACE};font-size:12px;font-weight:700;")
        layout.addWidget(label_lbl)
        layout.addStretch(1)
        value_lbl = QLabel(value)
        value_lbl.setObjectName("SummaryValue")
        value_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        value_lbl.setStyleSheet(f"color:{Color.MUTED};font-size:12px;font-weight:700;")
        layout.addWidget(value_lbl)
        return row

    def update_values(self, profile: str, games: list[str], objective: str) -> None:
        profile_label = PROFILES.get(profile).label if profile in PROFILES else profile
        game_text = f"{len(games)} selecionado(s)" if games else "Nenhum selecionado"
        objective_label = OBJECTIVE_LABELS.get(objective, objective)
        self._set_value(self.profile_row, profile_label)
        self._set_value(self.games_row, game_text)
        self._set_value(self.objective_row, objective_label)

    @staticmethod
    def _set_value(row: QWidget, value: str) -> None:
        label = row.findChild(QLabel, "SummaryValue")
        if label is not None:
            label.setText(value)


class StartScreen(QWidget):
    startRequested = Signal(str, list)
    settingsRequested = Signal()
    themeToggleRequested = Signal()

    def __init__(self, registry: GamesRegistry | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setAccessibleName("Tela inicial")
        self.setAccessibleDescription(
            "Tela para escolher perfil, jogos, objetivo e iniciar a análise."
        )
        self.setStyleSheet(
            f"#StartScreen{{background-color:{Color.BACKGROUND};}}"
            "QLabel{background:transparent;}"
        )

        self._registry = registry or GamesRegistry()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(Spacing.LG, Spacing.MD, Spacing.LG, Spacing.MD)
        outer.setSpacing(Spacing.MD)

        outer.addWidget(self._build_top_bar(), 0)

        body = QHBoxLayout()
        body.setSpacing(Spacing.MD)
        body.setContentsMargins(0, 0, 0, 0)
        body.addWidget(self._build_left(), 0)
        body.addWidget(self._build_center(), 1)
        body.addWidget(self._build_right(), 0)
        outer.addLayout(body, 1)

        outer.addWidget(self._build_status_bar(), 0)

        self._on_profile_changed(self.profile_picker.selected_profile())

    # --- top bar -----------------------------------------------------------
    def _build_top_bar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("TopShell")
        bar.setFixedHeight(64)
        bar.setStyleSheet(
            f"#TopShell{{background-color:rgba(11,17,32,0.92);"
            f"border:1px solid rgba(51,65,85,0.45);"
            f"border-radius:{Rounded.LG}px;}}"
        )
        row = QHBoxLayout(bar)
        row.setContentsMargins(Spacing.MD, 0, Spacing.MD, 0)
        row.setSpacing(Spacing.MD)

        # Brand block: icon + name + subtitle
        brand_box = QHBoxLayout()
        brand_box.setSpacing(Spacing.SM)
        brand_icon = AssetIcon("logo", fallback="H", size=42)
        brand_icon.setFixedSize(42, 42)
        brand_icon.setAlignment(Qt.AlignCenter)
        brand_box.addWidget(brand_icon)

        title_box = QVBoxLayout()
        title_box.setContentsMargins(0, 0, 0, 0)
        title_box.setSpacing(0)
        brand = QLabel("HardwareOptimizer")
        brand.setStyleSheet(
            f"color:{Color.ON_SURFACE};font-size:18px;font-weight:800;"
            f"letter-spacing:0.5px;"
        )
        title_box.addWidget(brand)
        sub = QLabel("Análise local e segura do PC")
        sub.setStyleSheet(f"color:{Color.MUTED};font-size:11px;")
        title_box.addWidget(sub)
        brand_box.addLayout(title_box)
        row.addLayout(brand_box)
        row.addStretch(1)

        self.settings_btn = QPushButton("⚙  Configurações")
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        self.settings_btn.setAccessibleName("Configurações")
        self.settings_btn.setMinimumHeight(36)
        self.settings_btn.setStyleSheet(
            f"QPushButton{{background-color:{Color.SURFACE_ELEVATED};"
            f"color:{Color.ON_SURFACE};border:1px solid {Color.BORDER};"
            f"border-radius:{Rounded.MD}px;padding:8px 18px;font-size:13px;font-weight:600;}}"
            f"QPushButton:hover{{border-color:{Color.ACCENT};"
            f"background-color:{Color.SURFACE};}}"
        )
        self.settings_btn.clicked.connect(self._on_settings_clicked)
        row.addWidget(self.settings_btn)

        row.addSpacing(Spacing.SM)

        mode_label = QLabel("☼")
        mode_label.setFixedSize(36, 36)
        mode_label.setAlignment(Qt.AlignCenter)
        mode_label.setStyleSheet(
            f"background-color:{Color.SURFACE_ELEVATED};"
            f"border:1px solid {Color.BORDER};"
            f"border-radius:{Rounded.MD}px;color:{Color.ON_SURFACE};font-size:16px;"
        )
        row.addWidget(mode_label)

        self.theme_btn = QToolButton()
        self.theme_btn.setText("◑")
        self.theme_btn.setAccessibleName("Alternar tema")
        self.theme_btn.setCursor(Qt.PointingHandCursor)
        self.theme_btn.setStyleSheet(
            f"QToolButton{{color:{Color.ACCENT};background-color:{Color.SURFACE_ELEVATED};"
            f"border:1px solid {Color.BORDER};border-radius:{Rounded.MD}px;"
            f"font-size:16px;padding:8px;}}"
            f"QToolButton:hover{{border-color:{Color.ACCENT};}}"
        )
        self.theme_btn.clicked.connect(self.themeToggleRequested.emit)
        row.addWidget(self.theme_btn)

        row.addSpacing(Spacing.SM)
        for symbol in ("−", "□", "×"):
            ctrl = QLabel(symbol)
            ctrl.setFixedSize(32, 32)
            ctrl.setAlignment(Qt.AlignCenter)
            ctrl.setStyleSheet(f"color:{Color.MUTED};font-size:18px;font-weight:600;")
            row.addWidget(ctrl)

        return bar

    # --- left column: orbit + safety banner -------------------------------
    def _build_left(self) -> QWidget:
        wrapper = QFrame()
        wrapper.setObjectName("SectionCard")
        wrapper.setStyleSheet(_section_card_qss(Color.PRIMARY))
        wrapper.setMinimumWidth(390)
        wrapper.setMaximumWidth(430)
        wrapper.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        layout.setSpacing(Spacing.SM)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        badge = QLabel("◆  ANÁLISE LOCAL E SEGURA")
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet(f"color:{Color.ACCENT};font-size:12px;font-weight:900;")
        layout.addWidget(badge)

        title = QLabel("Análise completa do seu PC")
        title.setStyleSheet(
            f"color:{Color.ON_SURFACE};font-size:20px;font-weight:900;"
        )
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        sub = QLabel("Diagnóstico aprofundado e recomendações\n100% locais e seguras.")
        sub.setStyleSheet(f"color:{Color.MUTED};font-size:12px;")
        sub.setAlignment(Qt.AlignCenter)
        layout.addWidget(sub)

        layout.addSpacing(Spacing.SM)

        self.orbit = OrbitalCircle()
        self.start_button = self.orbit.button
        self.start_button.setToolTip("Iniciar análise (F5 ou Ctrl+R)")
        self.start_button.clicked.connect(self._on_start_clicked)
        layout.addWidget(self.orbit, 1, Qt.AlignHCenter)

        # Safety banner
        banner = QFrame()
        banner.setObjectName("InfoCard")
        banner.setStyleSheet(_info_card_qss(Color.BORDER))
        bl = QHBoxLayout(banner)
        bl.setContentsMargins(Spacing.MD, Spacing.SM, Spacing.MD, Spacing.SM)
        bl.setSpacing(Spacing.SM)
        bicon = AssetIcon("trust-readonly", fallback="▣", size=24)
        bl.addWidget(bicon)
        btext = QLabel(
            "<b>Somente leitura. Nenhuma alteração automática.</b><br>"
            f"<span style='color:{Color.MUTED};font-size:11px;'>"
            "O HardwareOptimizer apenas analisa e sugere ajustes seguros.</span>"
        )
        btext.setStyleSheet(f"color:{Color.ON_SURFACE};font-size:12px;background:transparent;")
        btext.setWordWrap(True)
        bl.addWidget(btext, 1)
        layout.addWidget(banner)
        return wrapper

    # --- center column: profile + games + objective ----------------------
    def _build_center(self) -> QWidget:
        wrapper = QFrame()
        wrapper.setObjectName("SectionCard")
        wrapper.setStyleSheet(_section_card_qss())
        wrapper.setMinimumWidth(600)
        wrapper.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        layout.setSpacing(Spacing.MD)

        self.profile_picker = ProfilePicker()
        self.profile_picker.profileChanged.connect(self._on_profile_changed)
        self.profile_picker.profileChanged.connect(lambda _key: self._update_session_summary())
        layout.addWidget(self.profile_picker, 0)

        # Games block (revealed only for "games")
        self.games_block = QWidget()
        gb_layout = QVBoxLayout(self.games_block)
        gb_layout.setContentsMargins(0, 0, 0, 0)
        gb_layout.setSpacing(Spacing.MD)
        self.games_panel = GamesPanel(self._registry)
        self.games_panel.manageRequested.connect(self._on_manage_games)
        self.games_panel.selectionChanged.connect(lambda _games: self._update_session_summary())
        gb_layout.addWidget(self.games_panel)

        self.objective_selector = ObjectiveSelector()
        self.objective_selector.objectiveChanged.connect(lambda _objective: self._update_session_summary())
        gb_layout.addWidget(self.objective_selector)
        layout.addWidget(self.games_block, 0)

        layout.addStretch(1)
        return wrapper

    # --- right column: trust badges --------------------------------------
    def _build_right(self) -> QWidget:
        wrapper = QWidget()
        wrapper.setMinimumWidth(280)
        wrapper.setMaximumWidth(330)
        wrapper.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        principles = QFrame()
        principles.setObjectName("SectionCard")
        principles.setStyleSheet(_section_card_qss())
        pl = QVBoxLayout(principles)
        pl.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        pl.setSpacing(Spacing.MD)
        title = QLabel("Princípios do HardwareOptimizer")
        title.setStyleSheet(f"color:{Color.ON_SURFACE};font-size:15px;font-weight:800;")
        title.setWordWrap(True)
        pl.addWidget(title)
        pl.addWidget(TrustBadgesColumn())
        layout.addWidget(principles)

        self.session_summary = SessionSummaryPanel()
        layout.addWidget(self.session_summary, 1)
        layout.addStretch(1)
        return wrapper

    # --- bottom status bar -----------------------------------------------
    def _build_status_bar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("InfoCard")
        bar.setStyleSheet(_info_card_qss(Color.BORDER))
        row = QHBoxLayout(bar)
        row.setContentsMargins(Spacing.MD, Spacing.SM, Spacing.MD, Spacing.SM)
        row.setSpacing(Spacing.SM)

        self.status_icon = QLabel("✓")
        self.status_icon.setFixedSize(22, 22)
        self.status_icon.setAlignment(Qt.AlignCenter)
        self.status_icon.setStyleSheet(
            f"background-color:{Color.SUCCESS};color:{Color.ON_PRIMARY};"
            f"border-radius:11px;font-weight:800;font-size:12px;"
        )
        row.addWidget(self.status_icon)

        self.status_label = QLabel(
            "<b>Pronto para análise.</b>  "
            f"<span style='color:{Color.MUTED};font-size:12px;'>"
            "Selecione um perfil e clique em 'Analisar PC' para começar.</span>"
        )
        self.status_label.setStyleSheet(
            f"color:{Color.ON_SURFACE};font-size:13px;background:transparent;"
        )
        self.status_label.setWordWrap(True)
        row.addWidget(self.status_label, 1)

        local = QLabel("⬟  Análise 100% local")
        local.setStyleSheet(f"color:{Color.MUTED};font-size:12px;font-weight:700;")
        row.addWidget(local)

        version = QLabel("Versão 1.0.0")
        version.setStyleSheet(f"color:{Color.MUTED};font-size:12px;font-weight:700;")
        row.addWidget(version)

        return bar

    # --- handlers ----------------------------------------------------------
    def _on_profile_changed(self, key: str) -> None:
        is_games = key == "games"
        self.games_block.setVisible(is_games)
        self._update_session_summary()

    def _on_start_clicked(self) -> None:
        if self.start_button.is_running():
            return
        profile = self.profile_picker.selected_profile()
        games = self.games_panel.selected_games() if profile == "games" else []
        self.startRequested.emit(profile, games)

    def _on_settings_clicked(self) -> None:
        self.settingsRequested.emit()

    def _on_manage_games(self) -> None:
        dlg = ManageGamesDialog(self._registry, self)
        if dlg.exec() == QDialog.Accepted:
            self.games_panel.refresh()
        else:
            # Mesmo se fechar via Close, o registry pode ter mudado
            self.games_panel.refresh()
        self._update_session_summary()

    def _update_session_summary(self) -> None:
        if not hasattr(self, "session_summary"):
            return
        profile = self.profile_picker.selected_profile()
        games = self.games_panel.selected_games() if profile == "games" else []
        objective = self.objective_selector.selected()
        self.session_summary.update_values(profile, games, objective)

    # --- public API used by MainWindow ------------------------------------
    def set_running(self, running: bool) -> None:
        self.start_button.set_running(running)
        self.start_button.setEnabled(True)
        self.profile_picker.setEnabled(not running)
        self.games_panel.setEnabled(not running)
        self.objective_selector.setEnabled(not running)
        if running:
            self.start_button.setToolTip("Passe o mouse e clique em PARAR para cancelar a análise.")
            self.orbit.reset_stages()
            self.status_label.setText(
                "<b>Coletando dados…</b>  "
                f"<span style='color:{Color.MUTED};font-size:12px;'>"
                "A análise é local e somente leitura.</span>"
            )
            self.status_icon.setStyleSheet(
                f"background-color:{Color.ACCENT};color:{Color.ON_PRIMARY};"
                f"border-radius:11px;font-weight:800;font-size:12px;"
            )
        else:
            self.start_button.setToolTip("Iniciar análise (F5 ou Ctrl+R)")
            self.reset_status()

    def update_stage(self, stage: str, state: str) -> None:
        self.orbit.set_stage(stage, state)

    def set_status(self, text: str) -> None:
        self.status_label.setText(text)

    def reset_status(self) -> None:
        self.status_icon.setStyleSheet(
            f"background-color:{Color.SUCCESS};color:{Color.ON_PRIMARY};"
            f"border-radius:11px;font-weight:800;font-size:12px;"
        )
        self.status_label.setText(
            "<b>Pronto para análise.</b>  "
            f"<span style='color:{Color.MUTED};font-size:12px;'>"
            "Selecione um perfil e clique em 'Analisar PC' para começar.</span>"
        )

    # Backwards compat (some tests reference these)
    def selected_objective(self) -> str:
        return self.objective_selector.selected()
