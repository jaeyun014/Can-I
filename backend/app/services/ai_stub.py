from fastapi import UploadFile

from app.services.ocr_stub import extract_text_from_image


async def detect_item_from_image(file: UploadFile) -> dict[str, str]:
    """Return deterministic image detection data until Vision AI is connected."""
    ocr_text = await extract_text_from_image(file)
    return {
        "itemName": "플라스틱 배달 용기",
        "detectedMaterial": "pp",
        "ocrText": ocr_text or "PP",
    }
