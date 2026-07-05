from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageStat


ROLE_LABELS = {
    "overview": "전체 사진",
    "material_label": "재질 코드 사진",
    "safety_label": "안전 표기/바코드 사진",
}


def inspect_image_quality(image_bytes: bytes) -> dict[str, object]:
    try:
        image = Image.open(BytesIO(image_bytes)).convert("L")
    except Exception:
        return {
            "blurScore": 0.0,
            "brightnessScore": 0.0,
            "objectCoverage": 0.0,
            "labelVisibility": 0.0,
            "barcodeVisibility": 0.0,
            "isAcceptable": False,
            "issues": ["image_unreadable"],
            "captureAdvice": ["사진을 다시 선택하거나 촬영해 주세요."],
        }

    width, height = image.size
    stat = ImageStat.Stat(image)
    brightness = (stat.mean[0] if stat.mean else 0.0) / 255
    contrast = (stat.stddev[0] if stat.stddev else 0.0) / 128
    pixel_count = max(1, width * height)

    issues: list[str] = []
    advice: list[str] = []
    if brightness < 0.18:
        issues.append("image_too_dark")
        advice.append("밝은 곳에서 다시 촬영해 주세요.")
    if brightness > 0.92:
        issues.append("image_too_bright")
        advice.append("빛 반사를 줄이고 다시 촬영해 주세요.")
    if contrast < 0.18:
        issues.append("image_low_contrast_or_blurry")
        advice.append("초점을 맞추고 재질 표기가 보이도록 가까이 촬영해 주세요.")
    if pixel_count < 250_000:
        issues.append("image_resolution_low")
        advice.append("물건이 화면을 더 크게 차지하도록 촬영해 주세요.")

    if not advice:
        advice.append("전체 모습, 용기 바닥, 안전 표기나 바코드를 함께 촬영하면 더 정확합니다.")

    return {
        "blurScore": round(max(0.0, min(1.0, contrast)), 3),
        "brightnessScore": round(brightness, 3),
        "objectCoverage": 0.5,
        "labelVisibility": 0.0,
        "barcodeVisibility": 0.0,
        "isAcceptable": not issues,
        "issues": issues,
        "captureAdvice": advice,
    }


def inspect_multiple_images(images: list[tuple[str, bytes]]) -> dict[str, object]:
    checks = [
        {"role": role, "label": ROLE_LABELS.get(role, role), **inspect_image_quality(image_bytes)}
        for role, image_bytes in images
    ]
    issues: list[str] = []
    advice: list[str] = []
    for check in checks:
        issues.extend(str(issue) for issue in check.get("issues", []))
        advice.extend(str(item) for item in check.get("captureAdvice", []))

    roles = {role for role, _ in images}
    if "overview" not in roles:
        issues.append("overview_image_missing")
        advice.append("물건 전체가 보이는 사진을 추가해 주세요.")
    if "material_label" not in roles:
        issues.append("material_label_image_missing")
        advice.append("용기 바닥의 재질 코드가 보이도록 가까이 촬영해 주세요.")
    if "safety_label" not in roles:
        issues.append("safety_label_or_barcode_image_missing")
        advice.append("전자레인지/냉동 가능 표시나 바코드가 보이는 사진을 추가해 주세요.")

    return {
        "isAcceptable": all(bool(check.get("isAcceptable")) for check in checks) and "overview" in roles,
        "issues": list(dict.fromkeys(issues)),
        "captureAdvice": list(dict.fromkeys(advice)),
        "images": checks,
        "recommendedShots": [
            "물건 전체 사진",
            "바닥 또는 뒷면의 재질 코드 확대 사진",
            "안전 표기 또는 바코드 사진",
        ],
    }
