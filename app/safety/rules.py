"""Regras de segurança em profundidade.

Define ações que o app **nunca** executa nem recomenda como ação default,
e funções utilitárias para enforce-lar a regra na engine de recomendações.
"""
from __future__ import annotations

from typing import Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.recommendation import Recommendation


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


# Padrões textuais que sinalizam que uma recomendação está prometendo
# ganho exato/garantido de FPS — proibido pelas regras do projeto.
_FPS_PROMISE_PATTERNS = (
    "+fps garantido",
    "fps garantido",
    "ganho garantido de fps",
    "garante fps",
    "guaranteed fps",
)

# Padrões que sinalizam recomendação de downgrade de BIOS — proibido.
_BIOS_DOWNGRADE_PATTERNS = (
    "downgrade de bios",
    "fazer downgrade da bios",
    "voltar para uma versão anterior da bios",
    "bios downgrade",
)


def is_blocked_action(action: str) -> bool:
    """Retorna True se a ação está na lista de proibidas."""
    return action in BLOCKED_ACTIONS


def violates_safety_rules(rec: "Recommendation") -> str | None:
    """Retorna a regra violada, ou None se a recomendação está OK.

    Verifica conteúdo textual da recomendação contra padrões proibidos.
    Em caso de violação, devolve uma string com o motivo para auditoria.
    """
    haystack = " ".join(
        [
            rec.title,
            rec.expected_benefit,
            rec.expected_impact,
            rec.rationale,
            rec.recommended_state,
        ]
    ).lower()

    for pattern in _FPS_PROMISE_PATTERNS:
        if pattern in haystack:
            return f"violates: promise_exact_fps_gain ({pattern!r})"
    for pattern in _BIOS_DOWNGRADE_PATTERNS:
        if pattern in haystack:
            return f"violates: bios_downgrade ({pattern!r})"
    return None


def filter_safe_recommendations(
    recommendations: Iterable["Recommendation"],
) -> tuple[list["Recommendation"], list[str]]:
    """Devolve (lista_segura, lista_de_violações_detectadas)."""
    safe: list["Recommendation"] = []
    violations: list[str] = []
    for rec in recommendations:
        reason = violates_safety_rules(rec)
        if reason:
            violations.append(f"{rec.title} -> {reason}")
            continue
        safe.append(rec)
    return safe, violations
