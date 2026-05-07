"""Registro de jogos suportados, com defaults + entradas custom do usuário.

Os defaults vêm de :data:`app.models.profile.SUPPORTED_GAMES` e ficam
sempre disponíveis. O usuário pode:

- adicionar jogos customizados (nome livre + sigla curta);
- remover (esconder) qualquer jogo, default ou custom.

Persistência: ``%LOCALAPPDATA%/HardwareOptimizer/games.json`` (ou
``~/.local/share/HardwareOptimizer/games.json`` fora do Windows).
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

from app.logging_setup import get_logger
from app.models.profile import SUPPORTED_GAMES

_log = get_logger("storage.games")


def _registry_path() -> Path:
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~/.local/share")
    folder = Path(base) / "HardwareOptimizer"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / "games.json"


@dataclass(frozen=True)
class GameEntry:
    key: str
    label: str
    badge: str
    custom: bool


def _slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return s or "game"


def _short_badge(label: str) -> str:
    parts = [p for p in re.split(r"\s+", label.strip()) if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:3].upper()
    return (parts[0][0] + parts[1][0]).upper()


class GamesRegistry:
    """Mantém a lista efetiva de jogos exibidos para seleção."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or _registry_path()
        self._custom: dict[str, dict[str, str]] = {}
        self._hidden: set[str] = set()
        self._load()

    # ----------------------------------------------------------- persistence
    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            self._custom = {
                k: {"label": v.get("label", k), "badge": v.get("badge", _short_badge(k))}
                for k, v in (data.get("custom") or {}).items()
            }
            self._hidden = set(data.get("hidden") or [])
        except (OSError, json.JSONDecodeError) as exc:
            _log.warning("falha ao ler games.json: %s", exc)

    def _save(self) -> None:
        try:
            payload = {
                "custom": self._custom,
                "hidden": sorted(self._hidden),
            }
            self._path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError as exc:
            _log.warning("falha ao salvar games.json: %s", exc)

    # ----------------------------------------------------------------- API
    def entries(self) -> list[GameEntry]:
        result: list[GameEntry] = []
        for key, label in SUPPORTED_GAMES.items():
            if key in self._hidden:
                continue
            result.append(
                GameEntry(key=key, label=label, badge=_short_badge(label), custom=False)
            )
        for key, info in self._custom.items():
            if key in self._hidden:
                continue
            result.append(
                GameEntry(
                    key=key,
                    label=info["label"],
                    badge=info.get("badge") or _short_badge(info["label"]),
                    custom=True,
                )
            )
        return result

    def add_custom(self, label: str, badge: str | None = None) -> GameEntry:
        label = label.strip()
        if not label:
            raise ValueError("nome do jogo é obrigatório")
        key = _slug(label)
        # Avoid collisions with defaults and existing custom
        original = key
        counter = 2
        while key in SUPPORTED_GAMES or key in self._custom:
            key = f"{original}_{counter}"
            counter += 1
        badge_value = (badge or _short_badge(label)).strip()[:4].upper() or _short_badge(label)
        self._custom[key] = {"label": label, "badge": badge_value}
        self._hidden.discard(key)
        self._save()
        return GameEntry(key=key, label=label, badge=badge_value, custom=True)

    def remove(self, key: str) -> None:
        if key in self._custom:
            del self._custom[key]
            self._hidden.discard(key)
        else:
            self._hidden.add(key)
        self._save()
