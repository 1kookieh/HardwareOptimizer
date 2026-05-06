from __future__ import annotations

import datetime as _dt
import ctypes
import platform
import re
import socket
import subprocess
import sys
from typing import Any

from app.models.hardware import (
    UNDETECTED,
    UNEXPOSED,
    BiosInfo,
    FullScan,
    HardwareInfo,
    MemoryModule,
    SystemInfo,
)

from .updates import collect_updates, enrich_online_update_sources
from .sensors import collect_sensors


def _safe(fn, errors: list[str], label: str, default: Any = None) -> Any:
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001
        errors.append(f"{label}: {exc}")
        return default


def _collect_system(errors: list[str]) -> SystemInfo:
    info = SystemInfo()
    info.os_name = _safe(platform.system, errors, "os_name", UNDETECTED) or UNDETECTED
    info.os_version = _safe(platform.version, errors, "os_version", UNDETECTED) or UNDETECTED
    info.os_build = _safe(platform.release, errors, "os_build", UNDETECTED) or UNDETECTED
    info.architecture = _safe(platform.machine, errors, "architecture", UNDETECTED) or UNDETECTED
    info.hostname = _safe(socket.gethostname, errors, "hostname", UNDETECTED) or UNDETECTED
    if sys.platform == "win32":
        info.power_plan = _collect_power_plan(errors)
    return info


