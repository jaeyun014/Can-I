from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.models.schemas import AnalyzeResponse, NormalizedInput
from app.services.confidence_service import apply_conservative_conflict_policy, build_confidence_report

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SERVICE_KEYS = ["microwave", "airFryer", "oven", "freezer", "dishwasher"]
FOOD_SERVICE_KEYS = ["freezer", "refrigerator", "foodWaste", "generalWaste"]
RISK_ORDER = {"SAFE": 0, "WARNING": 1, "DANGER": 2}

FOOD_RULES: list[dict[str, Any]] = [
    {
        "itemName": "밥",
        "aliases": ["밥", "쌀밥", "흰밥", "잡곡밥", "햇반"],
        "freezer": "SAFE",
        "refrigerator": "WARNING",
        "disposalCategory": "음식물쓰레기",
        "storage": "소분해서 밀폐한 뒤 빠르게 식혀 냉동 보관하는 편이 좋습니다.",
        "waste": "상한 밥은 물기를 줄여 음식물쓰레기로 배출하세요.",
    },
    {
        "itemName": "국물 음식",
        "aliases": ["국", "찌개", "탕", "국물", "스프", "수프", "카레"],
        "freezer": "SAFE",
        "refrigerator": "SAFE",
        "disposalCategory": "음식물쓰레기",
        "storage": "완전히 식힌 뒤 밀폐 용기에 담아 냉장 또는 소분 냉동하세요.",
        "waste": "액체는 최대한 따라내고 건더기는 음식물쓰레기로 배출하세요.",
    },
    {
        "itemName": "고기",
        "aliases": ["고기", "소고기", "돼지고기", "닭고기", "육류", "생선", "해산물"],
        "freezer": "SAFE",
        "refrigerator": "WARNING",
        "disposalCategory": "음식물쓰레기",
        "storage": "바로 먹지 않을 생고기와 생선은 밀봉해 냉동 보관하는 편이 안전합니다.",
        "waste": "뼈, 조개껍데기처럼 딱딱한 부산물은 일반쓰레기로 따로 배출하세요.",
    },
    {
        "itemName": "채소",
        "aliases": ["채소", "야채", "상추", "양파", "당근", "오이", "대파", "과일", "사과", "바나나"],
        "freezer": "WARNING",
        "refrigerator": "SAFE",
        "disposalCategory": "음식물쓰레기",
        "storage": "대부분 냉장 보관이 적합하고, 냉동하면 식감이 크게 바뀔 수 있습니다.",
        "waste": "먹을 수 없는 껍질과 씨는 지역 기준에 따라 음식물 또는 일반쓰레기로 나누세요.",
    },
    {
        "itemName": "뼈 또는 껍데기",
        "aliases": ["뼈", "닭뼈", "돼지뼈", "소뼈", "조개껍데기", "달걀껍데기", "계란껍데기", "복숭아씨"],
        "freezer": "WARNING",
        "refrigerator": "WARNING",
        "disposalCategory": "일반쓰레기",
        "storage": "보관 대상 음식이라기보다 폐기 대상이면 밀봉해 냄새가 나지 않게 처리하세요.",
        "waste": "동물이 먹기 어려운 단단한 뼈, 껍데기, 큰 씨앗은 일반쓰레기로 배출하세요.",
    },
]


@lru_cache
def _load_json(filename: str) -> dict[str, Any]:
    path = DATA_DIR / filename
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _normalize(text: str) -> str:
    return "".join(text.lower().split())


def _matches_alias(normalized_query: str, aliases: list[str]) -> bool:
    normalized_aliases = [_normalize(alias) for alias in aliases]
    return normalized_query in normalized_aliases or any(alias in normalized_query for alias in normalized_aliases)


def _find_rule(item_name: str, detected_material: str | None = None) -> dict[str, Any] | None:
    rules = _load_json("material_rules.json")["items"]
    normalized_query = _normalize(item_name)

    for rule in rules:
        if _matches_alias(normalized_query, rule["aliases"]):
            return rule

    for rule in rules:
        material = rule["detectedMaterial"]
        if detected_material and detected_material == material:
            return rule
    return None


def _find_food_rule(item_name: str, object_type: str = "", detected_material: str | None = None) -> dict[str, Any] | None:
    normalized_query = _normalize(item_name)
    for rule in FOOD_RULES:
        if _matches_alias(normalized_query, rule["aliases"]):
            return rule

    food_markers = {"food", "meal", "fruit", "vegetable", "meat", "seafood", "leftover_food"}
    normalized_type = _normalize(object_type)
    if detected_material == "food" or any(marker in normalized_type for marker in food_markers):
        return {
            "itemName": item_name or "음식",
            "aliases": [],
            "freezer": "WARNING",
            "refrigerator": "WARNING",
            "disposalCategory": "음식물쓰레기",
            "storage": "음식 종류가 명확하지 않아 냉장 또는 냉동 가능 여부를 보수적으로 확인해야 합니다.",
            "waste": "뼈, 껍데기, 큰 씨앗처럼 동물이 먹기 어려운 부분은 일반쓰레기로 분리하세요.",
        }
    return None


