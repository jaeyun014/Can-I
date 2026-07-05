from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends

from app.models.schemas import AuthUser, UsageLog, UsageLogCreate
from app.db.database import create_usage_log, delete_usage_logs, list_usage_logs
from app.services.auth_service import get_optional_user, get_required_user

router = APIRouter()


@router.post("/logs", response_model=UsageLog)
def create_log(
    payload: UsageLogCreate,
    user: Optional[AuthUser] = Depends(get_optional_user),
) -> UsageLog:
    return create_usage_log(payload, user_email=user.email if user else None, input_type="manual")


@router.get("/logs", response_model=list[UsageLog])
def list_logs(user: Optional[AuthUser] = Depends(get_optional_user)) -> list[UsageLog]:
    return list_usage_logs(user_email=user.email if user else None)


@router.delete("/logs", response_model=dict[str, int])
def delete_logs(user: AuthUser = Depends(get_required_user)) -> dict[str, int]:
    return {"deleted": delete_usage_logs(user.email)}
