from __future__ import annotations


def classify_material_candidates(_: bytes) -> dict[str, object]:
    """Optional custom image classifier interface.

    This model never makes final safety decisions. Predictions are evidence
    candidates only and are intentionally empty until a trained model is wired.
    """
    return {
        "modelName": "material_classifier_stub",
        "modelVersion": "0.1.0",
        "predictions": [],
    }
