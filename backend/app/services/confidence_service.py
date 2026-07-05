from __future__ import annotations

from typing import Iterable

from app.models.schemas import AnalyzeResponse, ConfidenceFactor, ConfidenceReport, NormalizedInput

PRIORITY = [
    "사용자 입력",
    "OCR 안전 표기",
    "OCR 재질 표기",
    "바코드 제품 DB",
    "GPT Vision",
    "unknown fallback",
]

MATERIAL_BY_KEYWORD = {
    "종이컵": "paper_coated",
    "컵": "paper_coated",
    "호일": "aluminum",
    "포일": "aluminum",
    "은박지": "aluminum",
    "페트병": "pet",
    "생수병": "pet",
    "배달용기": "pp",
    "플라스틱용기": "pp",
    "유리": "glass",
    "글라스락": "glass",
    "보조배터리": "lithium_battery",
    "배터리": "lithium_battery",
    "나무젓가락": "wood",
    "젓가락": "wood",
}

HEAT_INTENT_LABELS = {"전자레인지", "에어프라이어", "오븐"}


def _normalize(text: str) -> str:
    return "".join(text.lower().split())


def _expected_material_from_user_query(user_query: str) -> str:
    normalized = _normalize(user_query)
    for keyword, material in MATERIAL_BY_KEYWORD.items():
        if _normalize(keyword) in normalized:
            return material
    return ""


def _is_known_vision(normalized: NormalizedInput | None) -> bool:
    if not normalized:
        return False
    return normalized.visionItemName not in {"", "알 수 없는 물건"} or normalized.visionMaterial not in {"", "unknown"}


def _has_rule_match(result: AnalyzeResponse) -> bool:
    return result.detectedMaterial != "unknown" and result.disposal.category != "확인 필요"


def _has_combo_match(result: AnalyzeResponse, normalized: NormalizedInput | None) -> bool:
    material = result.detectedMaterial
    object_type = _normalize(result.objectType or (normalized.objectType if normalized else ""))
    safety_hints = set(normalized.safetyHints if normalized else [])
    intent_labels = {decision.label for decision in result.decisions.values()}

    return any(
        [
            material == "pp" and "food" in object_type and "microwave_safe" in safety_hints,
            material == "pp" and "food" in object_type,
            material == "glass" and bool({"microwave_safe", "oven_safe"} & safety_hints),
            material == "glass" and "decorative" in object_type,
            material in {"aluminum", "metal"} and "전자레인지" in intent_labels,
            material == "lithium_battery" and result.disposal.category in {"소형폐가전", "확인 필요"},
            material == "unknown" and bool(HEAT_INTENT_LABELS & intent_labels),
            material == "food" and bool({"냉동 보관", "냉장 보관"} & intent_labels),
        ]
    )


def _detect_conflicts(result: AnalyzeResponse, normalized: NormalizedInput | None) -> list[str]:
    if not normalized:
        return []

    conflicts: list[str] = []
    user_expected_material = _expected_material_from_user_query(normalized.userQuery)

    if user_expected_material and normalized.visionMaterial not in {"", "unknown", user_expected_material}:
        conflicts.append("사용자 입력 물건명과 GPT Vision 추정 재질이 서로 다릅니다.")

    if normalized.ocrMaterialHints and normalized.visionMaterial not in {"", "unknown"}:
        ocr_material = normalized.ocrMaterialHints[0]
        if ocr_material != normalized.visionMaterial:
            conflicts.append("OCR 재질과 GPT Vision 추정 재질이 서로 다릅니다.")

    if normalized.barcodeMaterial and normalized.visionMaterial not in {"", "unknown", normalized.barcodeMaterial}:
        conflicts.append("바코드 제품 정보와 GPT Vision 결과가 서로 다릅니다.")

    if "microwave_safe" in normalized.safetyHints:
        microwave = result.decisions.get("microwave")
        if microwave and microwave.status == "DANGER":
            conflicts.append("OCR 안전 표기와 전자레인지 Rule Engine 결과가 충돌합니다.")

    if "microwave_unsafe" in normalized.safetyHints:
        microwave = result.decisions.get("microwave")
        if microwave and microwave.status == "SAFE":
            conflicts.append("OCR 사용 금지 표기와 전자레인지 Rule Engine 결과가 충돌합니다.")

    normalized_user_item = _normalize(normalized.userQuery)
    normalized_vision_item = _normalize(normalized.visionItemName)
    if normalized_user_item and normalized_vision_item and normalized_vision_item != _normalize("알 수 없는 물건"):
        if normalized_user_item not in normalized_vision_item and normalized_vision_item not in normalized_user_item:
            if user_expected_material and normalized.visionMaterial not in {"", "unknown", user_expected_material}:
                conflicts.append("사용자 입력 물건명과 GPT Vision 물체명이 크게 다릅니다.")

    return list(dict.fromkeys(conflicts))


def _append_factor(factors: list[ConfidenceFactor], label: str, score: int, reason: str) -> None:
    factors.append(ConfidenceFactor(label=label, score=score, reason=reason))


