from __future__ import annotations

from typing import Any

from app.models.schemas import AnalyzeResponse, Decision, NormalizedInput
from app.services.confidence_service import apply_conservative_conflict_policy, build_confidence_report
from app.services.rule_engine import (
    RISK_ORDER,
    SERVICE_KEYS,
    _apply_safety_hints,
    _fallback_rule,
    _find_rule,
    _region_message,
)


def analyze_material(normalized: NormalizedInput) -> AnalyzeResponse:
    rule = _find_rule(normalized.itemName, normalized.material) or _fallback_rule(normalized.itemName)
    contamination_level = detect_contamination_level(normalized)
    decisions: dict[str, dict[str, Any]] = {}
    highest_risk = "SAFE"
    labels = {
        "microwave": "전자레인지",
        "airFryer": "에어프라이어",
        "oven": "오븐",
        "freezer": "냉동 보관",
        "dishwasher": "식기세척기",
    }

    for key in SERVICE_KEYS:
        decision = dict(rule["decisions"][key])
        decision["label"] = labels[key]
        decisions[key] = decision
        if RISK_ORDER[decision["status"]] > RISK_ORDER[highest_risk]:
            highest_risk = decision["status"]

    category = rule["disposal"]["category"]
    disposal_decision = _build_disposal_decision(
        category=category,
        instruction=rule["disposal"]["instruction"],
        contamination_level=contamination_level,
        region=normalized.region,
    )
    result = AnalyzeResponse(
        targetType="MATERIAL_OBJECT",
        itemName=rule["itemName"],
        summary="용기/재질 기준으로 가열, 냉동, 세척, 분리배출을 판단했습니다.",
        detectedMaterial=rule["detectedMaterial"],
        materialCode=(normalized.material or rule["detectedMaterial"]).upper()
        if (normalized.material or rule["detectedMaterial"]) != "unknown"
        else "",
        contaminationLevel=contamination_level,
        objectType=normalized.objectType,
        ocrText=normalized.ocrText,
        region=normalized.region,
        overallRisk=max(highest_risk, disposal_decision.status, key=lambda status: RISK_ORDER[status]),
        decisions=decisions,
        disposal={
            "category": disposal_decision.category or category,
            "regionRule": _region_message(normalized.region, disposal_decision.category or category),
            "instruction": disposal_decision.instruction or rule["disposal"]["instruction"],
        },
        evidence=normalized.evidence,
    )
    _apply_safety_hints(result, normalized.safetyHints)
    result.decisions["disposal"] = disposal_decision
    result.decisions = {key: value for key, value in result.decisions.items() if key in SERVICE_KEYS}
    result.decisions["disposal"] = disposal_decision
    result.overallRisk = max((decision.status for decision in result.decisions.values()), key=lambda status: RISK_ORDER[status])
    result.confidence = build_confidence_report(result, normalized)
    apply_conservative_conflict_policy(result)
    return result


def detect_contamination_level(normalized: NormalizedInput) -> str:
    text = " ".join(
        [
            normalized.userQuery,
            normalized.itemName,
            normalized.ocrText,
            str(normalized.evidence.get("vision", "") if isinstance(normalized.evidence, dict) else ""),
        ]
    )
    compact = "".join(text.casefold().split())

    if any(keyword in compact for keyword in ["깨끗", "세척된", "씻은", "헹군", "clean"]):
        return "CLEAN"
    if any(keyword in compact for keyword in ["기름이많이", "기름많이", "오염이심", "오염심", "세척이어려", "찌든", "heavy"]):
        return "HEAVY_CONTAMINATION"
    if any(keyword in compact for keyword in ["음식물이묻", "소스", "기름묻", "국물묻", "묻은", "잔여물", "residue"]):
        if any(keyword in compact for keyword in ["많이", "심하", "어려"]):
            return "HEAVY_CONTAMINATION"
        return "LIGHT_CONTAMINATION"
    if normalized.visionHasFoodResidue:
        return "LIGHT_CONTAMINATION"
    if normalized.contaminationLevel in {"CLEAN", "LIGHT_CONTAMINATION", "HEAVY_CONTAMINATION"}:
        return normalized.contaminationLevel
    return "UNKNOWN_CONTAMINATION"


def _build_disposal_decision(category: str, instruction: str, contamination_level: str, region: str) -> Decision:
    if contamination_level == "CLEAN":
        return Decision(
            status="SAFE",
            label="분리수거",
            allowed=True,
            category=category,
            reason="오염이 거의 없어 재질별 분리수거가 가능합니다.",
            why="분리배출 가능 여부는 재질과 오염도를 함께 봅니다. 깨끗한 용기와 포장재는 재활용 선별 가능성이 높습니다.",
            instruction=f"내용물을 비우고 라벨을 제거한 뒤 {category}으로 배출하세요.",
            alternative=instruction,
        )
    if contamination_level == "LIGHT_CONTAMINATION":
        return Decision(
            status="WARNING",
            label="분리수거",
            allowed=True,
            category=category,
            reason="음식물이 조금 묻어 있어 세척 후 배출해야 합니다.",
            why="가벼운 오염은 헹굼으로 제거할 수 있어 재질별 분리배출이 가능합니다.",
            instruction=f"내용물을 비우고 가볍게 헹군 뒤 {category}으로 배출하세요.",
            alternative="세척이 어렵거나 오염이 심하면 일반쓰레기로 배출하세요.",
        )
    if contamination_level == "HEAVY_CONTAMINATION":
        return Decision(
            status="WARNING",
            label="분리수거",
            allowed=False,
            category="일반쓰레기",
            reason="오염이 심해 재활용이 어렵습니다.",
            why="기름이나 음식물이 많이 밴 포장재는 선별과 재활용 공정에서 품질 문제를 만들 수 있습니다.",
            instruction="오염이 심해 재활용이 어렵습니다. 일반쓰레기로 배출하세요.",
            alternative="세척으로 오염을 충분히 제거할 수 있다면 재질별 분리배출을 선택하세요.",
        )
    return Decision(
        status="WARNING",
        label="분리수거",
        allowed=True,
        category=category,
        reason="오염 정도가 명확하지 않습니다.",
        why="오염도를 알 수 없으면 세척 가능 여부에 따라 분리배출과 일반쓰레기를 나누는 것이 안전합니다.",
        instruction="오염 정도가 명확하지 않습니다. 세척 가능하면 분리배출하고, 어렵다면 일반쓰레기로 배출하세요.",
        alternative=instruction or _region_message(region, category),
    )
