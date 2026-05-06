from app.models.recommendation import Category, Priority, Recommendation, RiskLevel
from app.recommendations import generate_recommendations
from app.safety import (
    BLOCKED_ACTIONS,
    filter_safe_recommendations,
    is_blocked_action,
    violates_safety_rules,
)
from tests.fixtures import make_scan


def test_blocked_actions_include_critical_changes():
    for a in [
        "auto_apply_bios", "auto_overclock", "auto_undervolt",
        "auto_voltage_change", "auto_frequency_change",
        "auto_power_limit_change", "bios_downgrade",
    ]:
        assert is_blocked_action(a)


def test_unknown_action_not_blocked():
    assert not is_blocked_action("read_system_info")


def test_blocklist_immutable():
    assert isinstance(BLOCKED_ACTIONS, frozenset)


def _rec(**overrides) -> Recommendation:
    base = dict(
        title="x",
        category=Category.WINDOWS,
        priority=Priority.LOW,
        risk=RiskLevel.SAFE,
        rationale="r",
        expected_benefit="b",
        expected_impact="i",
    )
    base.update(overrides)
    return Recommendation(**base)


def test_violates_safety_detects_fps_promise():
    bad = _rec(expected_benefit="+30 FPS garantido em todos os jogos")
    assert violates_safety_rules(bad) is not None


def test_violates_safety_detects_bios_downgrade():
    bad = _rec(recommended_state="Fazer downgrade da BIOS para a versão anterior")
    assert violates_safety_rules(bad) is not None


def test_violates_safety_returns_none_for_safe_recommendation():
    ok = _rec(expected_benefit="Pode melhorar a estabilidade de FPS")
    assert violates_safety_rules(ok) is None


def test_filter_safe_recommendations_removes_violations():
    ok = _rec(title="ok", expected_benefit="Pode melhorar")
    bad = _rec(title="bad", expected_benefit="ganho garantido de fps em todos os jogos")
    safe, violations = filter_safe_recommendations([ok, bad])
    assert ok in safe
    assert bad not in safe
    assert any("bad" in v for v in violations)


def test_engine_filters_unsafe_recommendations(monkeypatch):
    """Garante que a engine não entrega uma recomendação proibida mesmo
    se um builder começar a emitir uma por engano."""
    from app.recommendations import engine as engine_module

    poison = _rec(
        title="ataque",
        expected_benefit="ganho garantido de FPS de 50%",
    )

    def evil_builder(scan, profile_key):
        return [poison]

    monkeypatch.setattr(engine_module, "build_windows_recommendations", evil_builder)

    scan = make_scan()
    recs = generate_recommendations(scan, "general")
    assert poison not in recs
    assert any("safety:" in e for e in scan.collection_errors)