def _calculation(parts: Iterable[int], total: int) -> str:
    values = list(parts)
    if not values:
        return f"0 = {total}"
    expression = " ".join(
        f"+ {value}" if index > 0 and value >= 0 else str(value)
        for index, value in enumerate(values)
    )
    return f"{expression} = {total}"


def _level(score: int) -> str:
    if score >= 70:
        return "HIGH"
    if score >= 40:
        return "MEDIUM"
    return "LOW"


def _summary(level: str, conflict_detected: bool, unknown_used: bool) -> str:
    if conflict_detected:
        return "근거가 서로 달라 신뢰도가 낮습니다."
    if unknown_used:
        return "명확한 물건명, 재질 표기, Vision 근거가 부족해 신뢰도가 낮습니다."
    if level == "HIGH":
        return "여러 근거가 일치하여 비교적 신뢰도가 높습니다."
    if level == "MEDIUM":
        return "일부 정보가 불확실합니다. 재질 표기나 제품명을 확인하세요."
    return "신뢰도가 낮습니다. 사진을 다시 찍거나 물건명을 직접 입력하면 더 정확해집니다."


def build_confidence_report(result: AnalyzeResponse, normalized: NormalizedInput | None = None) -> ConfidenceReport:
    factors: list[ConfidenceFactor] = []
    penalties: list[ConfidenceFactor] = []
    low_reasons: list[str] = []

    if normalized and normalized.ocrMaterialHints:
        _append_factor(factors, "OCR 재질 인식", 30, f"이미지에서 {normalized.ocrMaterialHints[0]} 재질 표기를 인식했습니다.")
    else:
        low_reasons.append("OCR 재질 표기가 명확히 인식되지 않았습니다.")

    if normalized and normalized.safetyHints:
        _append_factor(factors, "OCR 안전 표기 인식", 35, "이미지에서 안전 사용 표기를 인식했습니다.")
    else:
        low_reasons.append("제품의 안전 표기가 명확히 인식되지 않았습니다.")

    if normalized and normalized.barcodeProductName:
        _append_factor(factors, "바코드 제품명 매칭", 30, f"{normalized.barcodeProductName} 제품 정보와 매칭되었습니다.")

    if normalized and normalized.userQuery:
        _append_factor(factors, "사용자 직접 입력", 25, f"사용자가 '{normalized.userQuery}' 물건명을 직접 입력했습니다.")

    if _is_known_vision(normalized):
        _append_factor(factors, "GPT Vision 객체 인식", 20, f"GPT Vision이 {normalized.visionItemName or normalized.visionMaterial}로 추정했습니다.")
    elif normalized is not None:
        low_reasons.append("GPT Vision이 물체나 재질을 충분히 확신하지 못했습니다.")

    if _has_rule_match(result):
        _append_factor(factors, "Rule Engine 정확 매칭", 40, f"{result.detectedMaterial} 규칙과 매칭되었습니다.")

    if _has_combo_match(result, normalized):
        _append_factor(factors, "재질 + 용도 조합 규칙 매칭", 25, "재질, 용도, 안전 표기 조합 규칙이 매칭되었습니다.")

    unknown_used = result.detectedMaterial == "unknown"
    if unknown_used:
        _append_factor(penalties, "unknown fallback 사용", -35, "물건명, OCR, 바코드, Vision 모두 명확하지 않아 unknown fallback을 사용했습니다.")
        low_reasons.append("최종 재질이 unknown으로 처리되었습니다.")

    conflicts = _detect_conflicts(result, normalized)
    if conflicts:
        _append_factor(penalties, "근거 충돌", -30, conflicts[0])
        low_reasons.extend(conflicts)

    raw_scores = [factor.score for factor in factors] + [penalty.score for penalty in penalties]
    total = max(0, min(100, sum(raw_scores)))
    if conflicts:
        total = min(total, 69)
    if unknown_used:
        total = min(total, 39)
    level = _level(total)
    if level == "HIGH" and not conflicts and not unknown_used:
        low_reasons = []

    return ConfidenceReport(
        score=total,
        level=level,
        summary=_summary(level, bool(conflicts), unknown_used),
        factors=factors,
        penalties=penalties,
        calculation=_calculation(raw_scores, total),
        lowConfidenceReasons=list(dict.fromkeys(low_reasons)),
        priority=PRIORITY,
        conflictDetected=bool(conflicts),
    )


def apply_conservative_conflict_policy(result: AnalyzeResponse) -> None:
    if not result.confidence.conflictDetected:
        return
    for decision in result.decisions.values():
        if decision.status == "SAFE":
            decision.status = "WARNING"
            decision.allowed = False
            decision.reason = f"{decision.reason} 다만 분석 근거가 서로 달라 보수적으로 주의가 필요합니다."
            decision.alternative = "재질 표기, 제품 설명서, 안전 마크를 확인하세요. 불확실하면 가열하지 않는 것이 안전합니다."
    result.overallRisk = max((decision.status for decision in result.decisions.values()), key=lambda status: {"SAFE": 0, "WARNING": 1, "DANGER": 2}[status])
