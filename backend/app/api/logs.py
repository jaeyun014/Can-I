from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends

from app.models.schemas import AuthUser, UsageLog, UsageLogCreate
from app.services.auth_service import get_optional_user, get_required_user

router = APIRouter()
_logs: list[UsageLog] = []
_next_id = 1


@router.post("/logs", response_model=UsageLog)
def create_log(
    payload: UsageLogCreate,
    user: Optional[AuthUser] = Depends(get_optional_user),
) -> UsageLog:
    global _next_id
    log = UsageLog(
        id=_next_id,
        createdAt=datetime.now(timezone.utc),
        userEmail=user.email if user else None,
        **payload.model_dump(),
    )
    _next_id += 1
    _logs.insert(0, log)
    del _logs[200:]
    return log


@router.get("/logs", response_model=list[UsageLog])
def list_logs(user: Optional[AuthUser] = Depends(get_optional_user)) -> list[UsageLog]:
    if not user:
        return [log for log in _logs if log.userEmail is None][:20]
    return [log for log in _logs if log.userEmail == user.email][:20]


@router.delete("/logs", response_model=dict[str, int])
def delete_logs(user: AuthUser = Depends(get_required_user)) -> dict[str, int]:
    before_count = len(_logs)
    _logs[:] = [log for log in _logs if log.userEmail != user.email]
    return {"deleted": before_count - len(_logs)}
