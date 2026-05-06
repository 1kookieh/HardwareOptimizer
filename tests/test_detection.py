from app.recommendations import generate_recommendations
from tests.fixtures import make_scan


def test_xmp_active_state_appears_in_recommendation():
    scan = make_scan(ram_xmp_active=True, ram_speed_mhz=6000)
    recs = generate_recommendations(scan, "games", games=["valorant"])
    xmp = next(r for r in recs if "XMP" in r.title)
    assert "Provavelmente ativo" in xmp.current_state
    assert "6000" in xmp.current_state


def test_xmp_inactive_state_appears_in_recommendation():
    scan = make_scan(ram_xmp_active=False, ram_speed_mhz=2400)
    recs = generate_recommendations(scan, "games", games=["valorant"])
    xmp = next(r for r in recs if "XMP" in r.title)
    assert "Provavelmente inativo" in xmp.current_state
    assert "2400" in xmp.current_state


def test_rebar_enabled_drops_priority():
    enabled = make_scan(rebar_enabled=True)
    disabled = make_scan(rebar_enabled=False)
    rec_e = next(r for r in generate_recommendations(enabled, "games", games=["cs2"]) if "Resizable BAR" in r.title)
    rec_d = next(r for r in generate_recommendations(disabled, "games", games=["cs2"]) if "Resizable BAR" in r.title)
    assert rec_e.priority.value == "low"
    assert rec_d.priority.value == "medium"
    assert "Habilitado" in rec_e.current_state
    assert "Desabilitado" in rec_d.current_state


def test_sensors_collector_returns_dict_when_lhm_unavailable():
    from app.collectors.sensors import collect_sensors

    errs: list[str] = []
    out = collect_sensors(errs)
    assert isinstance(out, dict)


def test_device_guard_parser_detects_vbs_and_hvci():
    from app.collectors.system import _parse_device_guard

    vbs, hvci = _parse_device_guard("VBS=2\nServices=1,2")
    assert vbs is True
    assert hvci is True


def test_vendor_bios_setting_parser_filters_sensitive_names():
    from app.collectors.system import _parse_lenovo_bios_settings

    settings = _parse_lenovo_bios_settings([
        "SecureBoot,Enabled",
        "AssetTag,PRIVATE",
        "WakeOnLAN,Disabled",
    ])
    assert settings == {"SecureBoot": "Enabled", "WakeOnLAN": "Disabled"}


def test_scan_fixture_contains_exposed_bios_settings_and_sources():
    scan = make_scan()
    assert scan.bios.exposed_settings["SecureBoot"] == "Habilitado"
    assert "bios" in scan.detection_sources


def test_hvci_recommendation_is_risky_tradeoff_for_games():
    scan = make_scan(hvci_running="Habilitado", vbs_running="Habilitado")
    recs = generate_recommendations(scan, "games", games=["valorant"])
    rec = next(r for r in recs if "HVCI" in r.title)
    assert rec.risk.value == "risky"
    assert "Trade-off" in rec.safety_note


def test_fast_startup_recommendation_only_for_stability_profile():
    scan = make_scan(fast_startup="Habilitado")
    stability = generate_recommendations(scan, "stability")
    general = generate_recommendations(scan, "general")
    assert any("Rápida" in r.title or "Rápida" in r.title for r in stability)
    assert not any("Rápida" in r.title or "Rápida" in r.title for r in general)
