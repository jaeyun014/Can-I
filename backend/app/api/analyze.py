from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.models.schemas import AnalyzeResponse, AuthUser, TextAnalyzeRequest, UsageLogCreate
from app.api.logs import create_log
from app.services.auth_service import get_optional_user
from app.services.input_normalizer import normalize_image_input
from app.services.ocr_service import extract_text_from_image_bytes
from app.services.rule_engine import analyze_item, analyze_normalized
from app.services.vision_service import analyze_image_with_vision

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_text(payload: TextAnalyzeRequest) -> AnalyzeResponse:
    return analyze_item(item_name=payload.query, region=payload.region)


@router.post("/analyze/image", response_model=AnalyzeResponse)
async def analyze_image(
    file: UploadFile = File(...),
    region: str = Form(default="서울"),
    itemName: str = Form(default=""),
    user: Optional[AuthUser] = Depends(get_optional_user),
) -> AnalyzeResponse:
    image_bytes = await file.read()
    ocr_result = extract_text_from_image_bytes(image_bytes)
    vision_result = await analyze_image_with_vision(image_bytes, file.content_type)
    normalized = normalize_image_input(
        vision=vision_result,
        ocr=ocr_result,
        region=region,
        user_query=itemName,
    )
    result = analyze_normalized(normalized)
    create_log(
        UsageLogCreate(
            itemName=result.itemName,
            detectedMaterial=result.detectedMaterial,
            region=result.region,
            overallRisk=result.overallRisk,
        ),
        user=user,
    )
    return result
