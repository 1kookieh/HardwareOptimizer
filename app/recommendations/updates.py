from __future__ import annotations

from app.models.hardware import FullScan
from app.models.recommendation import Category, Priority, Recommendation, RiskLevel


def build_updates_recommendations(scan: FullScan, profile_key: str) -> list[Recommendation]:
    recs: list[Recommendation] = []
    updates = scan.updates

    if updates.pending_reboot is True:
        recs.append(
            Recommendation(
                title="Reiniciar para aplicar atualizaÃ§Ãµes pendentes",
                category=Category.WINDOWS,
                priority=Priority.HIGH,
                risk=RiskLevel.SAFE,
                rationale="O Windows sinalizou uma reinicializaÃ§Ã£o pendente apÃ³s update ou troca de arquivo.",
                current_state="ReinicializaÃ§Ã£o pendente detectada.",
                recommended_state="Reiniciar em um momento seguro e validar estabilidade depois.",
                expected_benefit="Pode concluir correÃ§Ãµes e reduzir inconsistÃªncias de driver/sistema.",
                expected_impact="Interrompe sessÃµes abertas; salve trabalhos antes.",
                when_not_to_apply="Durante partidas, renders, compilaÃ§Ãµes ou tarefas longas em andamento.",
                how_to_validate="Abrir Windows Update apÃ³s reiniciar e confirmar que nÃ£o hÃ¡ reinÃ­cio pendente.",
                safety_note="AÃ§Ã£o normal do Windows; nÃ£o altera BIOS nem instala drivers automaticamente.",
                manual_confirmation_required=False,
                confidence="high",
                evidence=["updates.pending_reboot=True"],
            )
        )

    if updates.available_windows_updates and updates.available_windows_updates > 0:
        recs.append(
            Recommendation(
                title=f"HÃ¡ {updates.available_windows_updates} atualizaÃ§Ã£o(Ãµes) do Windows pendente(s)",
                category=Category.WINDOWS,
                priority=Priority.HIGH,
                risk=RiskLevel.SAFE,
                rationale="AtualizaÃ§Ãµes pendentes podem incluir correÃ§Ãµes de estabilidade, seguranÃ§a e drivers via Windows Update.",
                current_state=f"{updates.available_windows_updates} update(s) disponÃ­vel(is).",
                recommended_state="Revisar no Windows Update e instalar apenas pelo fluxo oficial do Windows.",
                expected_benefit="Pode melhorar estabilidade, seguranÃ§a e compatibilidade.",
                expected_impact="Pode exigir download, reinÃ­cio e algum tempo de indisponibilidade.",
                when_not_to_apply="Quando vocÃª precisa manter a versÃ£o atual por compatibilidade ou polÃ­tica corporativa.",
                how_to_validate="Abrir ConfiguraÃ§Ãµes > Windows Update e verificar histÃ³rico apÃ³s aplicar.",
                safety_note="O app apenas informa. Nenhuma atualizaÃ§Ã£o Ã© instalada automaticamente.",
                confidence="medium",
                evidence=[f"updates.available_windows_updates={updates.available_windows_updates}"],
            )
        )

    if updates.last_hotfix_age_days is not None and updates.last_hotfix_age_days > 60:
        recs.append(
            Recommendation(
                title="Verificar Windows Update por falta de hotfix recente",
                category=Category.WINDOWS,
                priority=Priority.MEDIUM,
                risk=RiskLevel.SAFE,
                rationale="O Ãºltimo hotfix detectado parece antigo para um sistema Windows conectado.",
                current_state=(
                    f"Ãšltimo hotfix: {updates.last_hotfix_id} em {updates.last_hotfix_date} "
                    f"({updates.last_hotfix_age_days} dias)."
                ),
                recommended_state="Executar verificaÃ§Ã£o manual no Windows Update.",
                expected_benefit="Pode trazer correÃ§Ãµes de seguranÃ§a e estabilidade.",
                expected_impact="Pode exigir reinÃ­cio.",
                when_not_to_apply="Sistemas gerenciados por WSUS/empresa ou mÃ¡quinas offline por desenho.",
                how_to_validate="Confirmar novo hotfix no histÃ³rico do Windows Update.",
                safety_note="NÃ£o force updates por ferramentas de terceiros.",
                confidence="medium",
                evidence=[f"updates.last_hotfix_age_days={updates.last_hotfix_age_days}"],
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
                recommended_state="Comparar com drivers oficiais do fabricante do PC, placa-mÃ£e, GPU ou perifÃ©rico.",
                expected_benefit="Pode melhorar estabilidade e compatibilidade, especialmente em GPU/chipset/rede/Ã¡udio.",
                expected_impact="Atualizar driver pode alterar comportamento; crie ponto de restauraÃ§Ã£o quando apropriado.",
                when_not_to_apply="Quando o driver atual Ã© exigido por hardware legado ou software corporativo.",
                how_to_validate="Verificar versÃ£o/data no Gerenciador de Dispositivos apÃ³s update e testar o uso real.",
                safety_note="Nunca usar instaladores de driver genÃ©ricos ou duvidosos. NÃ£o hÃ¡ instalaÃ§Ã£o automÃ¡tica.",
                confidence="medium",
                evidence=[
                    f"{d.device_name} | {d.version} | {d.driver_date} | {d.provider}"
                    for d in updates.outdated_drivers[:10]
                ],
                manual_steps=[
                    "Identificar o dispositivo e o fabricante real.",
                    "Baixar driver apenas do site oficial do fabricante.",
                    "Criar ponto de restauraÃ§Ã£o quando a mudanÃ§a for sensÃ­vel.",
                    "Instalar, reiniciar e validar estabilidade.",
                ],
                rollback="Usar 'Reverter Driver' no Gerenciador de Dispositivos ou ponto de restauraÃ§Ã£o.",
            )
        )

    return recs
