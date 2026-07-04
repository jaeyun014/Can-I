from __future__ import annotations

import base64
import json

from openai import AsyncOpenAI

from app.core.config import settings
from app.models.schemas import VisionResult


def _fallback_result(notes: str) -> VisionResult:
    return VisionResult(
        itemName="플라스틱 배달 용기",
        detectedMaterial="pp",
        visibleLabels=[],
        objectType="food_container",
        confidence=0.0,
        notes=notes,
    )


async def analyze_image_with_vision(image_bytes: bytes, content_type: str | None) -> VisionResult:
    """Use GPT Vision only for extraction hints; the rule engine still decides safety."""
    if not settings.openai_api_key:
        return _fallback_result("AI 분석이 비활성화되어 규칙 기반으로 분석했습니다.")

    mime_type = content_type or "image/jpeg"
    image_data = base64.b64encode(image_bytes).decode("utf-8")
    data_url = f"data:{mime_type};base64,{image_data}"

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "itemName": {"type": "string"},
            "detectedMaterial": {"type": "string"},
            "visibleLabels": {"type": "array", "items": {"type": "string"}},
            "objectType": {"type": "string"},
            "confidence": {"type": "number"},
            "notes": {"type": "string"},
        },
        "required": ["itemName", "detectedMaterial", "visibleLabels", "objectType", "confidence", "notes"],
    }

    try:
        response = await client.responses.create(
            model=settings.vision_model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "이미지 속 물건과 재질 표기를 추출해 JSON으로만 답하세요. "
                                "최종 안전 판단은 하지 마세요. 재질이 불확실하면 detectedMaterial은 unknown으로 두세요. "
                                "가능한 재질 값: aluminum, pp, pet, ps, paper_coated, glass, lithium_battery, wood, unknown."
                            ),
                        },
                        {"type": "input_image", "image_url": data_url, "detail": "low"},
                    ],
                }
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "vision_extraction",
                    "schema": schema,
                    "strict": True,
                }
            },
        )
        payload = json.loads(response.output_text)
        result = VisionResult(**payload)
        if result.confidence < 0.55:
            result.detectedMaterial = "unknown"
            result.notes = f"{result.notes} 신뢰도가 낮아 재질을 unknown으로 처리했습니다."
        return result
    except Exception:
        return _fallback_result("GPT Vision 호출에 실패해 fallback 규칙 기반 분석을 사용했습니다.")
