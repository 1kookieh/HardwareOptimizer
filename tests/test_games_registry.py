"""Cobertura básica do GamesRegistry: defaults, add/remove e persistência."""
from __future__ import annotations

from pathlib import Path

from app.models.profile import SUPPORTED_GAMES
from app.storage.games_registry import GamesRegistry


def test_defaults_are_listed_when_empty(tmp_path: Path) -> None:
    reg = GamesRegistry(tmp_path / "games.json")
    keys = [e.key for e in reg.entries()]
    assert keys == list(SUPPORTED_GAMES.keys())
    assert all(not e.custom for e in reg.entries())


def test_add_custom_persists_and_appears(tmp_path: Path) -> None:
    path = tmp_path / "games.json"
    reg = GamesRegistry(path)
    entry = reg.add_custom("Apex Legends", badge="APX")
    assert entry.custom is True
    assert entry.label == "Apex Legends"
    assert entry.badge == "APX"

    # Reabrir lê do disco
    reg2 = GamesRegistry(path)
    keys = [e.key for e in reg2.entries()]
    assert entry.key in keys
    assert path.exists()


def test_remove_default_hides_it(tmp_path: Path) -> None:
    reg = GamesRegistry(tmp_path / "games.json")
    reg.remove("valorant")
    keys = [e.key for e in reg.entries()]
    assert "valorant" not in keys


def test_remove_custom_drops_it(tmp_path: Path) -> None:
    reg = GamesRegistry(tmp_path / "games.json")
    entry = reg.add_custom("Dota 2")
    reg.remove(entry.key)
    keys = [e.key for e in reg.entries()]
    assert entry.key not in keys


def test_add_custom_rejects_empty_name(tmp_path: Path) -> None:
    reg = GamesRegistry(tmp_path / "games.json")
    try:
        reg.add_custom("   ")
    except ValueError:
        return
    raise AssertionError("ValueError esperado para nome vazio")
