"""Tela inicial: CTA circular à esquerda, perfis em grid e jogos à direita.

Layout:
- Topo esquerdo: branding HardwareOptimizer
- Centro esquerdo: botão circular "Analisar PC"
- Topo direito: "Selecione o perfil" + grid 3-col de cards de perfil
- Logo abaixo: GamesPanel (slide-down quando perfil = jogos)
- Rodapé: banners "Somente leitura" + "Pronto para análise"
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.ui.tokens import Color, Rounded, Spacing
from app.ui.widgets import CircularStartButton, GamesPanel, ProfilePicker


def _info_banner_qss(border: str) -> str:
    return (
        f"#InfoBanner{{background-color:{Color.SURFACE};"
        f"border:1px solid {border};border-radius:{Rounded.MD}px;}}"
    )


class StartScreen(QWidget):
    startRequested = Signal(str, list)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAccessibleName("Tela inicial")
        self.setAccessibleDescription(
            "Tela para escolher perfil, jogos e iniciar a análise do computador."
        )
        self.setStyleSheet(f"background-color:{Color.BACKGROUND};")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        outer.setSpacing(Spacing.MD)

        # Brand on top
        brand_row = QHBoxLayout()
        brand_row.setContentsMargins(0, 0, 0, 0)
        brand_row.setSpacing(Spacing.SM)
        brand = QLabel("HardwareOptimizer")
        brand.setStyleSheet(
            f"color:{Color.ON_SURFACE};font-size:20px;font-weight:800;"
            f"letter-spacing:0.5px;"
        )
        brand_row.addWidget(brand)
        brand_row.addStretch(1)
        outer.addLayout(brand_row)

        # Main content split
        body = QHBoxLayout()
        body.setSpacing(Spacing.LG)
        body.setContentsMargins(0, 0, 0, 0)
        body.addWidget(self._build_left(), 0)
        body.addWidget(self._build_right(), 1)
        outer.addLayout(body, 1)

        # Footer banners
        outer.addWidget(self._build_footer(), 0)

        self._on_profile_changed(self.profile_picker.selected_profile())

    # --- left: circular CTA ------------------------------------------------
    def _build_left(self) -> QWidget:
        wrapper = QWidget()
        wrapper.setMinimumWidth(300)
        wrapper.setMaximumWidth(380)
        wrapper.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.SM)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        layout.addStretch(1)

        btn_container = QWidget()
        btn_layout = QVBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setAlignment(Qt.AlignCenter)
        self.start_button = CircularStartButton()
        self.start_button.setToolTip("Iniciar análise (F5 ou Ctrl+R)")
        self.start_button.clicked.connect(self._on_start_clicked)
        btn_layout.addWidget(self.start_button, 0, Qt.AlignCenter)
        layout.addWidget(btn_container, 0, Qt.AlignHCenter)

        self.status_label = QLabel("Iniciar análise completa do sistema")
        self.status_label.setStyleSheet(
            f"color:{Color.MUTED};font-size:13px;font-weight:500;"
        )
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        layout.addStretch(2)
        return wrapper

    # --- right: profile + games -------------------------------------------
    def _build_right(self) -> QWidget:
        right = QFrame()
        right.setMinimumWidth(420)
        right.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(right)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.MD)

        self.profile_picker = ProfilePicker()
        self.profile_picker.profileChanged.connect(self._on_profile_changed)
        layout.addWidget(self.profile_picker, 0)

        self.games_panel = GamesPanel()
        layout.addWidget(self.games_panel, 0)

        layout.addStretch(1)
        return right

    # --- footer: info banners ---------------------------------------------
    def _build_footer(self) -> QWidget:
        footer = QWidget()
        layout = QVBoxLayout(footer)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.SM)

        # Read-only banner
        readonly = QFrame()
        readonly.setObjectName("InfoBanner")
        readonly.setStyleSheet(_info_banner_qss(Color.BORDER))
        ro_l = QHBoxLayout(readonly)
        ro_l.setContentsMargins(Spacing.MD, Spacing.SM, Spacing.MD, Spacing.SM)
        ro_l.setSpacing(Spacing.SM)
        ro_icon = QLabel("🔒")
        ro_icon.setStyleSheet(f"color:{Color.ACCENT};font-size:16px;background:transparent;")
        ro_l.addWidget(ro_icon)
        ro_text = QLabel(
            "<b>Somente leitura.</b> Nenhuma alteração automática.<br>"
            "<span style='color:" + Color.MUTED + ";font-size:12px;'>"
            "O HardwareOptimizer apenas analisa e sugere ajustes. "
            "Todas as mudanças são manuais.</span>"
        )
        ro_text.setStyleSheet(f"color:{Color.ON_SURFACE};font-size:13px;background:transparent;")
        ro_text.setWordWrap(True)
        ro_l.addWidget(ro_text, 1)
        layout.addWidget(readonly)

        # Status banner
        status = QFrame()
        status.setObjectName("InfoBanner")
        status.setStyleSheet(_info_banner_qss(Color.SUCCESS))
        st_l = QHBoxLayout(status)
        st_l.setContentsMargins(Spacing.MD, Spacing.SM, Spacing.MD, Spacing.SM)
        st_l.setSpacing(Spacing.SM)
        st_icon = QLabel("✓")
        st_icon.setFixedSize(20, 20)
        st_icon.setAlignment(Qt.AlignCenter)
        st_icon.setStyleSheet(
            f"background-color:{Color.SUCCESS};color:{Color.ON_PRIMARY};"
            f"border-radius:10px;font-weight:800;font-size:12px;"
        )
        st_l.addWidget(st_icon)
        st_text = QLabel(
            "<b>Pronto para análise.</b>"
            "<span style='color:" + Color.MUTED + ";font-size:12px;'>"
            "  Perfis e recomendações são armazenados localmente neste dispositivo.</span>"
        )
        st_text.setStyleSheet(f"color:{Color.ON_SURFACE};font-size:13px;background:transparent;")
        st_text.setWordWrap(True)
        st_l.addWidget(st_text, 1)
        layout.addWidget(status)

        return footer

    # --- handlers ----------------------------------------------------------
    def _on_profile_changed(self, key: str) -> None:
        self.games_panel.reveal(key == "games")

    def _on_start_clicked(self) -> None:
        if self.start_button.is_running():
            return
        profile = self.profile_picker.selected_profile()
        games = self.games_panel.selected_games() if profile == "games" else []
        self.startRequested.emit(profile, games)

    # --- public API used by MainWindow ------------------------------------
    def set_running(self, running: bool) -> None:
        self.start_button.set_running(running)
        self.start_button.setEnabled(not running)
        self.profile_picker.setEnabled(not running)
        self.games_panel.setEnabled(not running)

    def set_status(self, text: str) -> None:
        self.status_label.setText(text)

    def reset_status(self) -> None:
        self.status_label.setText("Iniciar análise completa do sistema")