def _fallback_rule(item_name: str) -> dict[str, Any]:
    unknown_decision = {
        "status": "WARNING",
        "allowed": False,
        "reason": "아직 등록되지 않은 물건이라 정확한 안전 판단이 어렵습니다.",
        "why": "재질과 코팅 여부에 따라 가열, 냉동, 세척 가능 여부가 크게 달라질 수 있습니다.",
        "alternative": "재질 표기, 제품 설명서, 안전 마크를 확인하세요. 불확실하면 가열하지 않는 것이 안전합니다.",
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
    "음식물쓰레기": "food_waste",
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
    if mapped_key == "food_waste":
        return selected.get(category) or selected.get(mapped_key) or f"{region} 기준, 물기를 줄이고 이물질을 제거한 뒤 음식물쓰레기 배출 기준을 확인하세요."
    return selected.get(category) or selected.get(mapped_key) or selected["default"]


def _food_decision(status: str, label: str, allowed: bool, reason: str, why: str, alternative: str) -> dict[str, Any]:
    return {
        "status": status,
        "label": label,
        "allowed": allowed,
        "reason": reason,
        "why": why,
        "alternative": alternative,
    }


def analyze_food_item(item_name: str, region: str, object_type: str = "", detected_material: str | None = None, ocr_text: str = "") -> AnalyzeResponse | None:
    food_rule = _find_food_rule(item_name, object_type, detected_material)
    if not food_rule:
        return None

    freezer_status = food_rule["freezer"]
    refrigerator_status = food_rule["refrigerator"]
    category = food_rule["disposalCategory"]
    decisions = {
        "freezer": _food_decision(
            freezer_status,
            "냉동 보관",
            freezer_status != "DANGER",
            food_rule["storage"] if freezer_status == "SAFE" else "냉동은 가능할 수 있지만 맛, 식감, 위생 상태를 확인해야 합니다.",
            "음식은 종류, 수분량, 조리 여부에 따라 냉동 후 품질 변화와 해동 안전성이 달라집니다.",
            "빠르게 먹을 예정이면 냉장, 오래 보관할 예정이면 1회분씩 소분해 냉동하세요.",
        ),
        "refrigerator": _food_decision(
            refrigerator_status,
            "냉장 보관",
            refrigerator_status != "DANGER",
            food_rule["storage"] if refrigerator_status == "SAFE" else "냉장은 단기 보관에 가깝고 오래 두면 변질될 수 있습니다.",
            "냉장은 세균 증식을 늦추지만 멈추지는 못하므로 조리 상태와 보관 시간을 함께 봐야 합니다.",
            "냄새, 점액, 곰팡이, 색 변화가 있으면 먹지 말고 폐기하세요.",
        ),
        "foodWaste": _food_decision(
            "SAFE" if category == "음식물쓰레기" else "WARNING",
            "음식물쓰레기",
            category == "음식물쓰레기",
            "음식물쓰레기로 배출 가능한 성격입니다." if category == "음식물쓰레기" else "동물이 먹기 어려운 부분은 음식물쓰레기로 배출하지 않습니다.",
            "음식물쓰레기는 사료화나 퇴비화 가능성을 기준으로 나누는 경우가 많아 단단한 뼈와 껍데기는 제외됩니다.",
            food_rule["waste"],
        ),
        "generalWaste": _food_decision(
            "SAFE" if category == "일반쓰레기" else "WARNING",
            "일반쓰레기",
            category == "일반쓰레기",
            "일반쓰레기로 배출하는 편이 적합합니다." if category == "일반쓰레기" else "먹을 수 있는 음식 부분은 일반쓰레기보다 음식물쓰레기 기준을 먼저 확인하세요.",
            "뼈, 껍데기, 큰 씨앗, 이쑤시개 등 처리 시설에 부담이 되는 것은 일반쓰레기로 분리합니다.",
            "음식물과 포장재, 딱딱한 부산물을 분리해 배출하세요.",
        ),
    }
    highest_risk = max((decision["status"] for decision in decisions.values()), key=lambda status: RISK_ORDER[status])
    return AnalyzeResponse(
        itemName=food_rule["itemName"],
        detectedMaterial="food",
        objectType=object_type or "food",
        ocrText=ocr_text,
        region=region,
        overallRisk=highest_risk,
        decisions=decisions,
        disposal={
            "category": category,
            "regionRule": _region_message(region, category),
            "instruction": food_rule["waste"],
        },
    )


def analyze_item(item_name: str, region: str, detected_material: str | None = None, ocr_text: str = "") -> AnalyzeResponse:
    """Analyze an item with JSON rules, keeping AI output out of final judgment."""
    text_context = NormalizedInput(
        itemName=item_name or "알 수 없는 물건",
        material=detected_material or "unknown",
        region=region,
        ocrText=ocr_text,
        userQuery=item_name,
    )
    food_result = analyze_food_item(item_name=item_name, region=region, detected_material=detected_material, ocr_text=ocr_text)
    if food_result:
        food_result.confidence = build_confidence_report(food_result, text_context)
        return food_result

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
    result = AnalyzeResponse(
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
    result.confidence = build_confidence_report(result, text_context)
    return result


def analyze_normalized(normalized: NormalizedInput) -> AnalyzeResponse:
    food_result = analyze_food_item(
        item_name=normalized.itemName,
        region=normalized.region,
        object_type=normalized.objectType,
        detected_material=normalized.material,
        ocr_text=normalized.ocrText,
    )
    if food_result:
        food_result.evidence = normalized.evidence
        if not food_result.evidence.rule:
            food_result.evidence.rule = "food_storage_rule 규칙과 매칭되었습니다."
        food_result.confidence = build_confidence_report(food_result, normalized)
        apply_conservative_conflict_policy(food_result)
        return food_result

    result = analyze_item(
        item_name=normalized.itemName,
        region=normalized.region,
        detected_material=normalized.material,
        ocr_text=normalized.ocrText,
    )
    _apply_safety_hints(result, normalized.safetyHints)
    result.objectType = normalized.objectType
    result.evidence = normalized.evidence
    result.confidence = build_confidence_report(result, normalized)
    apply_conservative_conflict_policy(result)
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
