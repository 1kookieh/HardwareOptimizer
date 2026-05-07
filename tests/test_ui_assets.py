"""Garante que os assets visuais locais da tela inicial existem."""
from pathlib import Path

from app.ui.widgets.icon_asset import ICON_ROOT


def test_start_screen_icon_assets_exist():
    expected = {
        "logo.svg",
        "profile-games.svg",
        "profile-development.svg",
        "profile-video.svg",
        "profile-general.svg",
        "profile-performance.svg",
        "profile-stability.svg",
        "profile-low-power.svg",
        "trust-local.svg",
        "trust-uac.svg",
        "trust-readonly.svg",
        "safe-check.svg",
        "game-valorant.svg",
        "game-league.svg",
        "game-warzone.svg",
        "game-marvel.svg",
        "game-fortnite.svg",
        "game-cs2.svg",
        "orbit-system.svg",
        "orbit-hardware.svg",
        "orbit-bios.svg",
        "orbit-updates.svg",
    }

    missing = [name for name in sorted(expected) if not (Path(ICON_ROOT) / name).exists()]
    assert not missing
