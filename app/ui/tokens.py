"""Tokens de design extraídos de DESIGN.md.

Mantém os valores ativos do design system para que widgets nativos do
Qt e folhas de estilo (QSS) consumam uma única fonte de verdade.

Suporta dois temas: ``dark`` (default) e ``light``. Use
:func:`apply_theme` para trocar globalmente — todos os atributos
de :class:`Color` são mutados in-place.
"""
from __future__ import annotations


class _DarkPalette:
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
    SHADOW = "rgba(0, 0, 0, 0.45)"


class _LightPalette:
    BACKGROUND = "#F1F5F9"
    SURFACE = "#FFFFFF"
    SURFACE_ELEVATED = "#F8FAFC"
    ON_SURFACE = "#0F172A"
    MUTED = "#64748B"
    BORDER = "#CBD5E1"
    PRIMARY = "#2563EB"
    PRIMARY_HOVER = "#1D4ED8"
    PRIMARY_PRESSED = "#1E40AF"
    ON_PRIMARY = "#FFFFFF"
    ACCENT = "#0284C7"
    ON_ACCENT = "#FFFFFF"
    SCAN_ACTIVE = "#0284C7"
    SUCCESS = "#16A34A"
    WARNING = "#D97706"
    DANGER = "#DC2626"
    PROFILE_GAMING = "#7C3AED"
    PROFILE_STABILITY = "#16A34A"
    PROFILE_POWER = "#D97706"
    OVERLAY = "rgba(15, 23, 42, 0.55)"
    SHADOW = "rgba(15, 23, 42, 0.18)"


class Color:
    """Tokens ativos. Mutados por :func:`apply_theme`."""
    BACKGROUND = _DarkPalette.BACKGROUND
    SURFACE = _DarkPalette.SURFACE
    SURFACE_ELEVATED = _DarkPalette.SURFACE_ELEVATED
    ON_SURFACE = _DarkPalette.ON_SURFACE
    MUTED = _DarkPalette.MUTED
    BORDER = _DarkPalette.BORDER
    PRIMARY = _DarkPalette.PRIMARY
    PRIMARY_HOVER = _DarkPalette.PRIMARY_HOVER
    PRIMARY_PRESSED = _DarkPalette.PRIMARY_PRESSED
    ON_PRIMARY = _DarkPalette.ON_PRIMARY
    ACCENT = _DarkPalette.ACCENT
    ON_ACCENT = _DarkPalette.ON_ACCENT
    SCAN_ACTIVE = _DarkPalette.SCAN_ACTIVE
    SUCCESS = _DarkPalette.SUCCESS
    WARNING = _DarkPalette.WARNING
    DANGER = _DarkPalette.DANGER
    PROFILE_GAMING = _DarkPalette.PROFILE_GAMING
    PROFILE_STABILITY = _DarkPalette.PROFILE_STABILITY
    PROFILE_POWER = _DarkPalette.PROFILE_POWER
    OVERLAY = _DarkPalette.OVERLAY
    SHADOW = _DarkPalette.SHADOW


_TOKEN_NAMES = [k for k in vars(_DarkPalette) if not k.startswith("_")]


def apply_theme(dark: bool) -> None:
    """Mutates :class:`Color` para refletir tema dark ou light."""
    src = _DarkPalette if dark else _LightPalette
    for name in _TOKEN_NAMES:
        setattr(Color, name, getattr(src, name))


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
    "games": "#8B5CF6",
    "high_performance": "#F59E0B",
    "stability": "#22C55E",
    "low_power": "#F59E0B",
    "development": "#0EA5E9",
    "video_editing": "#0EA5E9",
    "general": "#9CA3AF",
}
