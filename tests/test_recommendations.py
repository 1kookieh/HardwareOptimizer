import pytest

from app.recommendations import generate_recommendations
from tests.fixtures import make_scan


def test_engine_returns_recommendations_for_each_profile():
    scan = make_scan()
    for profile in ["games", "development", "video_editing", "general",
                    "high_performance", "stability", "low_power"]:
        recs = generate_recommendations(scan, profile)
        assert recs, f"perfil {profile} sem recomendações"


def test_unknown_profile_raises():
    with pytest.raises(ValueError):
        generate_recommendations(make_scan(), "wrong")


def test_games_only_emit_when_profile_is_games():
    scan = make_scan()
    recs = generate_recommendations(scan, "general", games=["valorant"])
    assert all(r.category.value != "games" for r in recs)

    recs2 = generate_recommendations(scan, "games", games=["valorant", "cs2"])
    assert any(r.category.value == "games" for r in recs2)


def test_secure_boot_disabled_triggers_security_rec():
    scan = make_scan(secure_boot="Desabilitado")
    recs = generate_recommendations(scan, "games", games=["valorant"])
    titles = [r.title for r in recs]
    assert any("Secure Boot" in t for t in titles)


def test_low_ram_triggers_hardware_rec():
    scan = make_scan(ram_gb=8.0)
    recs = generate_recommendations(scan, "games", games=["valorant"])
    assert any("RAM" in r.title for r in recs)


def test_no_promise_of_exact_fps():
    scan = make_scan()
    recs = generate_recommendations(scan, "games", games=["valorant", "cs2"])
    for r in recs:
        text = " ".join([
            r.expected_benefit, r.expected_impact, r.rationale, r.recommended_state
        ]).lower()
        assert "+" not in r.expected_benefit or "fps" not in text or "exato" not in text
        assert "garantido" not in text
        assert "guaranteed" not in text


def test_bios_update_only_when_unknown_or_with_caution():
    scan = make_scan(motherboard_model="Não detectado automaticamente — requer confirmação manual.",
                     bios_version="Não detectado automaticamente — requer confirmação manual.")
    recs = generate_recommendations(scan, "general")
    bios_update = [r for r in recs if "Atualização" in r.title]
    assert bios_update
    assert bios_update[0].risk.value == "risky"
    assert bios_update[0].manual_confirmation_required is True


def test_recommendations_sorted_by_priority():
    scan = make_scan(secure_boot="Desabilitado", ram_gb=8.0)
    recs = generate_recommendations(scan, "games", games=["valorant"])
    rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    ranks = [rank[r.priority.value] for r in recs]
    assert ranks == sorted(ranks)


def test_missing_data_marked_as_manual():
    scan = make_scan()
    scan.bios.virtualization = "Não detectado automaticamente — requer confirmação manual."
    recs = generate_recommendations(scan, "development")
    for r in recs:
        if r.current_state.startswith("Não detectado"):
            assert r.manual_confirmation_required is True
