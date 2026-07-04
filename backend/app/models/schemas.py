from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

RiskStatus = Literal["SAFE", "WARNING", "DANGER"]


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


class AnalyzeResponse(BaseModel):
    itemName: str
    detectedMaterial: str
    objectType: str = ""
    ocrText: str = ""
    region: str
    confidence: float = 0.0
    evidence: Evidence = Field(default_factory=Evidence)
    overallRisk: RiskStatus
    decisions: dict[str, Decision]
    disposal: Disposal


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
    confidence: float = 0.0
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


class GoogleLoginRequest(BaseModel):
    credential: str


class AuthUser(BaseModel):
    email: str
    name: str = ""
    picture: str = ""


class AuthSession(BaseModel):
    token: str
    user: AuthUser