def _collect_power_plan(errors: list[str]) -> str:
    try:
        out = subprocess.run(
            ["powercfg", "/getactivescheme"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        text = (out.stdout or "").strip()
        if "(" in text and ")" in text:
            return text.split("(", 1)[1].split(")", 1)[0].strip() or text
        return text or UNDETECTED
    except Exception as exc:  # noqa: BLE001
        errors.append(f"power_plan: {exc}")
        return UNDETECTED


def _collect_hardware(errors: list[str]) -> HardwareInfo:
    hw = HardwareInfo()
    try:
        import psutil  # type: ignore

        hw.cpu_cores = psutil.cpu_count(logical=False)
        hw.cpu_threads = psutil.cpu_count(logical=True)
        try:
            freq = psutil.cpu_freq()
            if freq:
                hw.cpu_freq_mhz = float(freq.current)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"cpu_freq: {exc}")
        vm = psutil.virtual_memory()
        hw.ram_total_gb = round(vm.total / (1024 ** 3), 2)
        hw.ram_used_gb = round(vm.used / (1024 ** 3), 2)
        for part in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(part.mountpoint)
                hw.storage.append(
                    {
                        "device": part.device,
                        "mountpoint": part.mountpoint,
                        "fstype": part.fstype,
                        "total_gb": round(usage.total / (1024 ** 3), 2),
                        "used_gb": round(usage.used / (1024 ** 3), 2),
                    }
                )
            except Exception:  # noqa: BLE001
                continue
    except Exception as exc:  # noqa: BLE001
        errors.append(f"psutil: {exc}")

    hw.cpu_name = _safe(platform.processor, errors, "cpu_name", UNDETECTED) or UNDETECTED

    if sys.platform == "win32":
        _collect_windows_hardware(hw, errors)
        _collect_memory_modules(hw, errors)
        _collect_rebar(hw, errors)
        hw.sensors = collect_sensors(errors)
    return hw


def _collect_windows_hardware(hw: HardwareInfo, errors: list[str]) -> None:
    try:
        import wmi  # type: ignore

        c = wmi.WMI()
        cpus = c.Win32_Processor()
        if cpus:
            name = getattr(cpus[0], "Name", None)
            if name:
                hw.cpu_name = str(name).strip()
        gpus = c.Win32_VideoController()
        if gpus:
            hw.gpu_name = str(getattr(gpus[0], "Name", UNDETECTED)).strip() or UNDETECTED
            drv = getattr(gpus[0], "DriverVersion", None)
            if drv:
                hw.gpu_driver_version = str(drv).strip()
            vram = getattr(gpus[0], "AdapterRAM", None)
            if vram:
                try:
                    hw.gpu_vram_gb = round(int(vram) / (1024 ** 3), 2)
                except (TypeError, ValueError):
                    pass
        boards = c.Win32_BaseBoard()
        if boards:
            hw.motherboard_vendor = str(getattr(boards[0], "Manufacturer", UNDETECTED)).strip() or UNDETECTED
            hw.motherboard_model = str(getattr(boards[0], "Product", UNDETECTED)).strip() or UNDETECTED
    except Exception as exc:  # noqa: BLE001
        errors.append(f"wmi_hardware: {exc}")


def _collect_memory_modules(hw: HardwareInfo, errors: list[str]) -> None:
    try:
        import wmi  # type: ignore

        c = wmi.WMI()
        modules: list[MemoryModule] = []
        for m in c.Win32_PhysicalMemory():
            mod = MemoryModule()
            mod.manufacturer = str(getattr(m, "Manufacturer", UNDETECTED) or UNDETECTED).strip() or UNDETECTED
            mod.part_number = str(getattr(m, "PartNumber", UNDETECTED) or UNDETECTED).strip() or UNDETECTED
            cap = getattr(m, "Capacity", None)
            if cap:
                try:
                    mod.capacity_gb = round(int(cap) / (1024 ** 3), 2)
                except (TypeError, ValueError):
                    pass
            cfg = getattr(m, "ConfiguredClockSpeed", None)
            if cfg:
                try:
                    mod.configured_clock_mhz = int(cfg)
                except (TypeError, ValueError):
                    pass
            speed = getattr(m, "Speed", None)
            if speed:
                try:
                    mod.rated_speed_mhz = int(speed)
                except (TypeError, ValueError):
                    pass
            ff = getattr(m, "FormFactor", None)
            mod.form_factor = {8: "DIMM", 12: "SO-DIMM"}.get(ff, str(ff) if ff is not None else UNDETECTED)
            modules.append(mod)
        hw.ram_modules = modules

        speeds = [m.configured_clock_mhz for m in modules if m.configured_clock_mhz]
        if speeds:
            top = max(speeds)
            hw.ram_xmp_active = top >= 3200
    except Exception as exc:  # noqa: BLE001
        errors.append(f"memory_modules: {exc}")


def _collect_rebar(hw: HardwareInfo, errors: list[str]) -> None:
    nv = _query_nvidia_rebar(errors)
    if nv is not None:
        hw.rebar_enabled = nv
        return

    text = _run_powershell(
        "(Get-PnpDevice -Class Display -Status OK | "
        "Get-PnpDeviceProperty -KeyName 'DEVPKEY_Device_LargeMemoryRangeAddressable' "
        "-ErrorAction SilentlyContinue).Data",
        errors,
        "rebar_pnp",
    )
    if text:
        low = text.strip().lower()
        if "true" in low:
            hw.rebar_enabled = True
        elif "false" in low:
            hw.rebar_enabled = False


def _query_nvidia_rebar(errors: list[str]) -> bool | None:
    try:
        out = subprocess.run(
            ["nvidia-smi", "-q"],
            capture_output=True,
            text=True,
            timeout=6,
            check=False,
        )
    except FileNotFoundError:
        return None
    except Exception as exc:  # noqa: BLE001
        errors.append(f"nvidia-smi: {exc}")
        return None
    text = out.stdout or ""
    m = re.search(r"Resizable BAR\s*:\s*(\w+)", text, re.IGNORECASE)
    if not m:
        return None
    return m.group(1).strip().lower() in {"yes", "enabled", "on", "true"}


def _collect_bios(errors: list[str]) -> BiosInfo:
    bios = BiosInfo()
    if sys.platform != "win32":
        return bios
    try:
        import wmi  # type: ignore

        c = wmi.WMI()
        bios_objs = c.Win32_BIOS()
        if bios_objs:
            b = bios_objs[0]
            bios.vendor = str(getattr(b, "Manufacturer", UNDETECTED)).strip() or UNDETECTED
            bios.version = str(getattr(b, "SMBIOSBIOSVersion", UNDETECTED)).strip() or UNDETECTED
            release = getattr(b, "ReleaseDate", None)
            if release:
                bios.release_date = str(release)[:8]
        secure = _query_secure_boot(errors)
        if secure is not None:
            bios.secure_boot = "Habilitado" if secure else "Desabilitado"
        tpm = _query_tpm(errors)
        if tpm is not None:
            bios.tpm = "Presente" if tpm else "Ausente"
        firmware = _query_firmware_type(errors)
        if firmware:
            bios.boot_mode = firmware
        try:
            virt_objs = c.Win32_Processor()
            if virt_objs:
                vt = getattr(virt_objs[0], "VirtualizationFirmwareEnabled", None)
                if vt is not None:
                    bios.virtualization = "Habilitado" if vt else "Desabilitado"
                vendor = getattr(virt_objs[0], "Manufacturer", None)
                if vendor:
                    bios.cpu_vendor = str(vendor).strip() or UNDETECTED
        except Exception as exc:  # noqa: BLE001
            errors.append(f"virtualization: {exc}")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"wmi_bios: {exc}")

    tpm_version = _query_tpm_version(errors)
    if tpm_version:
        bios.tpm_version = tpm_version

    hyper_v = _query_hyper_v_enabled(errors)
    if hyper_v is not None:
        bios.hyper_v_enabled = "Habilitado" if hyper_v else "Desabilitado"

    vbs, hvci = _query_device_guard(errors)
    if vbs is not None:
        bios.vbs_running = "Habilitado" if vbs else "Desabilitado"
    if hvci is not None:
        bios.hvci_running = "Habilitado" if hvci else "Desabilitado"

    storage_mode = _query_storage_mode(errors)
    if storage_mode:
        bios.storage_mode = storage_mode

    fast_startup = _query_fast_startup(errors)
    if fast_startup is not None:
        bios.fast_startup = "Habilitado" if fast_startup else "Desabilitado"

    hibernation = _query_hibernation(errors)
    if hibernation is not None:
        bios.hibernation = "Habilitado" if hibernation else "Desabilitado"
    bios.firmware_tables = _enumerate_firmware_tables(errors)
    bios.exposed_settings = _collect_exposed_bios_settings(errors)
    if bios.exposed_settings:
        bios.exposure_note = (
            "Configurações de BIOS expostas por interface WMI do fabricante foram lidas."
        )
    else:
        bios.exposure_note = UNEXPOSED
    return bios


