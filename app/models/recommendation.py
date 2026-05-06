from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class RiskLevel(str, Enum):
    SAFE = "safe"
    REVIEW = "review"
    RISKY = "risky"
    BLOCKED = "blocked"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Category(str, Enum):
    BIOS = "bios"
    WINDOWS = "windows"
    DRIVERS = "drivers"
    HARDWARE = "hardware"
    GAMES = "games"
    ENERGY = "energy"
    SECURITY = "security"
    TEMPERATURE = "temperature"


@dataclass
class Recommendation:
    title: str
    category: Category
    priority: Priority
    risk: RiskLevel
    rationale: str
    expected_benefit: str
    expected_impact: str
    current_state: str = "Não detectado automaticamente."
    recommended_state: str = ""
    when_not_to_apply: str = ""
    how_to_validate: str = ""
    safety_note: str = ""
    manual_confirmation_required: bool = False
    confidence: str = "medium"
    evidence: list[str] = field(default_factory=list)
    manual_steps: list[str] = field(default_factory=list)
    rollback: str = ""
    games: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.risk in {RiskLevel.RISKY, RiskLevel.BLOCKED} or self.category == Category.BIOS:
            self.manual_confirmation_required = True

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["category"] = self.category.value
        d["priority"] = self.priority.value
        d["risk"] = self.risk.value
        return d
