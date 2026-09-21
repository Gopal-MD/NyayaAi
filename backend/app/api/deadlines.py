"""Deadlines router: GET /deadlines"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.auth import CurrentUser
from app.core.db import get_db
from app.models.db import User, UserCase, Deadline
from app.models.schemas import DeadlineListResponse, DeadlineItem

router = APIRouter()


@router.get("", response_model=DeadlineListResponse)
async def list_deadlines(
    case_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(User.firebase_uid == current_user["user_id"])
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    result = await db.execute(
        select(UserCase).where(UserCase.id == case_id, UserCase.user_id == user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Case not found.")

    result = await db.execute(
        select(Deadline)
        .where(Deadline.case_id == case_id)
        .order_by(Deadline.due_date.asc())
    )
    deadlines = result.scalars().all()

    return DeadlineListResponse(
        deadlines=[
            DeadlineItem(
                label=d.label,
                due_date=str(d.due_date) if d.due_date else None,
                source_type=d.source_type or "document",
                source_ref=d.source_ref or "",
            )
            for d in deadlines
        ]
    )
