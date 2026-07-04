from fastapi import APIRouter, File, Form, UploadFile

from app.models.schemas import AnalyzeResponse, TextAnalyzeRequest
from app.services.ai_stub import detect_item_from_image
from app.services.rule_engine import analyze_item

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_text(payload: TextAnalyzeRequest) -> AnalyzeResponse:
    return analyze_item(item_name=payload.query, region=payload.region)


@router.post("/analyze/image", response_model=AnalyzeResponse)
async def analyze_image(
    file: UploadFile = File(...),
    region: str = Form(default="서울"),
) -> AnalyzeResponse:
    detected = await detect_item_from_image(file)
    return analyze_item(
        item_name=detected["itemName"],
        detected_material=detected["detectedMaterial"],
        ocr_text=detected["ocrText"],
        region=region,
    )
