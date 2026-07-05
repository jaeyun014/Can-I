from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any


CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


@dataclass
class EvidenceRecord:
    field: str
    value: str
    source: str
    rawConfidence: float
    evidenceText: str
    verified: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def sourceReliability(self) -> float:
        return source_reliability().get(self.source, 0.3)

    @property
    def weighted_score(self) -> float:
        verified_boost = 0.1 if self.verified else 0.0
        return min(1.0, self.rawConfidence * self.sourceReliability + verified_boost)


@dataclass
class FusedField:
    field: str
    selectedValue: str
    confidence: float
    candidates: list[dict[str, Any]]
    resolutionReason: str
    hasConflict: bool


@lru_cache
def source_reliability() -> dict[str, float]:
    path = CONFIG_DIR / "source_reliability.json"
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def fuse_evidence(field_name: str, records: list[EvidenceRecord]) -> FusedField:
    relevant = [record for record in records if record.field == field_name and record.value]
    if not relevant:
        return FusedField(
            field=field_name,
            selectedValue="unknown",
            confidence=0.0,
            candidates=[],
            resolutionReason="사용 가능한 근거가 없어 unknown으로 처리했습니다.",
            hasConflict=False,
        )

    scores: dict[str, float] = {}
    sources: dict[str, list[str]] = {}
    for record in relevant:
        scores[record.value] = scores.get(record.value, 0.0) + record.weighted_score
        sources.setdefault(record.value, []).append(record.source)

    total = sum(scores.values()) or 1.0
    candidates = [
        {
            "value": value,
            "score": round(score / total, 3),
            "sources": sources[value],
        }
        for value, score in sorted(scores.items(), key=lambda item: item[1], reverse=True)
    ]
    selected = candidates[0]
    has_conflict = len(candidates) > 1 and selected["score"] < 0.85
    reason = f"{', '.join(selected['sources'])} 근거를 우선 적용했습니다."
    if has_conflict:
        reason = f"{reason} 단, 다른 후보와 충돌이 있어 신뢰도를 낮춥니다."

    return FusedField(
        field=field_name,
        selectedValue=selected["value"],
        confidence=selected["score"],
        candidates=candidates,
        resolutionReason=reason,
        hasConflict=has_conflict,
    )
