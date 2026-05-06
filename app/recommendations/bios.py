from __future__ import annotations

from app.models.hardware import UNDETECTED, UNEXPOSED, FullScan
from app.models.recommendation import Category, Priority, Recommendation, RiskLevel


def _detected(value: str | None) -> bool:
    return bool(value) and value not in {UNDETECTED, UNEXPOSED}


def build_bios_recommendations(scan: FullScan, profile_key: str) -> list[Recommendation]:
    recs: list[Recommendation] = []
    bios = scan.bios

    xmp_state = UNEXPOSED
    if scan.hardware.ram_xmp_active is True:
        xmp_state = "Provavelmente ativo (frequência acima de JEDEC detectada)."
    elif scan.hardware.ram_xmp_active is False:
        xmp_state = "Provavelmente inativo (memória operando em frequência JEDEC)."
    speeds = ", ".join(
        f"{m.configured_clock_mhz} MHz" for m in scan.hardware.ram_modules if m.configured_clock_mhz
    ) or "—"
    recs.append(
        Recommendation(
            title="Habilitar XMP / EXPO / DOCP para a memória RAM",
            category=Category.BIOS,
            priority=Priority.HIGH if profile_key in {"games", "high_performance"} else Priority.MEDIUM,
            risk=RiskLevel.REVIEW,
            rationale=(
                "Sem perfil de memória ativado, a RAM opera em frequência JEDEC, abaixo do "
                "anunciado pelo fabricante."
            ),
            current_state=f"{xmp_state} Velocidade(s): {speeds}.",
            recommended_state="Perfil XMP/EXPO/DOCP ativo, validado por POST e teste de estabilidade.",
            expected_benefit="Pode melhorar a estabilidade de FPS e reduzir gargalos em jogos competitivos.",
            expected_impact="Maior largura de banda de memória; pequena variação de consumo.",
            when_not_to_apply=(
                "Quando o sistema não estabiliza, há erros de memória (MEMTEST) ou a placa-mãe "
                "não lista o kit como QVL."
            ),
            how_to_validate="Rodar MemTest86 ou TestMem5 por 1+ hora e confirmar boot estável.",
            safety_note="Configuração de BIOS — alteração apenas manual pelo usuário.",
            confidence="medium",
            evidence=["bios.virtualization=" + bios.virtualization],
            manual_steps=[
                "Reiniciar e entrar na BIOS/UEFI.",
                "Localizar a opção XMP, EXPO ou DOCP.",
                "Selecionar o perfil indicado pelo fabricante da memória.",
                "Salvar e testar o boot.",
            ],
            rollback="Carregar 'Restore Defaults' na BIOS para voltar ao perfil JEDEC.",
        )
    )

    rebar_state = UNEXPOSED
    if scan.hardware.rebar_enabled is True:
        rebar_state = "Habilitado (detectado)."
    elif scan.hardware.rebar_enabled is False:
        rebar_state = "Desabilitado (detectado)."
    rebar_priority = Priority.MEDIUM if scan.hardware.rebar_enabled is False else Priority.LOW
    recs.append(
        Recommendation(
            title="Verificar Resizable BAR / Above 4G Decoding",
            category=Category.BIOS,
            priority=rebar_priority,
            risk=RiskLevel.REVIEW,
            rationale="ReBAR pode trazer ganhos pontuais em GPUs e jogos compatíveis.",
            current_state=rebar_state,
            recommended_state="Resizable BAR e Above 4G Decoding habilitados quando suportados.",
            expected_benefit="Pode melhorar desempenho em jogos compatíveis; ganho variável.",
            expected_impact="Sem impacto negativo conhecido em hardware compatível.",
            when_not_to_apply="Placa-mãe ou GPU sem suporte oficial; instabilidade após habilitar.",
            how_to_validate="Confirmar 'Resizable BAR: Enabled' no GPU-Z após reiniciar.",
            safety_note="Configuração de BIOS — alteração apenas manual pelo usuário.",
            confidence="medium",
            manual_steps=[
                "Verificar suporte da placa-mãe e da GPU no site dos fabricantes.",
                "Habilitar 'Above 4G Decoding' antes de habilitar 'Re-Size BAR Support'.",
                "Salvar e validar com GPU-Z ou painel do driver.",
            ],
            rollback="Desabilitar ambas as opções e carregar defaults se houver instabilidade.",
        )
    )

    if bios.secure_boot.lower().startswith("desabilitado"):
        recs.append(
            Recommendation(
                title="Reativar Secure Boot",
                category=Category.SECURITY,
                priority=Priority.HIGH,
                risk=RiskLevel.SAFE,
                rationale="Secure Boot é requisito de segurança e exigência de jogos com anti-cheat moderno.",
                current_state="Desabilitado",
                recommended_state="Habilitado",
                expected_benefit="Maior segurança e compatibilidade com Valorant, CS2 e outros títulos.",
                expected_impact="Sem impacto de desempenho.",
                when_not_to_apply="Quando há sistema operacional não compatível com UEFI/Secure Boot.",
                how_to_validate="Executar `msinfo32` e verificar 'Secure Boot State: On'.",
                safety_note="Não desabilite Secure Boot por motivos de desempenho.",
                confidence="high",
                evidence=["bios.secure_boot=" + bios.secure_boot],
                manual_steps=[
                    "Entrar na BIOS/UEFI.",
                    "Habilitar Secure Boot e salvar.",
                ],
                rollback="Desabilitar novamente em caso de incompatibilidade.",
            )
        )

    if bios.virtualization.lower().startswith("desabilitado") and profile_key in {
        "development",
        "video_editing",
        "general",
        "stability",
    }:
        recs.append(
            Recommendation(
                title="Habilitar Virtualização (VT-x / AMD-V)",
                category=Category.BIOS,
                priority=Priority.HIGH,
                risk=RiskLevel.SAFE,
                rationale="Necessária para WSL2, Docker, Hyper-V, sandboxing e segurança baseada em virtualização.",
                current_state="Desabilitado",
                recommended_state="Habilitado",
                expected_benefit="Habilita virtualização e melhora isolamento/segurança.",
                expected_impact="Sem impacto perceptível em desempenho de jogos.",
                when_not_to_apply="Quando há políticas corporativas que exijam o contrário.",
                how_to_validate="Executar `systeminfo` e ver 'Virtualization Enabled In Firmware: Yes'.",
                safety_note="Configuração de BIOS — alteração apenas manual pelo usuário.",
                confidence="high",
                evidence=["bios.virtualization=" + bios.virtualization],
                manual_steps=[
                    "Entrar na BIOS/UEFI.",
                    "Habilitar Intel VT-x ou AMD SVM.",
                    "Salvar e reiniciar.",
                ],
                rollback="Desabilitar a opção e reiniciar.",
            )
        )

    if bios.hvci_running.lower().startswith("habilitado") and profile_key in {"games", "high_performance"}:
        recs.append(
            Recommendation(
                title="Avaliar Memory Integrity / HVCI para desempenho em jogos",
                category=Category.SECURITY,
                priority=Priority.MEDIUM,
                risk=RiskLevel.RISKY,
                rationale=(
                    "Memory Integrity aumenta isolamento de kernel, mas pode ter custo de desempenho em alguns "
                    "jogos e anti-cheats."
                ),
                current_state="Memory Integrity / HVCI detectado como habilitado.",
                recommended_state="Manter habilitado por padrão; considerar desabilitar somente se houver perda real medida.",
                expected_benefit="Pode reduzir overhead em alguns cenários competitivos, sem ganho garantido.",
                expected_impact="Desabilitar reduz uma camada de segurança do Windows.",
                when_not_to_apply="PC usado para trabalho sensível, bancos, dados corporativos ou quando segurança é prioridade.",
                how_to_validate="Medir frametime antes/depois no mesmo jogo e restaurar se não houver benefício claro.",
                safety_note="Trade-off de segurança. O app nunca muda essa configuração automaticamente.",
                confidence="medium",
                evidence=[f"bios.hvci_running={bios.hvci_running}", f"bios.vbs_running={bios.vbs_running}"],
                manual_steps=[
                    "Criar ponto de restauração.",
                    "Abrir Segurança do Windows > Segurança do dispositivo > Isolamento do núcleo.",
                    "Alterar Memory Integrity apenas se você aceitar o trade-off.",
                    "Reiniciar e validar segurança/desempenho.",
                ],
                rollback="Reativar Memory Integrity e reiniciar.",
            )
        )

    if bios.storage_mode.lower().startswith("raid"):
        recs.append(
            Recommendation(
                title="Confirmar se modo RAID é necessário",
                category=Category.BIOS,
                priority=Priority.LOW,
                risk=RiskLevel.RISKY,
                rationale="Muitos PCs usam AHCI para SSDs comuns; RAID sem necessidade pode complicar drivers e migrações.",
                current_state=f"Modo de armazenamento detectado: {bios.storage_mode}.",
                recommended_state="Manter RAID se houver array/Intel RST/AMD RAIDXpert em uso; considerar AHCI apenas com migração planejada.",
                expected_benefit="Pode simplificar compatibilidade de storage quando RAID não é usado.",
                expected_impact="Trocar RAID/AHCI sem preparo pode impedir o boot do Windows.",
                when_not_to_apply="Quando há volume RAID real, Optane/RST, BitLocker sem preparo ou sistema corporativo.",
                how_to_validate="Confirmar no Gerenciador de Dispositivos e na BIOS antes de qualquer mudança.",
                safety_note="Alteração sensível de BIOS/storage; requer backup e plano de migração.",
                confidence="low",
                evidence=[f"bios.storage_mode={bios.storage_mode}"],
                manual_steps=[
                    "Fazer backup completo.",
                    "Confirmar se existe array RAID real.",
                    "Pesquisar procedimento oficial para migrar RAID/AHCI no Windows.",
                    "Alterar somente se houver motivo claro.",
                ],
                rollback="Voltar ao modo anterior na BIOS se o Windows não inicializar.",
            )
        )

    if bios.fast_startup.lower().startswith("habilitado") and profile_key == "stability":
        recs.append(
            Recommendation(
                title="Desabilitar Inicialização Rápida para estabilidade",
                category=Category.WINDOWS,
                priority=Priority.MEDIUM,
                risk=RiskLevel.SAFE,
                rationale="Fast Startup pode preservar estado de kernel/driver e mascarar problemas após updates.",
                current_state="Inicialização Rápida habilitada.",
                recommended_state="Desabilitada em perfil de estabilidade ou dual-boot.",
                expected_benefit="Pode reduzir inconsistências após updates, troca de driver ou dual-boot.",
                expected_impact="Boot frio pode ficar um pouco mais lento.",
                when_not_to_apply="Quando o tempo de boot é prioridade e não há problemas de estabilidade.",
                how_to_validate="Desligar totalmente, ligar novamente e testar dispositivos/drivers.",
                safety_note="Configuração reversível do Windows; não mexe em BIOS.",
                confidence="medium",
                evidence=[f"bios.fast_startup={bios.fast_startup}", f"bios.hibernation={bios.hibernation}"],
                manual_steps=[
                    "Abrir Opções de Energia.",
                    "Alterar configurações dos botões de energia.",
                    "Desmarcar 'Ligar inicialização rápida'.",
                ],
                rollback="Reabilitar a opção no mesmo painel.",
            )
        )

    cpu_vendor = bios.cpu_vendor.lower()
    if profile_key in {"games", "high_performance"} and ("authenticamd" in cpu_vendor or "genuineintel" in cpu_vendor):
        is_amd = "authenticamd" in cpu_vendor
        recs.append(
            Recommendation(
                title="Confirmar comportamento de boost da CPU",
                category=Category.BIOS,
                priority=Priority.LOW,
                risk=RiskLevel.REVIEW,
                rationale="Boost automático da CPU costuma ser mais seguro que OC manual para uso geral e jogos.",
                current_state=f"Fabricante da CPU: {bios.cpu_vendor}.",
                recommended_state=(
                    "AMD: PBO em Auto/Enabled conservador se houver refrigeração adequada."
                    if is_amd
                    else "Intel: Turbo Boost habilitado e limites de energia coerentes com refrigeração/placa-mãe."
                ),
                expected_benefit="Pode manter desempenho esperado sem prometer ganhos ou exigir overclock manual.",
                expected_impact="Mais boost pode elevar consumo e temperatura.",
                when_not_to_apply="Temperaturas altas, fonte/refrigeração insuficiente ou prioridade em baixo consumo.",
                how_to_validate="Monitorar clocks, temperatura e estabilidade em carga real.",
                safety_note="Não fazer OC/UV automático; qualquer ajuste é manual e conservador.",
                confidence="medium",
                evidence=[f"bios.cpu_vendor={bios.cpu_vendor}"],
                rollback="Voltar BIOS para Auto/Defaults se houver instabilidade.",
            )
        )

    if not (_detected(scan.hardware.motherboard_model) and _detected(bios.version)):
        recs.append(
            Recommendation(
                title="Atualização de BIOS — bloqueada até identificação automática confiável",
                category=Category.BIOS,
                priority=Priority.LOW,
                risk=RiskLevel.RISKY,
                rationale=(
                    "Atualizar BIOS sem o modelo exato da placa-mãe e a versão atual pode causar "
                    "incompatibilidade ou brick."
                ),
                current_state=f"Placa: {scan.hardware.motherboard_model} — BIOS: {bios.version}",
                recommended_state="Detectar modelo exato e versão atual antes de qualquer atualização.",
                expected_benefit="Atualização só deve ser feita se houver fix relevante para o seu hardware.",
                expected_impact="Risco de brick em caso de erro durante o flash.",
                when_not_to_apply=(
                    "Sempre que não houver problema específico documentado pelo fabricante; "
                    "nunca fazer downgrade."
                ),
                how_to_validate="Conferir versão atual em `msinfo32` e a mais recente no site do fabricante.",
                safety_note="O app não atualiza BIOS automaticamente e não recomenda downgrade.",
                confidence="low",
                manual_steps=[
                    "Identificar modelo exato da placa-mãe (placa, não apenas chipset).",
                    "Acessar o site oficial do fabricante.",
                    "Ler o changelog para sua versão.",
                    "Seguir o procedimento oficial (BIOS Flashback quando disponível).",
                ],
                rollback=(
                    "Não realizar downgrade de BIOS — pode trazer riscos e não é suportado por "
                    "muitos fabricantes."
                ),
            )
        )

    return recs
