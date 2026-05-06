from __future__ import annotations

from app.models.hardware import FullScan
from app.models.profile import SUPPORTED_GAMES
from app.models.recommendation import Category, Priority, Recommendation, RiskLevel


_COMPETITIVE = {"valorant", "league_of_legends", "cs2", "cod_warzone", "marvel_rivals", "fortnite"}


def build_games_recommendations(scan: FullScan, games: list[str]) -> list[Recommendation]:
    if not games:
        return []
    recs: list[Recommendation] = []
    selected_labels = [SUPPORTED_GAMES.get(g, g) for g in games if g in SUPPORTED_GAMES]

    recs.append(
        Recommendation(
            title="Habilitar Hardware-Accelerated GPU Scheduling (HAGS) — opcional",
            category=Category.GAMES,
            priority=Priority.LOW,
            risk=RiskLevel.REVIEW,
            rationale=(
                "Em GPUs e drivers compatíveis, HAGS pode reduzir input lag em alguns jogos; "
                "em outros pode causar regressão."
            ),
            recommended_state="Habilitado se a GPU/driver der suporte e não houver regressão.",
            expected_benefit="Pode reduzir input lag e melhorar consistência de frametime.",
            expected_impact="Pode causar regressão pontual; requer validação prática.",
            when_not_to_apply="Driver instável, GPU antiga ou regressão observada.",
            how_to_validate="Comparar FPS e input lag antes/depois em ambiente controlado.",
            safety_note="Configuração reversível pelo Windows.",
            confidence="medium",
            games=selected_labels,
            manual_steps=[
                "Configurações do Windows > Sistema > Tela > Configurações Gráficas.",
                "Habilitar 'Agendamento de GPU acelerado por hardware'.",
                "Reiniciar e validar com benchmark do jogo.",
            ],
            rollback="Desabilitar a opção e reiniciar.",
        )
    )

    if any(g in _COMPETITIVE for g in games):
        recs.append(
            Recommendation(
                title="Configurações conservadoras para FPS competitivo",
                category=Category.GAMES,
                priority=Priority.HIGH,
                risk=RiskLevel.SAFE,
                rationale="Em jogos competitivos, estabilidade de frametime é mais importante que FPS médio absoluto.",
                recommended_state=(
                    "VSync OFF, NVIDIA Reflex / Anti-Lag ON quando disponível, framerate cap ~3 FPS "
                    "abaixo do limite do monitor."
                ),
                expected_benefit="Pode melhorar consistência de frametime e reduzir input lag.",
                expected_impact="FPS médio pode ser limitado; estabilidade aumenta.",
                when_not_to_apply="Quando o objetivo é benchmark de pico, não jogo competitivo.",
                how_to_validate="Monitorar 1% low e frametime com ferramenta como CapFrameX.",
                safety_note="Configurações dentro do jogo e do painel do driver — manuais.",
                confidence="medium",
                games=selected_labels,
                manual_steps=[
                    "Abrir o painel da GPU (NVIDIA/AMD).",
                    "Habilitar Reflex / Anti-Lag se disponível.",
                    "Configurar limite de FPS abaixo do refresh do monitor.",
                ],
            )
        )

    if "valorant" in games or "cs2" in games:
        recs.append(
            Recommendation(
                title="Anti-cheats exigem Secure Boot e TPM 2.0 (Vanguard / VAC)",
                category=Category.GAMES,
                priority=Priority.HIGH,
                risk=RiskLevel.SAFE,
                rationale="Vanguard (Valorant) requer Secure Boot e TPM em Windows 11; CS2 funciona melhor com sistema atualizado.",
                recommended_state="Secure Boot habilitado, TPM 2.0 ativo, Windows atualizado.",
                expected_benefit="Mantém compatibilidade e segurança do anti-cheat.",
                expected_impact="Sem impacto de desempenho.",
                when_not_to_apply="Cenários de dual-boot complexos com restrições específicas.",
                how_to_validate="`msinfo32` para confirmar Secure Boot ON e TPM 2.0.",
                safety_note="Não desabilite Secure Boot/TPM por motivos de desempenho.",
                confidence="high",
                games=selected_labels,
            )
        )

    ram = scan.hardware.ram_total_gb or 0.0
    if ram and ram < 16:
        recs.append(
            Recommendation(
                title="RAM abaixo do confortável para jogos modernos",
                category=Category.GAMES,
                priority=Priority.HIGH,
                risk=RiskLevel.REVIEW,
                rationale=f"RAM detectada: {ram} GB. Jogos modernos beneficiam-se de 16 GB+ em dual-channel.",
                current_state=f"{ram} GB",
                recommended_state="16 GB ou mais em dual-channel, com XMP/EXPO ativo.",
                expected_benefit="Pode reduzir stutter por paginação e melhorar consistência.",
                expected_impact="Investimento financeiro; verificar QVL.",
                when_not_to_apply="Jogos antigos/leves apenas.",
                how_to_validate="Monitorar paginação e uso real durante o jogo.",
                safety_note="Compra/instalação manual.",
                confidence="medium",
                games=selected_labels,
            )
        )

    return recs
