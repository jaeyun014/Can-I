from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.models.schemas import AnalyzeResponse, NormalizedInput

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SERVICE_KEYS = ["microwave", "airFryer", "oven", "freezer", "dishwasher"]
RISK_ORDER = {"SAFE": 0, "WARNING": 1, "DANGER": 2}


@lru_cache
def _load_json(filename: str) -> dict[str, Any]:
    path = DATA_DIR / filename
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _normalize(text: str) -> str:
    return "".join(text.lower().split())


def _find_rule(item_name: str, detected_material: str | None = None) -> dict[str, Any] | None:
    rules = _load_json("material_rules.json")["items"]
    normalized_query = _normalize(item_name)

    for rule in rules:
        material = rule["detectedMaterial"]
        aliases = [_normalize(alias) for alias in rule["aliases"]]
        if detected_material and detected_material == material:
            return rule
        if normalized_query in aliases or any(alias in normalized_query for alias in aliases):
            return rule
    return None


def _fallback_rule(item_name: str) -> dict[str, Any]:
    unknown_decision = {
        "status": "WARNING",
        "allowed": False,
        "reason": "아직 등록되지 않은 물건이라 정확한 안전 판단이 어렵습니다.",
        "why": "재질과 코팅 여부에 따라 가열, 냉동, 세척 가능 여부가 크게 달라질 수 있습니다.",
        "alternative": "제품 표기나 제조사 안내를 확인하고, 확실하지 않다면 해당 기기 사용을 피하세요.",
    }
    return {
        "itemName": item_name or "알 수 없는 물건",
        "aliases": [],
        "detectedMaterial": "unknown",
        "decisions": {key: unknown_decision for key in SERVICE_KEYS},
        "disposal": {
            "category": "확인 필요",
            "instruction": "재질 표시를 확인한 뒤 지역 배출 기준에 따라 분리배출하세요.",
        },
    }


CATEGORY_KEYS = {
    "일반쓰레기": "general",
    "플라스틱": "plastic",
    "종이": "paper",
    "유리": "glass",
    "소형폐가전": "battery",
    "확인 필요": "default",
}


def _region_message(region: str, category: str) -> str:
    region_rules = _load_json("region_rules.json")
    selected = region_rules.get(region) or region_rules["서울"]
    mapped_key = CATEGORY_KEYS.get(category, category)
    return selected.get(category) or selected.get(mapped_key) or selected["default"]


def analyze_item(item_name: str, region: str, detected_material: str | None = None, ocr_text: str = "") -> AnalyzeResponse:
    """Analyze an item with JSON rules, keeping AI output out of final judgment."""
    rule = _find_rule(item_name, detected_material) or _fallback_rule(item_name)

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
    return AnalyzeResponse(
        itemName=rule["itemName"],
        detectedMaterial=rule["detectedMaterial"],
        ocrText=ocr_text,
        region=region,
        overallRisk=highest_risk,
        decisions=decisions,
        disposal={
            "category": category,
            "regionRule": _region_message(region, category),
            "instruction": rule["disposal"]["instruction"],
        },
    )


def analyze_normalized(normalized: NormalizedInput) -> AnalyzeResponse:
    result = analyze_item(
        item_name=normalized.itemName,
        region=normalized.region,
        detected_material=normalized.material,
        ocr_text=normalized.ocrText,
    )
    _apply_safety_hints(result, normalized.safetyHints)
    result.objectType = normalized.objectType
    result.confidence = normalized.confidence
    result.evidence = normalized.evidence
    return result


def _apply_safety_hints(result: AnalyzeResponse, safety_hints: list[str]) -> None:
    safe_hint_targets = {
        "microwave_safe": "microwave",
        "dishwasher_safe": "dishwasher",
        "freezer_safe": "freezer",
        "oven_safe": "oven",
    }
    danger_hint_targets = {
        "microwave_unsafe": "microwave",
    }

    for hint, key in safe_hint_targets.items():
        if hint in safety_hints and result.detectedMaterial in {"pp", "glass"}:
            decision = result.decisions[key]
            decision.status = "SAFE"
            decision.allowed = True
            decision.reason = f"{decision.label} 가능 표기가 확인되어 사용 가능성이 높습니다."
            decision.why = f"OCR에서 {hint.replace('_', ' ')} 표기를 확인했습니다. Rule Engine은 재질과 표기를 함께 보고 해당 조건에서 안전으로 보정했습니다."
            decision.alternative = "그래도 뚜껑, 패킹, 금속 부품은 제거하고 제조사 표기를 함께 확인하세요."

    for hint, key in danger_hint_targets.items():
        if hint in safety_hints:
            decision = result.decisions[key]
            decision.status = "DANGER"
            decision.allowed = False
            decision.reason = f"{decision.label} 사용 금지 표기가 확인되었습니다."
            decision.why = f"OCR에서 {hint.replace('_', ' ')} 표기를 확인했습니다. 사용 금지 표기는 제품 설계 기준이므로 Rule Engine이 위험으로 판단했습니다."
            decision.alternative = "해당 기기 사용을 피하고 제조사 안내에 맞는 용기를 사용하세요."

    result.overallRisk = max(
        (decision.status for decision in result.decisions.values()),
        key=lambda status: RISK_ORDER[status],
    )
