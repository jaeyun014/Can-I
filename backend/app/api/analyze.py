from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.models.schemas import AnalyzeResponse, AuthUser, TextAnalyzeRequest, UsageLogCreate
from app.db.database import create_usage_log
from app.services.auth_service import get_optional_user
from app.services.barcode_service import analyze_barcode_from_text
from app.services.conflict_detector import detect_conflicts
from app.services.evidence_fusion_service import EvidenceRecord, fuse_evidence
from app.services.image_quality_service import inspect_multiple_images
from app.services.input_normalizer import normalize_image_input
from app.services.material_classifier_service import classify_material_candidates
from app.services.ocr_service import extract_text_from_image_bytes
from app.services.rule_engine import analyze_item, analyze_normalized
from app.services.vision_service import analyze_image_with_vision

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_text(payload: TextAnalyzeRequest) -> AnalyzeResponse:
    result = analyze_item(item_name=payload.query, region=payload.region)
    result.versions = _versions()
    return result


@router.post("/analyze/image", response_model=AnalyzeResponse)
async def analyze_image(
    file: Optional[UploadFile] = File(default=None),
    files: Optional[list[UploadFile]] = File(default=None),
    region: str = Form(default="서울"),
    itemName: str = Form(default=""),
    barcode: str = Form(default=""),
    user: Optional[AuthUser] = Depends(get_optional_user),
) -> AnalyzeResponse:
    upload_files = files or ([file] if file else [])
    image_payloads: list[tuple[str, bytes, str | None]] = []
    for index, upload in enumerate(upload_files):
        role = _image_role(index)
        image_payloads.append((role, await upload.read(), upload.content_type))

    if not image_payloads:
        raise HTTPException(status_code=400, detail="At least one image file is required.")

    _, primary_bytes, primary_content_type = image_payloads[0]
    image_quality = inspect_multiple_images([(role, image_bytes) for role, image_bytes, _ in image_payloads])
    classifier_result = classify_material_candidates(primary_bytes)
    ocr_results = [extract_text_from_image_bytes(image_bytes) for _, image_bytes, _ in image_payloads]
    ocr_result = _merge_ocr_results(ocr_results)
    barcode_result = analyze_barcode_from_text(ocr_result.rawText, barcode)
    vision_result = await analyze_image_with_vision(primary_bytes, primary_content_type)
    normalized = normalize_image_input(
        vision=vision_result,
        ocr=ocr_result,
        region=region,
        user_query=itemName,
    )
    evidence_records = _build_evidence_records(itemName, ocr_result, vision_result, barcode_result, classifier_result)
    material_fusion = fuse_evidence("material", evidence_records)
    object_fusion = fuse_evidence("objectName", evidence_records)
    conflicts = detect_conflicts(evidence_records)
    product = barcode_result.get("product")
    if isinstance(product, dict):
        normalized.barcodeProductName = str(product.get("productName", ""))
        materials = product.get("materials", {})
        if isinstance(materials, dict):
            normalized.barcodeMaterial = str(materials.get("body", ""))
    if material_fusion.selectedValue != "unknown":
        normalized.material = material_fusion.selectedValue
    if object_fusion.selectedValue != "unknown" and not itemName.strip():
        normalized.itemName = object_fusion.selectedValue
    result = analyze_normalized(normalized)
    result.imageQuality = image_quality
    result.detectedObjects = _detected_objects(result, vision_result, classifier_result)
    result.normalized = {
        "objectName": result.itemName,
        "objectType": result.objectType,
        "material": result.detectedMaterial,
        "bodyMaterial": result.detectedMaterial if result.objectType else "",
        "lidMaterial": "unknown",
        "containsFood": result.detectedMaterial == "food" or "food" in result.objectType,
        "containsMetal": result.detectedMaterial in {"aluminum", "metal", "lithium_battery"},
        "imageCount": len(image_payloads),
        "barcode": barcode_result.get("barcode", ""),
        "materialCandidates": material_fusion.candidates,
        "objectNameCandidates": object_fusion.candidates,
        "conflicts": [conflict.__dict__ for conflict in conflicts],
    }
    result.additionalCaptureRequest = {
        "required": not bool(image_quality.get("isAcceptable", True)) or result.confidence.score < 65,
        "instructions": image_quality.get("captureAdvice", []),
        "recommendedShots": image_quality.get("recommendedShots", []),
    }
    result.versions = _versions(
        barcode_version=str(barcode_result.get("version", "0.1.0")),
        classifier_version=str(classifier_result.get("modelVersion", "0.1.0")),
    )
    create_usage_log(
        UsageLogCreate(
            itemName=result.itemName,
            detectedMaterial=result.detectedMaterial,
            region=result.region,
            overallRisk=result.overallRisk,
        ),
        user_email=user.email if user else None,
        input_type="image",
        input_text=itemName,
        result=result,
        normalized={**normalized.model_dump(), "imageQuality": image_quality, "detectedObjects": result.detectedObjects, "barcode": barcode_result},
        evidence_records=evidence_records,
        conflicts=conflicts,
    )
    return result


