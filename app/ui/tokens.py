"""Tokens de design extraídos de DESIGN.md.

Mantém os valores exatos do design system para que widgets nativos do Qt
e folhas de estilo (QSS) consumam uma única fonte de verdade.
"""
from __future__ import annotations


class Color:
    BACKGROUND = "#0B1120"
    SURFACE = "#111827"
    SURFACE_ELEVATED = "#1F2937"
    ON_SURFACE = "#E5E7EB"
    MUTED = "#9CA3AF"
    BORDER = "#334155"
    PRIMARY = "#2563EB"
    PRIMARY_HOVER = "#3B82F6"
    PRIMARY_PRESSED = "#1D4ED8"
    ON_PRIMARY = "#FFFFFF"
    ACCENT = "#38BDF8"
    ON_ACCENT = "#082F49"
    SCAN_ACTIVE = "#38BDF8"
    SUCCESS = "#22C55E"
    WARNING = "#F59E0B"
    DANGER = "#EF4444"
    PROFILE_GAMING = "#8B5CF6"
    PROFILE_STABILITY = "#22C55E"
    PROFILE_POWER = "#F59E0B"
    OVERLAY = "rgba(2, 6, 23, 0.72)"


class Spacing:
    XS = 4
    SM = 8
    MD = 16
    LG = 24
    XL = 32
    XXL = 48


class Rounded:
    SM = 4
    MD = 8
    LG = 12
    XL = 16


class Motion:
    FAST_MS = 120
    NORMAL_MS = 180
    PULSE_MS = 1600


PROFILE_ACCENTS: dict[str, str] = {
    "games": Color.PROFILE_GAMING,
    "high_performance": Color.PROFILE_POWER,
    "stability": Color.PROFILE_STABILITY,
    "low_power": Color.PROFILE_POWER,
    "development": Color.ACCENT,
    "video_editing": Color.ACCENT,
    "general": Color.MUTED,
}
