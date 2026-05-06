"""Optional sensor collection via LibreHardwareMonitor.

LibreHardwareMonitor (LHM) exposes sensor data through the WMI namespace
``root\\LibreHardwareMonitor`` while it is running. This module queries that
namespace if available; otherwise it returns an empty dict. It never starts
LHM, never installs anything, and never asks for elevation — purely opportunistic
read-only sensor collection.
"""
from __future__ import annotations

import sys
from typing import Any


def collect_sensors(errors: list[str]) -> dict[str, Any]:
    if sys.platform != "win32":
        return {}
    sensors: dict[str, list[dict[str, Any]]] = {}
    try:
        import wmi  # type: ignore

        try:
            c = wmi.WMI(namespace=r"root\LibreHardwareMonitor")
        except Exception:
            return {}
        try:
            items = c.Sensor()
        except Exception:
            return {}
        for s in items:
            name = getattr(s, "Name", None) or "?"
            stype = getattr(s, "SensorType", None) or "?"
            value = getattr(s, "Value", None)
            parent = getattr(s, "Parent", None) or ""
            if value is None:
                continue
            try:
                v = float(value)
            except (TypeError, ValueError):
                continue
            sensors.setdefault(stype, []).append(
                {"name": str(name), "parent": str(parent), "value": v}
            )
    except Exception as exc:  # noqa: BLE001
        errors.append(f"sensors: {exc}")
    return sensors


def hottest_temperature(sensors: dict[str, Any]) -> tuple[str, float] | None:
    temps = sensors.get("Temperature") if isinstance(sensors, dict) else None
    if not temps:
        return None
    best = max(temps, key=lambda t: t.get("value", -1))
    return best.get("name", "?"), float(best.get("value", 0.0))
