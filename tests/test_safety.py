from app.safety import is_blocked_action, BLOCKED_ACTIONS


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