def _run_powershell(command: str, errors: list[str], label: str) -> str | None:
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
        return (out.stdout or "").strip() or None
    except Exception as exc:  # noqa: BLE001
        errors.append(f"{label}: {exc}")
        return None


def _query_secure_boot(errors: list[str]) -> bool | None:
    text = _run_powershell("Confirm-SecureBootUEFI", errors, "secure_boot")
    if text is None:
        return None
    low = text.lower()
    if "true" in low:
        return True
    if "false" in low:
        return False
    return None


def _query_tpm(errors: list[str]) -> bool | None:
    text = _run_powershell("(Get-Tpm).TpmPresent", errors, "tpm")
    if text is None:
        return None
    low = text.lower()
    if "true" in low:
        return True
    if "false" in low:
        return False
    return None


def _query_tpm_version(errors: list[str]) -> str | None:
    text = _run_powershell(
        "$t = Get-CimInstance -Namespace root\\cimv2\\Security\\MicrosoftTpm "
        "-ClassName Win32_Tpm -ErrorAction SilentlyContinue; "
        "if ($t) { $t.SpecVersion } else { (Get-Tpm).ManufacturerVersionFull20 }",
        errors,
        "tpm_version",
    )
    if not text:
        return None
    low = text.lower()
    if "2.0" in low or "2," in low:
        return "2.0"
    if "1.2" in low or "1," in low:
        return "1.2"
    return text.strip() or None


