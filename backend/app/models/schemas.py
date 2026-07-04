from datetime import datetime
from typing import Literal

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


class AnalyzeResponse(BaseModel):
    itemName: str
    detectedMaterial: str
    ocrText: str = ""
    region: str
    overallRisk: RiskStatus
    decisions: dict[str, Decision]
    disposal: Disposal


class UsageLogCreate(BaseModel):
    itemName: str
    detectedMaterial: str
    region: str
    overallRisk: RiskStatus


class UsageLog(UsageLogCreate):
    id: int
    createdAt: datetime