def _versions(barcode_version: str = "0.1.0", classifier_version: str = "0.1.0") -> dict[str, str]:
    return {
        "ocr": "tesseract",
        "ocrPreprocessor": "0.1.0",
        "visionModel": "configured-model",
        "visionPrompt": "4.0.0",
        "materialClassifier": classifier_version,
        "barcodeDatabase": barcode_version,
        "normalizer": "2.0.0",
        "evidenceFusion": "1.0.0",
        "conflictDetector": "1.0.0",
        "ruleEngine": "1.5.0",
        "confidenceService": "2.0.0",
    }


def _image_role(index: int) -> str:
    return ["overview", "material_label", "safety_label"][index] if index < 3 else f"extra_{index + 1}"


def _merge_ocr_results(results):
    if not results:
        return extract_text_from_image_bytes(b"")
    first = results[0]
    first.rawText = "\n".join(result.rawText for result in results if result.rawText)
    first.detectedSymbols = list(dict.fromkeys(symbol for result in results for symbol in result.detectedSymbols))
    first.materialHints = list(dict.fromkeys(hint for result in results for hint in result.materialHints))
    first.safetyHints = list(dict.fromkeys(hint for result in results for hint in result.safetyHints))
    return first


def _build_evidence_records(item_name, ocr_result, vision_result, barcode_result, classifier_result) -> list[EvidenceRecord]:
    records: list[EvidenceRecord] = []
    if item_name.strip():
        records.append(
            EvidenceRecord(
                field="objectName",
                value=item_name.strip(),
                source="user_object_name",
                rawConfidence=0.9,
                evidenceText=f"사용자가 '{item_name.strip()}' 물건명을 입력했습니다.",
            )
        )
    for material in ocr_result.materialHints:
        records.append(
            EvidenceRecord(
                field="material",
                value=material,
                source="ocr_material_code",
                rawConfidence=0.94,
                evidenceText=f"OCR에서 {material} 재질 코드를 감지했습니다.",
            )
        )
    for safety_hint in ocr_result.safetyHints:
        records.append(
            EvidenceRecord(
                field="safetyLabel",
                value=safety_hint,
                source="ocr_safety_label",
                rawConfidence=0.92,
                evidenceText=f"OCR에서 {safety_hint} 안전 표기를 감지했습니다.",
            )
        )
    if vision_result.itemName != "알 수 없는 물건":
        records.append(
            EvidenceRecord(
                field="objectName",
                value=vision_result.itemName,
                source="gpt_vision",
                rawConfidence=vision_result.confidence or 0.5,
                evidenceText="GPT Vision이 물체명을 추정했습니다.",
            )
        )
    if vision_result.detectedMaterial != "unknown":
        records.append(
            EvidenceRecord(
                field="material",
                value=vision_result.detectedMaterial,
                source="gpt_vision",
                rawConfidence=vision_result.confidence or 0.5,
                evidenceText="GPT Vision이 재질을 추정했습니다.",
            )
        )
    product = barcode_result.get("product")
    if isinstance(product, dict):
        records.append(
            EvidenceRecord(
                field="objectName",
                value=str(product.get("productName", "")),
                source="barcode_verified_product_db" if product.get("verified") else "manufacturer_product_data",
                rawConfidence=float(product.get("dataConfidence", 0.7)),
                verified=bool(product.get("verified")),
                evidenceText="바코드 제품 DB에서 제품명을 확인했습니다.",
                metadata={"barcode": barcode_result.get("barcode", "")},
            )
        )
        materials = product.get("materials", {})
        if isinstance(materials, dict) and materials.get("body"):
            records.append(
                EvidenceRecord(
                    field="material",
                    value=str(materials["body"]),
                    source="barcode_verified_product_db" if product.get("verified") else "manufacturer_product_data",
                    rawConfidence=float(product.get("dataConfidence", 0.7)),
                    verified=bool(product.get("verified")),
                    evidenceText="바코드 제품 DB에서 본체 재질을 확인했습니다.",
                    metadata={"barcode": barcode_result.get("barcode", ""), "part": "body"},
                )
            )
    predictions = classifier_result.get("predictions", [])
    if isinstance(predictions, list):
        for prediction in predictions[:2]:
            if isinstance(prediction, dict) and prediction.get("label"):
                records.append(
                    EvidenceRecord(
                        field="material",
                        value=str(prediction["label"]),
                        source="custom_classifier",
                        rawConfidence=float(prediction.get("probability", 0.0)),
                        evidenceText="전용 이미지 분류 모델 후보입니다.",
                    )
                )
    return records


def _detected_objects(result: AnalyzeResponse, vision_result, classifier_result: dict[str, object]) -> list[dict[str, object]]:
    objects = [
        {
            "id": "body",
            "name": result.itemName,
            "objectType": result.objectType or vision_result.objectType,
            "material": result.detectedMaterial,
            "confidence": result.confidence.score / 100,
        }
    ]
    if result.objectType in {"food_container", "container"} or "container" in result.objectType:
        objects.append(
            {
                "id": "lid",
                "name": "뚜껑",
                "objectType": "container_lid",
                "material": "unknown",
                "confidence": 0.0,
            }
        )
    predictions = classifier_result.get("predictions", [])
    if predictions:
        objects[0]["classifierPredictions"] = predictions
    return objects
