"""Feedback router: POST /feedback"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.auth import CurrentUser
from app.core.db import get_db
from app.models.db import User, Feedback
from app.models.schemas import FeedbackRequest, FeedbackResponse

router = APIRouter()


@router.post("", response_model=FeedbackResponse, status_code=201)
async def submit_feedback(
    body: FeedbackRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(User.firebase_uid == current_user["user_id"])
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    fb = Feedback(
        message_id=body.message_id,
        user_id=user.id,
        rating=body.rating,
        comment=body.comment,
    )
    db.add(fb)
    await db.commit()
    await db.refresh(fb)
    return FeedbackResponse(feedback_id=fb.id)
