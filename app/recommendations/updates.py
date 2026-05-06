from __future__ import annotations

from app.config import STALE_HOTFIX_DAYS
from app.models.hardware import FullScan
from app.models.recommendation import Category, Priority, Recommendation, RiskLevel


def build_updates_recommendations(scan: FullScan, profile_key: str) -> list[Recommendation]:
    recs: list[Recommendation] = []
    updates = scan.updates

    if updates.pending_reboot is True:
        recs.append(
            Recommendation(
                title="Reiniciar para aplicar atualizações pendentes",
                category=Category.WINDOWS,
                priority=Priority.HIGH,
                risk=RiskLevel.SAFE,
                rationale="O Windows sinalizou uma reinicialização pendente após update ou troca de arquivo.",
                current_state="Reinicialização pendente detectada.",
                recommended_state="Reiniciar em um momento seguro e validar estabilidade depois.",
                expected_benefit="Pode concluir correções e reduzir inconsistências de driver/sistema.",
                expected_impact="Interrompe sessões abertas; salve trabalhos antes.",
                when_not_to_apply="Durante partidas, renders, compilações ou tarefas longas em andamento.",
                how_to_validate="Abrir Windows Update após reiniciar e confirmar que não há reinício pendente.",
                safety_note="Ação normal do Windows; não altera BIOS nem instala drivers automaticamente.",
                manual_confirmation_required=False,
                confidence="high",
                evidence=["updates.pending_reboot=True"],
            )
        )

    if updates.available_windows_updates and updates.available_windows_updates > 0:
        recs.append(
            Recommendation(
                title=f"Há {updates.available_windows_updates} atualização(ões) do Windows pendente(s)",
                category=Category.WINDOWS,
                priority=Priority.HIGH,
                risk=RiskLevel.SAFE,
                rationale="Atualizações pendentes podem incluir correções de estabilidade, segurança e drivers via Windows Update.",
                current_state=f"{updates.available_windows_updates} update(s) disponível(is).",
                recommended_state="Revisar no Windows Update e instalar apenas pelo fluxo oficial do Windows.",
                expected_benefit="Pode melhorar estabilidade, segurança e compatibilidade.",
                expected_impact="Pode exigir download, reinício e algum tempo de indisponibilidade.",
                when_not_to_apply="Quando você precisa manter a versão atual por compatibilidade ou política corporativa.",
                how_to_validate="Abrir Configurações > Windows Update e verificar histórico após aplicar.",
                safety_note="O app apenas informa. Nenhuma atualização é instalada automaticamente.",
                confidence="medium",
                evidence=[
                    f"updates.available_windows_updates={updates.available_windows_updates}",
                    f"updates.online_check_status={updates.online_check_status}",
                    *updates.official_sources,
                ],
            )
        )

    if updates.last_hotfix_age_days is not None and updates.last_hotfix_age_days > STALE_HOTFIX_DAYS:
        recs.append(
            Recommendation(
                title="Verificar Windows Update por falta de hotfix recente",
                category=Category.WINDOWS,
                priority=Priority.MEDIUM,
                risk=RiskLevel.SAFE,
                rationale="O último hotfix detectado parece antigo para um sistema Windows conectado.",
                current_state=(
                    f"Último hotfix: {updates.last_hotfix_id} em {updates.last_hotfix_date} "
                    f"({updates.last_hotfix_age_days} dias)."
                ),
                recommended_state="Executar verificação manual no Windows Update.",
                expected_benefit="Pode trazer correções de segurança e estabilidade.",
                expected_impact="Pode exigir reinício.",
                when_not_to_apply="Sistemas gerenciados por WSUS/empresa ou máquinas offline por desenho.",
                how_to_validate="Confirmar novo hotfix no histórico do Windows Update.",
                safety_note="Não force updates por ferramentas de terceiros.",
                confidence="medium",
                evidence=[
                    f"updates.last_hotfix_age_days={updates.last_hotfix_age_days}",
                    f"updates.online_check_status={updates.online_check_status}",
                    *updates.official_sources,
                ],
            )
        )

    if updates.outdated_drivers:
        names = ", ".join(d.device_name for d in updates.outdated_drivers[:5])
        priority = Priority.HIGH if profile_key in {"games", "video_editing"} else Priority.MEDIUM
        recs.append(
            Recommendation(
                title="Verificar drivers antigos manualmente",
                category=Category.DRIVERS,
                priority=priority,
                risk=RiskLevel.REVIEW,
                rationale="Drivers com mais de 3 anos podem causar perda de compatibilidade, bugs ou instabilidade.",
                current_state=f"{len(updates.outdated_drivers)} driver(s) antigo(s) detectado(s): {names}",
                recommended_state="Comparar com drivers oficiais do fabricante do PC, placa-mãe, GPU ou periférico.",
                expected_benefit="Pode melhorar estabilidade e compatibilidade, especialmente em GPU/chipset/rede/áudio.",
                expected_impact="Atualizar driver pode alterar comportamento; crie ponto de restauração quando apropriado.",
                when_not_to_apply="Quando o driver atual é exigido por hardware legado ou software corporativo.",
                how_to_validate="Verificar versão/data no Gerenciador de Dispositivos após update e testar o uso real.",
                safety_note="Nunca usar instaladores de driver genéricos ou duvidosos. Não há instalação automática.",
                confidence="medium",
                evidence=[
                    f"{d.device_name} | {d.version} | {d.driver_date} | {d.provider}"
                    for d in updates.outdated_drivers[:10]
                ]
                + [f"{kind}: {url}" for kind, url in updates.driver_lookup_urls.items()],
                manual_steps=[
                    "Identificar o dispositivo e o fabricante real.",
                    "Baixar driver apenas do site oficial do fabricante.",
                    "Criar ponto de restauração quando a mudança for sensível.",
                    "Instalar, reiniciar e validar estabilidade.",
                ],
                rollback="Usar 'Reverter Driver' no Gerenciador de Dispositivos ou ponto de restauração.",
            )
        )

    return recs
