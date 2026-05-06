from app.models.hardware import DriverInfo
from app.recommendations import generate_recommendations
from tests.fixtures import make_scan


def test_pending_reboot_triggers_high_priority_safe_recommendation():
    scan = make_scan(pending_reboot=True)
    recs = generate_recommendations(scan, "general")
    rec = next(r for r in recs if "Reiniciar" in r.title)
    assert rec.priority.value == "high"
    assert rec.risk.value == "safe"
    assert rec.manual_confirmation_required is False


def test_old_hotfix_triggers_windows_update_check():
    scan = make_scan(last_hotfix_age_days=90)
    recs = generate_recommendations(scan, "stability")
    rec = next(r for r in recs if "hotfix" in r.title.lower())
    assert rec.priority.value == "medium"
    assert "90" in rec.current_state


def test_available_windows_updates_trigger_recommendation():
    scan = make_scan(available_windows_updates=3)
    recs = generate_recommendations(scan, "general")
    rec = next(r for r in recs if "atualiza" in r.title.lower() and "3" in r.title)
    assert rec.priority.value == "high"
    assert rec.risk.value == "safe"


def test_outdated_drivers_trigger_manual_driver_recommendation():
    driver = DriverInfo(
        device_name="NVIDIA GeForce RTX 2060",
        provider="NVIDIA",
        version="456.71",
        driver_date="2020-10-07",
        age_days=2000,
        inf_name="oem42.inf",
    )
    scan = make_scan(outdated_drivers=[driver])
    recs = generate_recommendations(scan, "games", games=["cs2"])
    rec = next(r for r in recs if "drivers antigos" in r.title.lower())
    assert rec.priority.value == "high"
    assert rec.risk.value == "review"
    assert "NVIDIA GeForce RTX 2060" in rec.current_state
