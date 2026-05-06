from __future__ import annotations

import datetime as _dt
import json
import subprocess
import sys
from typing import Any
from urllib.request import Request, urlopen

from app.models.hardware import UNDETECTED, BiosInfo, DriverInfo, HardwareInfo, UpdatesInfo


_REBOOT_REGISTRY_PATHS = [
    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending",
    r"SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired",
]

_DRIVER_CLASSES = {
    "display",
    "net",
    "media",
    "audioendpoint",
    "hdc",
    "scsiadapter",
    "system",
}

# Mapa vendor -> página oficial de suporte. Apenas fabricantes com URL
# canônica e estável. Quando o vendor não está aqui, bios_lookup_url
# permanece em UNDETECTED — não fazemos fallback para buscador externo
# para evitar vazar modelo da placa-mãe a terceiros.
_BIOS_VENDOR_SUPPORT_URLS: dict[str, str] = {
    "asus": "https://www.asus.com/support/",
    "asustek": "https://www.asus.com/support/",
    "asustek computer inc.": "https://www.asus.com/support/",
    "gigabyte": "https://www.gigabyte.com/Support",
    "gigabyte technology co., ltd.": "https://www.gigabyte.com/Support",
    "msi": "https://www.msi.com/support",
    "micro-star international co., ltd.": "https://www.msi.com/support",
    "asrock": "https://www.asrock.com/support/index.asp",
    "asrock inc.": "https://www.asrock.com/support/index.asp",
    "biostar": "https://www.biostar.com.tw/app/en/support/",
    "evga": "https://www.evga.com/support/download/",
    "nzxt": "https://nzxt.com/support",
    "supermicro": "https://www.supermicro.com/en/support",
    "lenovo": "https://support.lenovo.com/",
    "dell": "https://www.dell.com/support/home",
    "dell inc.": "https://www.dell.com/support/home",
    "hp": "https://support.hp.com/",
    "hewlett-packard": "https://support.hp.com/",
    "hewlett packard": "https://support.hp.com/",
    "hp inc.": "https://support.hp.com/",
    "acer": "https://www.acer.com/support",
    "asus_notebook": "https://www.asus.com/support/",
    "samsung": "https://www.samsung.com/support/",
    "lg": "https://www.lg.com/support",
    "intel": "https://www.intel.com/content/www/us/en/support/",
    "intel corporation": "https://www.intel.com/content/www/us/en/support/",
    "american megatrends": "https://www.ami.com/support/",
    "american megatrends inc.": "https://www.ami.com/support/",
    "phoenix technologies": "https://www.phoenix.com/support/",
    "insyde corp.": "https://www.insyde.com/support",
}


def collect_updates(errors: list[str]) -> UpdatesInfo:
    info = UpdatesInfo()
    if sys.platform != "win32":
        info.update_check_status = "Não executado fora do Windows."
        return info

    info.pending_reboot = _collect_pending_reboot(errors)
    _collect_last_hotfix(info, errors)
    _collect_available_windows_updates(info, errors)
    _collect_outdated_drivers(info, errors)
    return info


def enrich_online_update_sources(
    info: UpdatesInfo,
    hardware: HardwareInfo,
    bios: BiosInfo,
    errors: list[str],
) -> None:
    sources = [
        "https://www.catalog.update.microsoft.com/Home.aspx",
        "https://www.microsoft.com/software-download/windows11",
    ]
    gpu = (hardware.gpu_name or "").lower()
    if "nvidia" in gpu:
        sources.append("https://www.nvidia.com/Download/index.aspx")
        info.driver_lookup_urls["gpu"] = (
            "https://www.nvidia.com/Download/index.aspx?lang=en-us"
        )
    elif "amd" in gpu or "radeon" in gpu:
        sources.append("https://www.amd.com/en/support/download/drivers.html")
        info.driver_lookup_urls["gpu"] = (
            "https://www.amd.com/en/support/download/drivers.html"
        )
    elif "intel" in gpu:
        sources.append("https://www.intel.com/content/www/us/en/download-center/home.html")
        info.driver_lookup_urls["gpu"] = (
            "https://www.intel.com/content/www/us/en/download-center/home.html"
        )

    bios_url = _resolve_bios_support_url(hardware.motherboard_vendor, bios.vendor)
    if bios_url:
        info.bios_lookup_url = bios_url
        sources.append(bios_url)

    info.official_sources = sorted(set(sources))
    reachable = []
    for url in info.official_sources:
        if _url_reachable(url, errors):
            reachable.append(url)
    if reachable:
        info.online_check_status = f"{len(reachable)}/{len(info.official_sources)} fonte(s) oficial(is) acessível(is)."
    else:
        info.online_check_status = "Fontes oficiais não acessíveis nesta execução."


def _resolve_bios_support_url(*candidates: str | None) -> str | None:
    """Mapeia o nome do fabricante para a página oficial de suporte.

    Aceita o vendor da placa-mãe e o vendor da BIOS como candidatos.
    Faz match por substring para tolerar variações como
    ``ASUSTeK COMPUTER INC.`` ou ``Gigabyte Technology Co., Ltd.``.
    Retorna None quando nenhum vendor conhecido bate — neste caso o
    chamador mantém ``UNDETECTED`` em vez de cair em buscador externo.
    """
    for candidate in candidates:
        if not candidate:
            continue
        low = candidate.strip().lower()
        if not low:
            continue
        if low in _BIOS_VENDOR_SUPPORT_URLS:
            return _BIOS_VENDOR_SUPPORT_URLS[low]
        for key, url in _BIOS_VENDOR_SUPPORT_URLS.items():
            if key in low:
                return url
    return None


