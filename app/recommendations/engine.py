from __future__ import annotations

from app.logging_setup import get_logger
from app.models.hardware import FullScan
from app.models.profile import PROFILES
from app.models.recommendation import Priority, Recommendation
from app.safety import filter_safe_recommendations

from .bios import build_bios_recommendations
from .games import build_games_recommendations
from .quality_spec import quality_spec_detection_source, quality_spec_reference
from .rules import (
    build_drivers_recommendations,
    build_storage_recommendations,
    build_windows_recommendations,
)
from .updates import build_updates_recommendations

_log = get_logger("recommendations.engine")

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

    scan.detection_sources["recommendation_quality_spec"] = quality_spec_detection_source()
    spec_ref = quality_spec_reference()

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
            0 if r.evidence else 1,
            cat_rank.get(r.category.value, 99),
            r.title,
        )
    )
    safe_recs, violations = filter_safe_recommendations(recs)
    if violations:
        for violation in violations:
            _log.warning("safety guard removeu recomendação: %s", violation)
        scan.collection_errors.extend(f"safety: {violation}" for violation in violations)

    spec_id = spec_ref.sha256[:12] if spec_ref.exists else "ausente"
    _log.info(
        "engine gerou %d recomendação(ões) para perfil=%s, jogos=%s, spec=%s",
        len(safe_recs),
        profile_key,
        games,
        spec_id,
    )
    return safe_recs
