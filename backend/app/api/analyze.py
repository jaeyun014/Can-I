from fastapi import APIRouter, File, Form, UploadFile

from app.models.schemas import AnalyzeResponse, TextAnalyzeRequest
from app.models.schemas import UsageLogCreate
from app.api.logs import create_log
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
) -> AnalyzeResponse:
    image_bytes = await file.read()
    ocr_result = extract_text_from_image_bytes(image_bytes)
    vision_result = await analyze_image_with_vision(image_bytes, file.content_type)
    normalized = normalize_image_input(
        vision=vision_result,
        ocr=ocr_result,
        region=region,
    )
    result = analyze_normalized(normalized)
    create_log(
        UsageLogCreate(
            itemName=result.itemName,
            detectedMaterial=result.detectedMaterial,
            region=result.region,
            overallRisk=result.overallRisk,
        )
    )
    return result
