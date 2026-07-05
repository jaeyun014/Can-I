from __future__ import annotations

from app.models.schemas import Evidence, NormalizedInput, OCRResult, VisionResult


def normalize_image_input(vision: VisionResult, ocr: OCRResult, region: str, user_query: str = "") -> NormalizedInput:
    material = "unknown"
    matched_rule = "unknown_fallback"

    if ocr.materialHints:
        material = ocr.materialHints[0]
        matched_rule = f"{material}_from_ocr"
    elif ocr.safetyHints and vision.detectedMaterial != "unknown":
        material = vision.detectedMaterial
        matched_rule = f"{material}_with_safety_hint"
    elif vision.detectedMaterial != "unknown":
        material = vision.detectedMaterial
        matched_rule = f"{material}_from_vision"

    trimmed_user_query = user_query.strip()
    item_name = trimmed_user_query or (vision.itemName if vision.itemName != "알 수 없는 물건" else "알 수 없는 물건")
    ocr_summary = ocr.rawText or "OCR에서 명확한 문구를 찾지 못했습니다."
    vision_summary = vision.notes or "Vision 분석 근거가 없습니다."

    return NormalizedInput(
        itemName=item_name,
        material=material,
        objectType=vision.objectType,
        region=region,
        ocrText=ocr.rawText,
        safetyHints=ocr.safetyHints,
        userQuery=trimmed_user_query,
        visionItemName=vision.itemName,
        visionMaterial=vision.detectedMaterial,
        visionConfidence=vision.confidence,
        ocrMaterialHints=ocr.materialHints,
        evidence=Evidence(
            vision=vision_summary,
            ocr=ocr_summary,
            rule=f"{matched_rule} 규칙과 매칭되었습니다.",
        ),
    )
