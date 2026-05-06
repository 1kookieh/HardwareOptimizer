from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path


QUALITY_SPEC_PATH = Path(__file__).resolve().parents[2] / "docs" / "recommendation_quality_spec.md"


@dataclass(frozen=True)
class QualitySpecReference:
    path: str
    exists: bool
    sha256: str
    title: str

    def to_dict(self) -> dict[str, str | bool]:
        return asdict(self)


def load_quality_spec_text() -> str:
    if not QUALITY_SPEC_PATH.exists():
        return ""
    return QUALITY_SPEC_PATH.read_text(encoding="utf-8")


def quality_spec_reference() -> QualitySpecReference:
    text = load_quality_spec_text()
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest() if text else ""
    title = "Recommendation Quality Spec"
    for line in text.splitlines():
        if line.startswith("# "):
            title = line.removeprefix("# ").strip() or title
            break
    return QualitySpecReference(
        path=str(QUALITY_SPEC_PATH),
        exists=bool(text),
        sha256=digest,
        title=title,
    )


def quality_spec_detection_source() -> list[str]:
    ref = quality_spec_reference()
    if not ref.exists:
        return [f"spec ausente: {ref.path}"]
    return [ref.path, f"sha256:{ref.sha256[:12]}", ref.title]
