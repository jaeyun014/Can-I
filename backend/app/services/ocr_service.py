from __future__ import annotations

import re
from io import BytesIO

from PIL import Image
from pytesseract import image_to_string

from app.models.schemas import OCRResult

MATERIAL_SYMBOLS = {
    "PP": "pp",
    "PET": "pet",
    "PS": "ps",
    "HDPE": "hdpe",
    "LDPE": "ldpe",
    "ABS": "abs",
    "OTHER": "other",
}

SAFETY_PATTERNS = {
    "microwave_safe": [r"microwave\s*safe", r"전자레인지\s*사용\s*가능"],
    "microwave_unsafe": [r"microwave\s*(unsafe|not safe)", r"전자레인지\s*사용\s*금지"],
    "dishwasher_safe": [r"dishwasher\s*safe", r"식기세척기\s*가능"],
    "freezer_safe": [r"freezer\s*safe", r"냉동\s*가능"],
    "oven_safe": [r"oven\s*safe", r"오븐\s*가능"],
}


def _extract_symbols(text: str) -> tuple[list[str], list[str], list[str]]:
    upper_text = text.upper()
    detected_symbols: list[str] = []
    material_hints: list[str] = []

    for symbol, material in MATERIAL_SYMBOLS.items():
        if re.search(rf"\b{symbol}\b", upper_text):
            detected_symbols.append(symbol)
            material_hints.append(material)

    safety_hints: list[str] = []
    lower_text = text.lower()
    for hint, patterns in SAFETY_PATTERNS.items():
        if any(re.search(pattern, lower_text, re.IGNORECASE) for pattern in patterns):
            safety_hints.append(hint)
            detected_symbols.append(hint.replace("_", " "))

    return detected_symbols, material_hints, safety_hints


def extract_text_from_image_bytes(image_bytes: bytes) -> OCRResult:
    """Run OCR when Tesseract is available; return an empty result if it is not."""
    try:
        image = Image.open(BytesIO(image_bytes))
        try:
            raw_text = image_to_string(image, lang="eng+kor").strip()
        except Exception:
            raw_text = image_to_string(image, lang="eng").strip()
    except Exception:
        raw_text = ""

    detected_symbols, material_hints, safety_hints = _extract_symbols(raw_text)
    return OCRResult(
        rawText=raw_text,
        detectedSymbols=detected_symbols,
        materialHints=material_hints,
        safetyHints=safety_hints,
    )
