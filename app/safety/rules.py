BLOCKED_ACTIONS: frozenset[str] = frozenset(
    {
        "auto_apply_bios",
        "auto_overclock",
        "auto_undervolt",
        "auto_voltage_change",
        "auto_frequency_change",
        "auto_power_limit_change",
        "auto_registry_edit",
        "auto_driver_install",
        "disable_secure_boot_default",
        "disable_tpm_default",
        "disable_firewall_default",
        "disable_antivirus_default",
        "bios_downgrade",
        "promise_exact_fps_gain",
    }
)


def is_blocked_action(action: str) -> bool:
    return action in BLOCKED_ACTIONS
