from __future__ import annotations

from app.models.schemas import AnalyzeResponse, NormalizedInput
from app.services.rule_engine import analyze_food_item
from app.services.confidence_service import apply_conservative_conflict_policy, build_confidence_report


def analyze_food(normalized: NormalizedInput) -> AnalyzeResponse:
    result = analyze_food_item(
        item_name=normalized.itemName,
        region=normalized.region,
        object_type=normalized.objectType,
        detected_material=normalized.material,
        ocr_text=normalized.ocrText,
    )
    if result is None:
        result = analyze_food_item(
            item_name=normalized.itemName or normalized.userQuery or "음식",
            region=normalized.region,
            object_type="food",
            detected_material="food",
            ocr_text=normalized.ocrText,
        )
    if result is None:
        result = AnalyzeResponse(
            targetType="FOOD",
            itemName=normalized.itemName or "음식",
            summary="음식으로 분류되었지만 세부 음식 종류를 특정하지 못했습니다.",
            detectedMaterial="food",
            objectType="food",
            ocrText=normalized.ocrText,
            region=normalized.region,
        )
    result.targetType = "FOOD"
    result.detectedMaterial = "food"
    result.materialCode = ""
    result.decisions = {key: value for key, value in result.decisions.items() if key in {"refrigerator", "freezer", "foodWaste", "generalWaste"}}
    result.evidence = normalized.evidence
    if not result.summary:
        result.summary = "음식 기준으로 냉장, 냉동, 폐기 방법을 판단했습니다."
    result.confidence = build_confidence_report(result, normalized)
    apply_conservative_conflict_policy(result)
    return result
