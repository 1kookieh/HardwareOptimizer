"""Constantes de domínio centralizadas.

Mantém num único lugar todos os thresholds usados pela engine de
recomendações e pelos coletores, para facilitar revisão, teste e
ajuste fino.
"""
from __future__ import annotations

# --- Memória RAM ---------------------------------------------------------
# Acima desta frequência, considera-se que XMP/EXPO/DOCP está provavelmente
# ativo (DDR4 JEDEC topa em 3200 MT/s; DDR5 JEDEC parte de 4800 MT/s, mas
# 3200 cobre o caso mais comum de "memória sem perfil ativo").
XMP_HEURISTIC_MHZ: int = 3200

# Mínimo confortável de RAM para uso geral atual.
RAM_COMFORTABLE_GB: float = 16.0


# --- Drivers e updates ---------------------------------------------------
# Drivers mais antigos que isto entram na lista de "verificar manualmente".
OUTDATED_DRIVER_DAYS: int = 365 * 3

# Hotfix mais antigo que isto sugere rodar Windows Update.
STALE_HOTFIX_DAYS: int = 60

# Limite máximo de itens listados em outdated_drivers no relatório.
OUTDATED_DRIVERS_REPORT_LIMIT: int = 20


# --- Armazenamento -------------------------------------------------------
# Acima deste percentual de uso, recomenda-se liberar espaço.
DISK_USAGE_HIGH_RATIO: float = 0.90


# --- Rede / fontes oficiais ---------------------------------------------
# Timeout HTTP para checagem de acessibilidade de fontes oficiais.
ONLINE_SOURCE_TIMEOUT_SECONDS: int = 3


# --- Coleta PowerShell ---------------------------------------------------
# Timeouts em segundos por etapa.
POWERSHELL_TIMEOUT_DEFAULT: int = 8
POWERSHELL_TIMEOUT_HOTFIX: int = 15
POWERSHELL_TIMEOUT_DRIVERS: int = 35
POWERSHELL_TIMEOUT_WINDOWS_UPDATE: int = 70