def _query_hyper_v_enabled(errors: list[str]) -> bool | None:
    text = _run_powershell(
        "(Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All "
        "-ErrorAction SilentlyContinue).State",
        errors,
        "hyper_v",
    )
    if not text:
        return None
    low = text.lower()
    if "enabled" in low or "habilitado" in low:
        return True
    if "disabled" in low or "desabilitado" in low:
        return False
    return None


def _query_device_guard(errors: list[str]) -> tuple[bool | None, bool | None]:
    text = _run_powershell(
        "$d = Get-CimInstance -Namespace root\\Microsoft\\Windows\\DeviceGuard "
        "-ClassName Win32_DeviceGuard -ErrorAction SilentlyContinue; "
        "if ($d) { "
        "Write-Output ('VBS=' + $d.VirtualizationBasedSecurityStatus); "
        "Write-Output ('Services=' + (($d.SecurityServicesRunning) -join ',')) "
        "}",
        errors,
        "device_guard",
    )
    return _parse_device_guard(text or "")


def _parse_device_guard(text: str) -> tuple[bool | None, bool | None]:
    vbs: bool | None = None
    hvci: bool | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("VBS="):
            value = line.split("=", 1)[1].strip()
            if value.isdigit():
                vbs = int(value) == 2
        elif line.startswith("Services="):
            services = {x.strip() for x in line.split("=", 1)[1].split(",") if x.strip()}
            hvci = "2" in services
    return vbs, hvci


def _query_storage_mode(errors: list[str]) -> str | None:
    text = _run_powershell(
        "$ahci = (Get-ItemProperty -Path "
        "'HKLM:\\SYSTEM\\CurrentControlSet\\Services\\storahci' "
        "-Name Start -ErrorAction SilentlyContinue).Start; "
        "$raid = (Get-CimInstance Win32_IDEController -ErrorAction SilentlyContinue | "
        "Select-Object -ExpandProperty Name) -join '; '; "
        "Write-Output ('storahci=' + $ahci); Write-Output ('controllers=' + $raid)",
        errors,
        "storage_mode",
    )
    if not text:
        return None
    low = text.lower()
    if "raid" in low:
        return "RAID"
    if "storahci=0" in low or "ahci" in low:
        return "AHCI"
    return None


def _query_fast_startup(errors: list[str]) -> bool | None:
    text = _run_powershell(
        "(Get-ItemProperty -Path "
        "'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Power' "
        "-Name HiberbootEnabled -ErrorAction SilentlyContinue).HiberbootEnabled",
        errors,
        "fast_startup",
    )
    if text is None:
        return None
    if text.strip() == "1":
        return True
    if text.strip() == "0":
        return False
    return None


def _query_hibernation(errors: list[str]) -> bool | None:
    text = _run_powershell("powercfg /a", errors, "hibernation")
    if not text:
        return None
    low = text.lower()
    if "hibernate has not been enabled" in low or "hiberna" in low and "não foi habilit" in low:
        return False
    if "hibernation" in low or "hiberna" in low:
        return True
    return None


def _enumerate_firmware_tables(errors: list[str]) -> list[str]:
    try:
        providers = {"RSMB": "Raw SMBIOS", "ACPI": "ACPI", "FIRM": "Firmware"}
        found: list[str] = []
        for provider, label in providers.items():
            sig = int.from_bytes(provider.encode("ascii"), "little")
            size = ctypes.windll.kernel32.EnumSystemFirmwareTables(sig, None, 0)
            if size:
                found.append(label)
        return found
    except Exception as exc:  # noqa: BLE001
        errors.append(f"firmware_tables: {exc}")
        return []


def _collect_exposed_bios_settings(errors: list[str]) -> dict[str, str]:
    settings: dict[str, str] = {}
    for fn, label in [
        (_collect_lenovo_bios_settings, "lenovo_bios_settings"),
        (_collect_hp_bios_settings, "hp_bios_settings"),
        (_collect_dell_bios_settings, "dell_bios_settings"),
    ]:
        try:
            settings.update(fn())
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{label}: {exc}")
    return settings


