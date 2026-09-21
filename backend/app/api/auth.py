"""Auth router: POST /auth/verify"""
import hashlib
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.auth import get_current_user, CurrentUser
from app.core.db import get_db
from app.models.db import User, AuditLog
from app.models.schemas import TokenVerifyRequest, UserResponse

router = APIRouter()


@router.post("/verify", response_model=UserResponse)
async def verify_token(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Verify Firebase token and upsert user record."""
    uid = current_user["user_id"]

    result = await db.execute(select(User).where(User.firebase_uid == uid))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            firebase_uid=uid,
            email=current_user.get("email", ""),
            display_name=current_user.get("display_name", ""),
        )
        db.add(user)
        # Audit log
        db.add(AuditLog(
            user_id=None,
            user_id_hash=hashlib.sha256(uid.encode()).hexdigest(),
            event_type="user_created",
            outcome="success",
        ))
        await db.commit()
        await db.refresh(user)

    return UserResponse(
        user_id=user.id,
        email=user.email or "",
        display_name=user.display_name or "",
        preferred_language=user.preferred_language,
        is_anonymous=current_user.get("is_anonymous", False),
        auto_delete_days=user.auto_delete_days,
    )