def _url_reachable(url: str, errors: list[str]) -> bool:
    try:
        req = Request(url, headers={"User-Agent": "HardwareOptimizer/1.0"})
        with urlopen(req, timeout=3) as response:
            return 200 <= int(response.status) < 400
    except Exception as exc:  # noqa: BLE001
        errors.append(f"online_source {url}: {exc}")
        return False


def _collect_pending_reboot(errors: list[str]) -> bool | None:
    try:
        import winreg

        for path in _REBOOT_REGISTRY_PATHS:
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                continue

        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Control\Session Manager",
            )
            try:
                winreg.QueryValueEx(key, "PendingFileRenameOperations")
                return True
            except FileNotFoundError:
                return False
            finally:
                winreg.CloseKey(key)
        except FileNotFoundError:
            return False
    except Exception as exc:  # noqa: BLE001
        errors.append(f"pending_reboot: {exc}")
        return None


def _collect_last_hotfix(info: UpdatesInfo, errors: list[str]) -> None:
    text = _run_powershell(
        "Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 1 "
        "HotFixID, InstalledOn | ConvertTo-Json -Compress",
        errors,
        "last_hotfix",
        timeout=15,
    )
    if not text:
        return
    try:
        data = json.loads(text)
        info.last_hotfix_id = str(data.get("HotFixID") or UNDETECTED)
        raw_date = data.get("InstalledOn")
        parsed = _parse_windows_date(raw_date)
        if parsed:
            info.last_hotfix_date = parsed.date().isoformat()
            info.last_hotfix_age_days = (_dt.datetime.now().date() - parsed.date()).days
        elif raw_date:
            info.last_hotfix_date = str(raw_date)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"last_hotfix_parse: {exc}")


def _collect_available_windows_updates(info: UpdatesInfo, errors: list[str]) -> None:
    text = _run_powershell(
        "$s = New-Object -ComObject Microsoft.Update.Session; "
        "$sr = $s.CreateUpdateSearcher(); "
        "$r = $sr.Search(\"IsInstalled=0 and Type='Software'\"); "
        "$r.Updates.Count",
        errors,
        "available_windows_updates",
        timeout=70,
    )
    if text is None:
        info.update_check_status = "Falhou ou indisponível."
        return
    try:
        info.available_windows_updates = int(text.strip().splitlines()[-1])
        info.update_check_status = "Concluído."
    except (TypeError, ValueError, IndexError) as exc:
        errors.append(f"available_windows_updates_parse: {exc}")
        info.update_check_status = "Resultado não interpretado."


def _collect_outdated_drivers(info: UpdatesInfo, errors: list[str]) -> None:
    text = _run_powershell(
        "Get-CimInstance Win32_PnPSignedDriver | "
        "Select-Object DeviceName, DriverProviderName, DriverVersion, DriverDate, InfName, DeviceClass | "
        "ConvertTo-Json -Compress -Depth 2",
        errors,
        "drivers",
        timeout=35,
    )
    if not text:
        return
    try:
        data = json.loads(text)
        rows = data if isinstance(data, list) else [data]
        info.drivers_total = len(rows)
        cutoff = _dt.datetime.now() - _dt.timedelta(days=365 * 3)
        outdated: list[DriverInfo] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            device_class = str(row.get("DeviceClass") or "").lower()
            if device_class and device_class not in _DRIVER_CLASSES:
                continue
            date = _parse_windows_date(row.get("DriverDate"))
            if date is None or date >= cutoff:
                continue
            driver = DriverInfo(
                device_name=str(row.get("DeviceName") or UNDETECTED),
                provider=str(row.get("DriverProviderName") or UNDETECTED),
                version=str(row.get("DriverVersion") or UNDETECTED),
                driver_date=date.date().isoformat(),
                age_days=(_dt.datetime.now().date() - date.date()).days,
                inf_name=str(row.get("InfName") or UNDETECTED),
            )
            outdated.append(driver)
        outdated.sort(key=lambda d: d.age_days or 0, reverse=True)
        info.outdated_drivers = outdated[:20]
    except Exception as exc:  # noqa: BLE001
        errors.append(f"drivers_parse: {exc}")


def _run_powershell(command: str, errors: list[str], label: str, timeout: int) -> str | None:
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        if out.returncode != 0 and out.stderr:
            errors.append(f"{label}: {out.stderr.strip()}")
        return (out.stdout or "").strip() or None
    except Exception as exc:  # noqa: BLE001
        errors.append(f"{label}: {exc}")
        return None


def _parse_windows_date(value: Any) -> _dt.datetime | None:
    if not value:
        return None
    if isinstance(value, str):
        text = value.strip()
        if text.startswith("/Date("):
            digits = "".join(ch for ch in text if ch.isdigit())
            if digits:
                return _dt.datetime.fromtimestamp(int(digits[:13]) / 1000)
        for fmt in ("%Y%m%d%H%M%S.%f%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%m/%d/%Y"):
            try:
                parsed = _dt.datetime.strptime(text[:26], fmt)
                return parsed.replace(tzinfo=None)
            except ValueError:
                continue
        try:
            return _dt.datetime.fromisoformat(text).replace(tzinfo=None)
        except ValueError:
            return None
    return None
