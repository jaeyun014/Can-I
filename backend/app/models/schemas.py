from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

RiskStatus = Literal["SAFE", "WARNING", "DANGER"]
ConfidenceLevel = Literal["LOW", "MEDIUM", "HIGH"]


class TextAnalyzeRequest(BaseModel):
    query: str = Field(..., min_length=1, examples=["알루미늄 포일"])
    region: str = Field(default="서울", examples=["서울"])


class Decision(BaseModel):
    status: RiskStatus
    label: str
    allowed: bool
    reason: str
    why: str
    alternative: str


class Disposal(BaseModel):
    category: str
    regionRule: str
    instruction: str


class Evidence(BaseModel):
    vision: str = ""
    ocr: str = ""
    rule: str = ""


class ConfidenceFactor(BaseModel):
    label: str
    score: int
    reason: str


class ConfidenceReport(BaseModel):
    score: int = 0
    level: ConfidenceLevel = "LOW"
    summary: str = "신뢰도를 계산할 근거가 충분하지 않습니다."
    factors: list[ConfidenceFactor] = Field(default_factory=list)
    penalties: list[ConfidenceFactor] = Field(default_factory=list)
    calculation: str = "0 = 0"
    lowConfidenceReasons: list[str] = Field(default_factory=list)
    priority: list[str] = Field(
        default_factory=lambda: [
            "사용자 입력",
            "OCR 안전 표기",
            "OCR 재질 표기",
            "바코드 제품 DB",
            "GPT Vision",
            "unknown fallback",
        ]
    )
    conflictDetected: bool = False


class AnalyzeResponse(BaseModel):
    logId: Optional[int] = None
    itemName: str
    detectedMaterial: str
    objectType: str = ""
    ocrText: str = ""
    region: str
    confidence: ConfidenceReport = Field(default_factory=ConfidenceReport)
    evidence: Evidence = Field(default_factory=Evidence)
    overallRisk: RiskStatus
    decisions: dict[str, Decision]
    disposal: Disposal
    imageQuality: dict[str, Any] = Field(default_factory=dict)
    detectedObjects: list[dict[str, Any]] = Field(default_factory=list)
    normalized: dict[str, Any] = Field(default_factory=dict)
    additionalCaptureRequest: dict[str, Any] = Field(default_factory=dict)
    versions: dict[str, str] = Field(default_factory=dict)


class VisionResult(BaseModel):
    itemName: str = "알 수 없는 물건"
    detectedMaterial: str = "unknown"
    visibleLabels: list[str] = Field(default_factory=list)
    objectType: str = "unknown"
    confidence: float = 0.0
    notes: str = "AI 분석이 비활성화되어 규칙 기반으로 분석했습니다."


class OCRResult(BaseModel):
    rawText: str = ""
    detectedSymbols: list[str] = Field(default_factory=list)
    materialHints: list[str] = Field(default_factory=list)
    safetyHints: list[str] = Field(default_factory=list)


class NormalizedInput(BaseModel):
    itemName: str
    material: str = "unknown"
    objectType: str = "unknown"
    region: str
    ocrText: str = ""
    safetyHints: list[str] = Field(default_factory=list)
    userQuery: str = ""
    visionItemName: str = ""
    visionMaterial: str = "unknown"
    visionConfidence: float = 0.0
    ocrMaterialHints: list[str] = Field(default_factory=list)
    barcodeProductName: str = ""
    barcodeMaterial: str = ""
    evidence: Evidence = Field(default_factory=Evidence)


class UsageLogCreate(BaseModel):
    itemName: str
    detectedMaterial: str
    region: str
    overallRisk: RiskStatus


class UsageLog(UsageLogCreate):
    id: int
    createdAt: datetime
    userEmail: Optional[str] = None


class FeedbackCreate(BaseModel):
    logId: Optional[int] = None
    feedbackType: str
    originalPrediction: dict[str, Any] = Field(default_factory=dict)
    userCorrection: dict[str, Any] = Field(default_factory=dict)
    comment: str = ""


class FeedbackRecord(FeedbackCreate):
    id: int
    userEmail: Optional[str] = None
    reviewStatus: str = "pending"
    createdAt: datetime
    updatedAt: datetime


class ReviewQueueItem(BaseModel):
    id: int
    usageLogId: int
    reviewScore: float
    reasons: list[str] = Field(default_factory=list)
    status: str
    assignedTo: Optional[str] = None
    itemName: str = ""
    detectedMaterial: str = ""
    overallRisk: str = ""
    createdAt: datetime
    updatedAt: datetime


class ReviewStatusUpdate(BaseModel):
    status: str
    assignedTo: Optional[str] = None


class GoogleLoginRequest(BaseModel):
    credential: str


class AuthUser(BaseModel):
    email: str
    name: str = ""
    picture: str = ""


class AuthSession(BaseModel):
    token: str
    user: AuthUser
