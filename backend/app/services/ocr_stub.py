from fastapi import UploadFile


async def extract_text_from_image(file: UploadFile) -> str:
    """Temporary OCR seam; replace with EasyOCR or Tesseract later."""
    await file.seek(0)
    return ""
