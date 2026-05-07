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
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.storage import GamesRegistry
from app.ui.tokens import Color, Rounded, Spacing
from app.ui.widgets import (
    GamesPanel,
    ManageGamesDialog,
    ObjectiveSelector,
    OrbitalCircle,
    ProfilePicker,
    TrustBadgesColumn,
)


def _info_card_qss(border: str) -> str:
    return (
        f"#InfoCard{{background-color:{Color.SURFACE};"
        f"border:1px solid {border};border-radius:{Rounded.MD}px;}}"
    )


def _section_card_qss() -> str:
    return (
        f"#SectionCard{{background-color:{Color.SURFACE};"
        f"border:1px solid {Color.BORDER};"
        f"border-radius:{Rounded.LG}px;}}"
    )


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
        self.setStyleSheet(f"background-color:{Color.BACKGROUND};")

        self._registry = registry or GamesRegistry()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
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
        bar = QWidget()
        row = QHBoxLayout(bar)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(Spacing.SM)

        # Brand block: icon + name + subtitle
        brand_box = QHBoxLayout()
        brand_box.setSpacing(Spacing.SM)
        brand_icon = QLabel("⏻")
        brand_icon.setFixedSize(36, 36)
        brand_icon.setAlignment(Qt.AlignCenter)
        brand_icon.setStyleSheet(
            f"background-color:{Color.SURFACE_ELEVATED};"
            f"color:{Color.ACCENT};border-radius:{Rounded.SM}px;"
            f"font-size:18px;font-weight:800;"
        )
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

        self.settings_btn = QPushButton("⚙   Configurações")
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

        # Light/dark toggle visual (still triggers parent signal)
        self.theme_btn = QToolButton()
        self.theme_btn.setText("☀ / 🌙")
        self.theme_btn.setAccessibleName("Alternar tema")
        self.theme_btn.setCursor(Qt.PointingHandCursor)
        self.theme_btn.setStyleSheet(
            f"QToolButton{{color:{Color.ACCENT};background:transparent;"
            f"border:none;font-size:14px;padding:4px;}}"
        )
        self.theme_btn.clicked.connect(self.themeToggleRequested.emit)
        row.addWidget(self.theme_btn)

        return bar

    # --- left column: orbit + safety banner -------------------------------
    def _build_left(self) -> QWidget:
        wrapper = QFrame()
        wrapper.setObjectName("SectionCard")
        wrapper.setStyleSheet(_section_card_qss())
        wrapper.setMinimumWidth(440)
        wrapper.setMaximumWidth(520)
        wrapper.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        layout.setSpacing(Spacing.SM)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        title = QLabel("Inicie uma análise completa")
        title.setStyleSheet(
            f"color:{Color.ON_SURFACE};font-size:18px;font-weight:700;"
        )
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        sub = QLabel("Diagnóstico aprofundado do seu sistema")
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
        bicon = QLabel("🛡")
        bicon.setStyleSheet(
            f"color:{Color.ACCENT};font-size:18px;background:transparent;"
        )
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
        wrapper.setMinimumWidth(540)
        wrapper.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        layout.setSpacing(Spacing.MD)

        self.profile_picker = ProfilePicker()
        self.profile_picker.profileChanged.connect(self._on_profile_changed)
        layout.addWidget(self.profile_picker, 0)

        # Games block (revealed only for "games")
        self.games_block = QWidget()
        gb_layout = QVBoxLayout(self.games_block)
        gb_layout.setContentsMargins(0, 0, 0, 0)
        gb_layout.setSpacing(Spacing.MD)
        self.games_panel = GamesPanel(self._registry)
        self.games_panel.manageRequested.connect(self._on_manage_games)
        gb_layout.addWidget(self.games_panel)

        self.objective_selector = ObjectiveSelector()
        gb_layout.addWidget(self.objective_selector)
        layout.addWidget(self.games_block, 0)

        layout.addStretch(1)
        return wrapper

    # --- right column: trust badges --------------------------------------
    def _build_right(self) -> QWidget:
        wrapper = QWidget()
        wrapper.setMinimumWidth(200)
        wrapper.setMaximumWidth(220)
        wrapper.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(TrustBadgesColumn())
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

        return bar

    # --- handlers ----------------------------------------------------------
    def _on_profile_changed(self, key: str) -> None:
        is_games = key == "games"
        self.games_block.setVisible(is_games)

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
