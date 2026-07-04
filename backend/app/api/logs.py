from datetime import datetime, timezone

from fastapi import APIRouter

from app.models.schemas import UsageLog, UsageLogCreate

router = APIRouter()
_logs: list[UsageLog] = []
_next_id = 1


@router.post("/logs", response_model=UsageLog)
def create_log(payload: UsageLogCreate) -> UsageLog:
    global _next_id
    log = UsageLog(
        id=_next_id,
        createdAt=datetime.now(timezone.utc),
        **payload.model_dump(),
    )
    _next_id += 1
    _logs.insert(0, log)
    del _logs[20:]
    return log


@router.get("/logs", response_model=list[UsageLog])
def list_logs() -> list[UsageLog]:
    return _logs[:20]
