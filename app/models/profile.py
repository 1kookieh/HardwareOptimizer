from dataclasses import dataclass


@dataclass(frozen=True)
class Profile:
    key: str
    label: str
    description: str
    priority_categories: tuple[str, ...]


PROFILES: dict[str, Profile] = {
    "games": Profile(
        key="games",
        label="Jogos",
        description="Prioriza FPS, frametime e input lag.",
        priority_categories=("games", "drivers", "bios", "windows", "energy"),
    ),
    "development": Profile(
        key="development",
        label="Desenvolvimento",
        description="Prioriza estabilidade, virtualização e multitarefa.",
        priority_categories=("windows", "hardware", "drivers", "bios"),
    ),
    "video_editing": Profile(
        key="video_editing",
        label="Edição de Vídeo",
        description="Prioriza CPU, GPU, RAM, VRAM e armazenamento.",
        priority_categories=("hardware", "drivers", "bios", "windows"),
    ),
    "general": Profile(
        key="general",
        label="Uso Geral",
        description="Prioriza segurança, estabilidade e energia equilibrada.",
        priority_categories=("security", "windows", "energy", "drivers"),
    ),
    "high_performance": Profile(
        key="high_performance",
        label="Alto Desempenho",
        description="Prioriza desempenho com alertas de consumo e temperatura.",
        priority_categories=("bios", "drivers", "windows", "temperature", "energy"),
    ),
    "stability": Profile(
        key="stability",
        label="Estabilidade",
        description="Prioriza configurações conservadoras e seguras.",
        priority_categories=("security", "windows", "drivers", "temperature"),
    ),
    "low_power": Profile(
        key="low_power",
        label="Baixo Consumo",
        description="Prioriza economia de energia, ruído e temperatura.",
        priority_categories=("energy", "temperature", "windows"),
    ),
}


SUPPORTED_GAMES: dict[str, str] = {
    "valorant": "Valorant",
    "league_of_legends": "League of Legends",
    "cod_warzone": "Call of Duty / Warzone",
    "marvel_rivals": "Marvel Rivals",
    "fortnite": "Fortnite",
    "cs2": "Counter-Strike 2",
}
