"""Tela inicial: CTA circular animado à esquerda, configuração à direita.

Layout:
- Coluna esquerda: branding + botão circular + hint + status
- Coluna direita: ProfilePicker + GamesPanel (slide-down condicional)

A coluna direita tem largura mínima 360px para garantir que o seletor
de perfil sempre apareça mesmo em janelas estreitas. A esquerda fixa
em ~340px para dar espaço ao botão sem espremer a direita.
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

from app.ui.tokens import Color, Spacing
from app.ui.widgets import CircularStartButton, GamesPanel, ProfilePicker


class StartScreen(QWidget):
    startRequested = Signal(str, list)  # profile_key, games

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet(f"background-color:{Color.BACKGROUND};")

        outer = QHBoxLayout(self)
        outer.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        outer.setSpacing(Spacing.LG)

        outer.addWidget(self._build_left(), 0)
        outer.addWidget(self._build_right(), 1)

        # Sincroniza GamesPanel com o perfil default (signal só dispara
        # após esta conexão, então fazemos um nudge manual aqui).
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

        brand = QLabel("HardwareOptimizer")
        brand.setStyleSheet(
            f"color:{Color.ON_SURFACE};font-size:24px;font-weight:800;"
            f"letter-spacing:0.5px;"
        )
        brand.setAlignment(Qt.AlignCenter)
        layout.addWidget(brand)

        tagline = QLabel("Análise local · advisory-first · sem alterações automáticas")
        tagline.setStyleSheet(f"color:{Color.MUTED};font-size:12px;")
        tagline.setAlignment(Qt.AlignCenter)
        tagline.setWordWrap(True)
        layout.addWidget(tagline)

        layout.addSpacing(Spacing.LG)

        # Container fixo para o botão (mantém centralizado)
        btn_container = QWidget()
        btn_container.setFixedHeight(320)
        btn_layout = QVBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setAlignment(Qt.AlignCenter)
        self.start_button = CircularStartButton()
        self.start_button.setToolTip("Iniciar análise (F5 ou Ctrl+R)")
        self.start_button.clicked.connect(self._on_start_clicked)
        btn_layout.addWidget(self.start_button, 0, Qt.AlignCenter)
        layout.addWidget(btn_container, 0, Qt.AlignHCenter)

        hint = QLabel("Coleta automática · somente leitura")
        hint.setStyleSheet(
            f"color:{Color.ACCENT};font-size:11px;"
            f"letter-spacing:1.5px;text-transform:uppercase;"
        )
        hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint)

        layout.addSpacing(Spacing.SM)

        self.status_label = QLabel("Pronto para iniciar.")
        self.status_label.setStyleSheet(
            f"color:{Color.MUTED};font-size:13px;font-weight:500;"
        )
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        layout.addStretch(1)
        return wrapper

    # --- right: profile + games -------------------------------------------
    def _build_right(self) -> QWidget:
        right = QFrame()
        right.setMinimumWidth(320)
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
        self.status_label.setText("Pronto para iniciar.")
