from __future__ import annotations

from dataclasses import dataclass

from app.services.evidence_fusion_service import EvidenceRecord, fuse_evidence


@dataclass
class ConflictRecord:
    conflictType: str
    field: str
    sourceA: str
    valueA: str
    sourceB: str
    valueB: str
    selectedValue: str
    resolution: str
    confidencePenalty: float


def detect_conflicts(records: list[EvidenceRecord]) -> list[ConflictRecord]:
    conflicts: list[ConflictRecord] = []
    for field_name in sorted({record.field for record in records}):
        fused = fuse_evidence(field_name, records)
        if not fused.hasConflict or len(fused.candidates) < 2:
            continue
        first, second = fused.candidates[0], fused.candidates[1]
        conflicts.append(
            ConflictRecord(
                conflictType=f"{field_name}_conflict",
                field=field_name,
                sourceA=",".join(first["sources"]),
                valueA=first["value"],
                sourceB=",".join(second["sources"]),
                valueB=second["value"],
                selectedValue=fused.selectedValue,
                resolution="source_reliability_priority",
                confidencePenalty=0.2,
            )
        )
    return conflicts
