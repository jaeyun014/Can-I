from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from app.db.database import create_feedback, list_review_queue, update_review_queue_status
from app.models.schemas import AuthUser, FeedbackCreate, FeedbackRecord, ReviewQueueItem, ReviewStatusUpdate
from app.services.auth_service import get_optional_user, get_required_user

router = APIRouter()


@router.post("/feedback", response_model=FeedbackRecord)
def submit_feedback(
    payload: FeedbackCreate,
    user: Optional[AuthUser] = Depends(get_optional_user),
) -> FeedbackRecord:
    return create_feedback(payload, user_email=user.email if user else None)


@router.get("/review-queue", response_model=list[ReviewQueueItem])
def get_review_queue(
    status: str = "pending",
    _: AuthUser = Depends(get_required_user),
) -> list[ReviewQueueItem]:
    return list_review_queue(status=status)


@router.patch("/review-queue/{review_id}", response_model=ReviewQueueItem)
def update_review_queue(
    review_id: int,
    payload: ReviewStatusUpdate,
    user: AuthUser = Depends(get_required_user),
) -> ReviewQueueItem:
    updated = update_review_queue_status(review_id, payload.status, payload.assignedTo or user.email)
    if not updated:
        raise HTTPException(status_code=404, detail="Review queue item not found.")
    return updated