def _collect_lenovo_bios_settings() -> dict[str, str]:
    try:
        import wmi  # type: ignore

        c = wmi.WMI(namespace="root\\wmi")
        rows = getattr(c, "Lenovo_BiosSetting", lambda: [])()
        return _parse_lenovo_bios_settings(
            str(getattr(row, "CurrentSetting", "") or "") for row in rows
        )
    except Exception:
        return {}


def _parse_lenovo_bios_settings(rows) -> dict[str, str]:
    settings: dict[str, str] = {}
    for raw in rows:
        if not raw or "," not in raw:
            continue
        name, value = raw.split(",", 1)
        name = _safe_setting_name(name)
        value = value.strip()
        if name and value:
            settings[name] = value
    return settings


def _collect_hp_bios_settings() -> dict[str, str]:
    try:
        import wmi  # type: ignore

        c = wmi.WMI(namespace="root\\hp\\instrumentedBIOS")
        rows = getattr(c, "HP_BIOSEnumeration", lambda: [])()
        out: dict[str, str] = {}
        for row in rows:
            name = _safe_setting_name(str(getattr(row, "Name", "") or ""))
            value = str(getattr(row, "CurrentValue", "") or "").strip()
            if name and value:
                out[name] = value
        return out
    except Exception:
        return {}


def _collect_dell_bios_settings() -> dict[str, str]:
    try:
        import wmi  # type: ignore

        c = wmi.WMI(namespace="root\\dcim\\sysman")
        rows = []
        for class_name in ("DCIM_BIOSEnumeration", "DCIM_BIOSInteger", "DCIM_BIOSString"):
            rows.extend(getattr(c, class_name, lambda: [])())
        out: dict[str, str] = {}
        for row in rows:
            name = _safe_setting_name(str(getattr(row, "AttributeName", "") or ""))
            value = str(
                getattr(row, "CurrentValue", "") or getattr(row, "CurrentValueName", "") or ""
            ).strip()
            if name and value:
                out[name] = value
        return out
    except Exception:
        return {}


def _safe_setting_name(value: str) -> str:
    name = value.strip()
    blocked = {"serial", "uuid", "asset", "tag", "password", "token", "key"}
    low = name.lower()
    if any(part in low for part in blocked):
        return ""
    return name


def _query_firmware_type(errors: list[str]) -> str | None:
    text = _run_powershell(
        "(Get-ComputerInfo -Property BiosFirmwareType).BiosFirmwareType",
        errors,
        "firmware_type",
    )
    if not text:
        return None
    cleaned = text.strip()
    if cleaned.lower() in {"uefi", "bios", "legacy"}:
        return cleaned
    return cleaned or None


def collect_full_scan() -> FullScan:
    """Run a full automatic read-only snapshot of the machine.

    No user prompts, no UAC elevation, no interactive confirmations. Failures
    are recorded in ``collection_errors``. Firmware settings that the vendor
    does not expose are marked as not exposed instead of guessed.
    """
    errors: list[str] = []
    system = _collect_system(errors)
    hardware = _collect_hardware(errors)
    bios = _collect_bios(errors)
    updates = collect_updates(errors)
    enrich_online_update_sources(updates, hardware, bios, errors)
    scan = FullScan(
        system=system,
        hardware=hardware,
        bios=bios,
        updates=updates,
        collected_at=_dt.datetime.now().isoformat(timespec="seconds"),
        collection_errors=errors,
        detection_sources={
            "system": ["platform", "socket", "powercfg"],
            "hardware": ["psutil", "WMI Win32_*", "nvidia-smi quando disponível"],
            "bios": [
                "WMI Win32_BIOS",
                "Confirm-SecureBootUEFI",
                "Get-Tpm",
                "DeviceGuard WMI",
                "vendor BIOS WMI quando exposto",
            ],
            "updates": [
                "registro Windows",
                "Get-HotFix",
                "Microsoft.Update.Session",
                "Win32_PnPSignedDriver",
                "fontes oficiais online quando acessíveis",
            ],
        },
    )
    return scan
