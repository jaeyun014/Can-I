from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from app.models.schemas import OCRResult, VisionResult

TargetType = Literal["FOOD", "MATERIAL_OBJECT", "AMBIGUOUS", "UNKNOWN"]
ConfidenceLevel = Literal["LOW", "MEDIUM", "HIGH"]

FOOD_KEYWORDS = {
    "밥",
    "치킨",
    "피자",
    "떡볶이",
    "김밥",
    "국",
    "찌개",
    "고기",
    "생선",
    "과일",
    "채소",
    "야채",
    "우유",
    "계란",
    "달걀",
    "두부",
    "빵",
    "음식",
    "반찬",
    "먹다남은",
    "먹다 남은",
    "배달음식",
    "배달 음식",
    "컵라면",
    "햇반",
    "라면",
    "noodle",
    "noodles",
    "rice",
    "chicken",
    "pizza",
    "soup",
    "meat",
    "fish",
    "fruit",
    "vegetable",
    "milk",
    "egg",
    "tofu",
    "bread",
    "food",
    "leftover",
    "meal",
}

MATERIAL_KEYWORDS = {
    "pp",
    "pet",
    "ps",
    "hdpe",
    "ldpe",
    "other",
    "aluminum",
    "aluminium",
    "glass",
    "paper",
    "metal",
    "plastic",
    "battery",
    "cup",
    "container",
    "bottle",
    "wrap",
    "foil",
    "용기",
    "컵",
    "병",
    "포장재",
    "포장",
    "보조배터리",
    "텀블러",
    "플라스틱",
    "금속",
    "유리",
    "종이",
    "호일",
    "박스",
    "비닐",
    "스티로폼",
    "분리수거",
    "분리배출",
    "재활용",
    "음식물이묻은",
    "음식물이 묻은",
    "기름묻은",
    "기름 묻은",
    "국물묻은",
    "국물이 묻은",
}

MATERIAL_CODES = {"pp", "pet", "ps", "hdpe", "ldpe", "other"}
SAFETY_HINT_MARKERS = {"microwave", "dishwasher", "freezer", "oven", "safe", "unsafe"}
FOOD_INTENT_KEYWORDS = {
    "보관",
    "섭취",
    "먹어도",
    "먹다",
    "상함",
    "상한",
    "상했",
    "냉장",
    "냉동",
    "며칠",
    "유통기한",
    "소비기한",
    "개봉 후",
    "개봉후",
    "음식물쓰레기",
    "음쓰",
}


@dataclass
class TargetClassification:
    targetType: TargetType
    confidenceLevel: ConfidenceLevel
    reason: str
    evidence: dict[str, object]
    options: list[dict[str, str]] | None = None
    message: str = ""


