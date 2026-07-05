from __future__ import annotations

import re

from app.db.database import lookup_product_by_barcode


def extract_barcode_candidates(text: str) -> list[str]:
    return list(dict.fromkeys(re.findall(r"\b\d{8,14}\b", text)))


def analyze_barcode_from_text(text: str = "", explicit_barcode: str = "") -> dict[str, object]:
    """Look up barcode evidence in the internal product DB.

    Real image decoding can be added later, but this already connects OCR or
    user-provided barcode numbers to product DB evidence.
    """
    candidates = [explicit_barcode.strip()] if explicit_barcode.strip() else extract_barcode_candidates(text)
    for barcode in candidates:
        product = lookup_product_by_barcode(barcode)
        if product:
            return {
                "detected": True,
                "barcode": barcode,
                "product": product,
                "source": "internal_product_db",
                "version": "2026.07",
            }
    return {
        "detected": False,
        "barcode": candidates[0] if candidates else "",
        "product": None,
        "source": "internal_product_db",
        "version": "0.1.0",
    }


def analyze_barcode_from_image(_: bytes) -> dict[str, object]:
    """Compatibility wrapper for future image barcode decoding."""
    return analyze_barcode_from_text()
