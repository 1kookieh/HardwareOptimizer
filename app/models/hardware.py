from dataclasses import asdict, dataclass, field
from typing import Any, Optional

UNDETECTED = "Não detectado automaticamente."
UNEXPOSED = "Não exposto pelo firmware ou pelo sistema operacional."


@dataclass
class BiosInfo:
    vendor: str = UNDETECTED
    version: str = UNDETECTED
    release_date: str = UNDETECTED
    secure_boot: str = UNDETECTED
    tpm: str = UNDETECTED
    tpm_version: str = UNDETECTED
    virtualization: str = UNDETECTED
    boot_mode: str = UNDETECTED
    hyper_v_enabled: str = UNDETECTED
    vbs_running: str = UNDETECTED
    hvci_running: str = UNDETECTED
    storage_mode: str = UNDETECTED
    fast_startup: str = UNDETECTED
    hibernation: str = UNDETECTED
    cpu_vendor: str = UNDETECTED
    firmware_tables: list[str] = field(default_factory=list)
    exposed_settings: dict[str, str] = field(default_factory=dict)
    exposure_note: str = UNEXPOSED

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MemoryModule:
    manufacturer: str = UNDETECTED
    part_number: str = UNDETECTED
    capacity_gb: Optional[float] = None
    configured_clock_mhz: Optional[int] = None
    rated_speed_mhz: Optional[int] = None
    form_factor: str = UNDETECTED

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DriverInfo:
    device_name: str = UNDETECTED
    provider: str = UNDETECTED
    version: str = UNDETECTED
    driver_date: str = UNDETECTED
    age_days: Optional[int] = None
    inf_name: str = UNDETECTED

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HardwareInfo:
    cpu_name: str = UNDETECTED
    cpu_cores: Optional[int] = None
    cpu_threads: Optional[int] = None
    cpu_freq_mhz: Optional[float] = None
    ram_total_gb: Optional[float] = None
    ram_used_gb: Optional[float] = None
    ram_modules: list[MemoryModule] = field(default_factory=list)
    ram_xmp_active: Optional[bool] = None
    gpu_name: str = UNDETECTED
    gpu_driver_version: str = UNDETECTED
    gpu_driver_date: str = UNDETECTED
    gpu_vram_gb: Optional[float] = None
    rebar_enabled: Optional[bool] = None
    motherboard_vendor: str = UNDETECTED
    motherboard_model: str = UNDETECTED
    storage: list[dict[str, Any]] = field(default_factory=list)
    sensors: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["ram_modules"] = [
            m if isinstance(m, dict) else m.to_dict() for m in d["ram_modules"]
        ]
        return d


@dataclass
class SystemInfo:
    os_name: str = UNDETECTED
    os_version: str = UNDETECTED
    os_build: str = UNDETECTED
    architecture: str = UNDETECTED
    hostname: str = UNDETECTED
    power_plan: str = UNDETECTED

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class UpdatesInfo:
    pending_reboot: Optional[bool] = None
    last_hotfix_id: str = UNDETECTED
    last_hotfix_date: str = UNDETECTED
    last_hotfix_age_days: Optional[int] = None
    available_windows_updates: Optional[int] = None
    update_check_status: str = UNDETECTED
    outdated_drivers: list[DriverInfo] = field(default_factory=list)
    drivers_total: Optional[int] = None
    online_check_status: str = UNDETECTED
    official_sources: list[str] = field(default_factory=list)
    driver_lookup_urls: dict[str, str] = field(default_factory=dict)
    bios_lookup_url: str = UNDETECTED

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["outdated_drivers"] = [
            x if isinstance(x, dict) else x.to_dict() for x in d["outdated_drivers"]
        ]
        return d


@dataclass
class FullScan:
    system: SystemInfo = field(default_factory=SystemInfo)
    hardware: HardwareInfo = field(default_factory=HardwareInfo)
    bios: BiosInfo = field(default_factory=BiosInfo)
    updates: UpdatesInfo = field(default_factory=UpdatesInfo)
    collected_at: str = ""
    collection_errors: list[str] = field(default_factory=list)
    detection_sources: dict[str, list[str]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "system": self.system.to_dict(),
            "hardware": self.hardware.to_dict(),
            "bios": self.bios.to_dict(),
            "updates": self.updates.to_dict(),
            "collected_at": self.collected_at,
            "collection_errors": list(self.collection_errors),
            "detection_sources": {
                key: list(values) for key, values in self.detection_sources.items()
            },
        }