def classify_target(
    *,
    user_input: str = "",
    vision: VisionResult | None = None,
    ocr: OCRResult | None = None,
    barcode_product: dict[str, object] | None = None,
    force_target_type: str | None = None,
) -> TargetClassification:
    evidence = {
        "userInput": user_input.strip(),
        "visionObject": _vision_object(vision),
        "ocrText": ocr.rawText if ocr else "",
        "barcodeProduct": barcode_product.get("productName") if barcode_product else None,
    }

    if force_target_type in {"FOOD", "MATERIAL_OBJECT"}:
        return TargetClassification(
            targetType=force_target_type,  # type: ignore[arg-type]
            confidenceLevel="HIGH",
            reason="forceTargetType 요청이 있어 분류 로직과 AMBIGUOUS 판단을 건너뛰었습니다.",
            evidence=evidence,
        )

    user_food = _contains_food(user_input)
    user_food_intent = user_food and _has_food_intent(user_input)
    user_material = _contains_material(user_input)
    ocr_material = _ocr_has_material_signal(ocr)
    ocr_safety = bool(ocr and ocr.safetyHints)
    barcode_food = _product_is_food(barcode_product)
    barcode_material = _product_is_material(barcode_product)
    vision_food = _vision_is_food(vision)
    vision_material = _vision_is_material(vision)
    standalone_food = vision_food and not vision_material and not ocr_material and not ocr_safety and not barcode_material

    if user_food_intent and not (ocr_material or ocr_safety):
        return TargetClassification("FOOD", "HIGH", "사용자 입력에서 음식 보관/섭취 의도가 명확하게 감지되었습니다.", evidence)
    if ocr_material or ocr_safety:
        reason = "OCR에서 재질 코드가 인식되어 용기/재질 판단 대상으로 분류되었습니다."
        if ocr_safety and not ocr_material:
            reason = "OCR에서 안전 표기가 인식되어 용기/재질 판단 대상으로 분류되었습니다."
        return TargetClassification("MATERIAL_OBJECT", "HIGH", reason, evidence)
    if user_material:
        return TargetClassification("MATERIAL_OBJECT", "HIGH", "사용자 입력에서 용기/재질/포장재 키워드가 감지되었습니다.", evidence)
    if barcode_material:
        return TargetClassification("MATERIAL_OBJECT", "HIGH", "바코드 제품 정보에서 재질 정보가 확인되었습니다.", evidence)
    if vision_material:
        return TargetClassification("MATERIAL_OBJECT", "MEDIUM", "GPT Vision 보조 분석에서 용기/재질 대상으로 추정되었습니다.", evidence)
    if user_food and not user_material:
        return TargetClassification("FOOD", "HIGH", "사용자 입력이 음식 자체만 가리키고 있습니다.", evidence)
    if standalone_food or (barcode_food and not barcode_material):
        return TargetClassification("FOOD", "MEDIUM", "음식이 단독 대상으로 인식되었습니다.", evidence)

    return TargetClassification(
        targetType="AMBIGUOUS",
        confidenceLevel="LOW",
        reason="음식인지 용기/재질인지 식별할 근거가 부족합니다.",
        evidence=evidence,
        options=[
            {"type": "MATERIAL_OBJECT", "label": "분리수거/용기 판단"},
            {"type": "FOOD", "label": "음식 보관/음식물 판단"},
        ],
        message="판단 대상이 명확하지 않습니다. 기본적으로 분리수거/용기 판단을 추천합니다.",
    )


def _vision_object(vision: VisionResult | None) -> str:
    if not vision:
        return ""
    parts = [vision.itemName, vision.objectType, vision.detectedMaterial, vision.materialCodeGuess]
    return " ".join(part for part in parts if part and part != "unknown")


def _normalized(text: str) -> str:
    return text.casefold().replace(" ", "")


def _contains_any(text: str, keywords: set[str]) -> bool:
    normalized = _normalized(text)
    lowered = text.casefold()
    return any(_normalized(keyword) in normalized or keyword in lowered for keyword in keywords)


def _contains_food(text: str) -> bool:
    return _contains_any(text, FOOD_KEYWORDS)


def _has_food_intent(text: str) -> bool:
    return _contains_any(text, FOOD_INTENT_KEYWORDS)


def _contains_material(text: str) -> bool:
    return _contains_any(text, MATERIAL_KEYWORDS)


def _ocr_has_material_signal(ocr: OCRResult | None) -> bool:
    if not ocr:
        return False
    if ocr.materialHints:
        return True
    return any(re.search(rf"\b{code}\b", ocr.rawText, re.IGNORECASE) for code in MATERIAL_CODES)


def _vision_is_food(vision: VisionResult | None) -> bool:
    return bool(
        vision
        and not vision.hasContainerOrPackage
        and (vision.isStandaloneFood or vision.detectedMaterial == "food" or _contains_food(_vision_object(vision)))
    )


def _vision_is_material(vision: VisionResult | None) -> bool:
    return bool(vision and (vision.hasContainerOrPackage or (vision.detectedMaterial != "food" and _contains_material(_vision_object(vision)))))


def _product_is_food(product: dict[str, object] | None) -> bool:
    if not product:
        return False
    return _contains_food(str(product.get("productName", "")))


def _product_is_material(product: dict[str, object] | None) -> bool:
    if not product:
        return False
    materials = product.get("materials")
    has_materials = isinstance(materials, dict) and any(str(value).strip() for value in materials.values())
    return has_materials or _contains_material(str(product.get("productName", "")))
