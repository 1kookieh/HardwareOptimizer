"""Helper único para invocar PowerShell em modo não interativo.

Centraliza a chamada a ``subprocess.run`` e a coleta de erros para que
todos os coletores compartilhem o mesmo comportamento (timeout, captura
de stderr, anotação em ``errors``).
"""
from __future__ import annotations

import subprocess


def run_powershell(
    command: str,
    errors: list[str],
    label: str,
    timeout: int = 8,
) -> str | None:
    """Executa ``powershell -NoProfile -Command``.

    Retorna o stdout sem espaços nas pontas, ou ``None`` se vazio/erro.
    Anota ``errors`` quando o processo termina com erro ou estoura
    timeout, sem propagar a exceção.
    """
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
