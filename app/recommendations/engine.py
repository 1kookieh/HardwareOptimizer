from __future__ import annotations

from app.models.hardware import FullScan
from app.models.profile import PROFILES
from app.models.recommendation import Priority, Recommendation
from app.safety import filter_safe_recommendations

from .bios import build_bios_recommendations
from .games import build_games_recommendations
from .rules import (
    build_drivers_recommendations,
    build_storage_recommendations,
    build_windows_recommendations,
)
from .updates import build_updates_recommendations


_PRIORITY_RANK = {
    Priority.CRITICAL: 0,
    Priority.HIGH: 1,
    Priority.MEDIUM: 2,
    Priority.LOW: 3,
}


def generate_recommendations(
    scan: FullScan,
    profile_key: str,
    games: list[str] | None = None,
) -> list[Recommendation]:
    if profile_key not in PROFILES:
        raise ValueError(f"Profile desconhecido: {profile_key}")
    games = games or []
    if profile_key != "games":
        games = []

    recs: list[Recommendation] = []
    recs.extend(build_bios_recommendations(scan, profile_key))
    recs.extend(build_updates_recommendations(scan, profile_key))
    recs.extend(build_windows_recommendations(scan, profile_key))
    recs.extend(build_drivers_recommendations(scan, profile_key))
    recs.extend(build_storage_recommendations(scan, profile_key))
    if profile_key == "games":
        recs.extend(build_games_recommendations(scan, games))

    profile = PROFILES[profile_key]
    cat_rank = {c: i for i, c in enumerate(profile.priority_categories)}
    recs.sort(
        key=lambda r: (
            _PRIORITY_RANK[r.priority],
            cat_rank.get(r.category.value, 99),
            r.title,
        )
    )
    safe_recs, violations = filter_safe_recommendations(recs)
    if violations:
        # Em caso de regra violada, registramos no scan para auditoria
        # mas mantemos a recomendação fora da lista entregue à UI/relatório.
        scan.collection_errors.extend(f"safety: {v}" for v in violations)
    return safe_recs
