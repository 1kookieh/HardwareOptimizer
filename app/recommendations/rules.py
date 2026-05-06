from __future__ import annotations

from app.models.hardware import FullScan
from app.models.recommendation import Category, Priority, Recommendation, RiskLevel


def build_windows_recommendations(scan: FullScan, profile_key: str) -> list[Recommendation]:
    recs: list[Recommendation] = []

    power_plan = (scan.system.power_plan or "").lower()
    if profile_key in {"games", "high_performance", "video_editing"}:
        if "alto desempenho" not in power_plan and "high performance" not in power_plan and "ultimate" not in power_plan:
            recs.append(
                Recommendation(
                    title="Selecionar plano de energia 'Alto Desempenho'",
                    category=Category.ENERGY,
                    priority=Priority.MEDIUM,
                    risk=RiskLevel.SAFE,
                    rationale="Planos balanceados podem reduzir clocks de CPU em cargas variáveis.",
                    current_state=scan.system.power_plan,
                    recommended_state="Plano 'Alto Desempenho' ou 'Desempenho Máximo' ativo.",
                    expected_benefit="Pode melhorar a consistência de frametime em jogos e cargas variáveis.",
                    expected_impact="Maior consumo de energia e leve aumento de temperatura.",
                    when_not_to_apply="Notebooks na bateria ou ambientes com restrição térmica.",
                    how_to_validate="Executar `powercfg /getactivescheme` após a troca.",
                    safety_note="Alteração reversível; preferível executar manualmente.",
                    confidence="high",
                    manual_steps=[
                        "Abrir 'Painel de Controle > Opções de Energia'.",
                        "Selecionar 'Alto Desempenho'.",
                        "Confirmar com `powercfg /getactivescheme`.",
                    ],
                    rollback="Voltar ao plano 'Equilibrado' a qualquer momento.",
                )
            )

    recs.append(
        Recommendation(
            title="Verificar inicialização do Windows e apps em background",
            category=Category.WINDOWS,
            priority=Priority.MEDIUM,
            risk=RiskLevel.SAFE,
            rationale="Apps em background podem competir por CPU, RAM e armazenamento.",
            recommended_state="Apps não-essenciais desabilitados na inicialização.",
            expected_benefit="Pode melhorar a responsividade do sistema e reduzir gargalos.",
            expected_impact="Apps desabilitados não iniciarão automaticamente.",
            when_not_to_apply="Apps essenciais (drivers, antivírus, suporte de hardware).",
            how_to_validate="Reiniciar e observar uso de CPU/RAM no Gerenciador de Tarefas.",
            safety_note="Não desabilitar antivírus, firewall, drivers ou serviços críticos.",
            confidence="medium",
            manual_steps=[
                "Abrir Gerenciador de Tarefas (Ctrl+Shift+Esc).",
                "Aba 'Inicializar' — desabilitar apps não essenciais.",
                "Reiniciar e validar.",
            ],
        )
    )

    ram = scan.hardware.ram_total_gb or 0.0
    if ram and ram < 16:
        recs.append(
            Recommendation(
                title="Considerar upgrade de RAM",
                category=Category.HARDWARE,
                priority=Priority.MEDIUM,
                risk=RiskLevel.REVIEW,
                rationale=f"RAM total detectada: {ram} GB. 16 GB é o mínimo confortável atual.",
                current_state=f"{ram} GB",
                recommended_state="16 GB ou mais, com kit em dual-channel.",
                expected_benefit="Pode reduzir gargalos em jogos modernos e multitarefa pesada.",
                expected_impact="Investimento financeiro; verificar QVL da placa-mãe.",
                when_not_to_apply="Quando o uso real raramente passa de 70% da RAM atual.",
                how_to_validate="Monitorar uso real com Gerenciador de Tarefas ou HWiNFO.",
                safety_note="Compra/instalação manual; verificar compatibilidade.",
                confidence="medium",
                evidence=[f"hardware.ram_total_gb={ram}"],
            )
        )

    return recs


def build_drivers_recommendations(scan: FullScan, profile_key: str) -> list[Recommendation]:
    recs: list[Recommendation] = []
    gpu = scan.hardware.gpu_name
    drv = scan.hardware.gpu_driver_version

    recs.append(
        Recommendation(
            title="Verificar manualmente o driver da GPU",
            category=Category.DRIVERS,
            priority=Priority.HIGH if profile_key in {"games", "video_editing"} else Priority.MEDIUM,
            risk=RiskLevel.REVIEW,
            rationale="Drivers desatualizados podem causar instabilidade, bugs visuais e redução de FPS.",
            current_state=f"GPU: {gpu} — Driver: {drv}",
            recommended_state="Driver oficial mais recente, baixado direto do site da NVIDIA/AMD/Intel.",
            expected_benefit="Pode melhorar estabilidade e suporte a jogos recém-lançados.",
            expected_impact="Sem impacto negativo conhecido se for driver oficial estável.",
            when_not_to_apply="Driver atual estável e jogos sem problema; evite versões 'beta' em produção.",
            how_to_validate="Após instalar, validar em jogo de referência (FPS estável, sem artefatos).",
            safety_note="Sempre baixar do site oficial. Nunca usar drivers de terceiros.",
            confidence="medium",
            manual_steps=[
                "Identificar fabricante e modelo da GPU.",
                "Acessar o site oficial (nvidia.com, amd.com, intel.com).",
                "Baixar e instalar a versão WHQL mais recente.",
                "Reiniciar e testar.",
            ],
            rollback="Reverter via 'Roll Back Driver' no Gerenciador de Dispositivos.",
        )
    )

    return recs


def build_storage_recommendations(scan: FullScan, profile_key: str) -> list[Recommendation]:
    recs: list[Recommendation] = []
    for disk in scan.hardware.storage:
        total = disk.get("total_gb") or 0.0
        used = disk.get("used_gb") or 0.0
        if total > 0 and (used / total) > 0.9:
            recs.append(
                Recommendation(
                    title=f"Liberar espaço no disco {disk.get('mountpoint')}",
                    category=Category.WINDOWS,
                    priority=Priority.HIGH,
                    risk=RiskLevel.SAFE,
                    rationale="Discos acima de 90% de uso prejudicam desempenho e estabilidade do Windows.",
                    current_state=f"{used:.1f} GB usados de {total:.1f} GB ({used/total:.0%}).",
                    recommended_state="Manter pelo menos 15% de espaço livre.",
                    expected_benefit="Pode melhorar a responsividade do sistema e reduzir engasgos.",
                    expected_impact="Sem impacto negativo conhecido.",
                    when_not_to_apply="Quando o disco contém dados arquivados que não podem ser movidos.",
                    how_to_validate="Verificar espaço livre após limpeza no Gerenciador de Arquivos.",
                    safety_note="Não usar 'Limpeza de Disco' agressivamente em pastas do sistema.",
                    confidence="high",
                    evidence=[f"storage={disk}"],
                )
            )
    return recs
