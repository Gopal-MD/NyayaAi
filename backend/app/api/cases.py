"""Cases router: CRUD for user cases."""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.core.auth import CurrentUser
from app.core.db import get_db
from app.core.config import settings
from app.models.db import User, UserCase, AuditLog
from app.models.schemas import CaseCreateRequest, CaseResponse, CaseListResponse
import hashlib

router = APIRouter()


async def _get_user_db(current_user: CurrentUser, db: AsyncSession) -> User:
    result = await db.execute(
        select(User).where(User.firebase_uid == current_user["user_id"])
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found. Call /auth/verify first.")
    return user


@router.post("", response_model=CaseResponse, status_code=201)
async def create_case(
    body: CaseCreateRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user_db(current_user, db)
    auto_delete = datetime.utcnow() + timedelta(days=user.auto_delete_days)
    case = UserCase(
        user_id=user.id,
        title=body.title,
        domain=body.domain,
        auto_delete_at=auto_delete,
    )
    db.add(case)
    await db.commit()
    await db.refresh(case)
    return _case_to_response(case)


@router.get("", response_model=CaseListResponse)
async def list_cases(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user_db(current_user, db)
    result = await db.execute(
        select(UserCase).where(UserCase.user_id == user.id).order_by(UserCase.updated_at.desc())
    )
    cases = result.scalars().all()
    return CaseListResponse(cases=[_case_to_response(c) for c in cases], total=len(cases))


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user_db(current_user, db)
    case = await _require_case(case_id, user.id, db)
    return _case_to_response(case)


@router.delete("/{case_id}", status_code=204)
async def delete_case(
    case_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user_db(current_user, db)
    await _require_case(case_id, user.id, db)
    await db.execute(delete(UserCase).where(UserCase.id == case_id))
    db.add(AuditLog(
        user_id=user.id,
        user_id_hash=hashlib.sha256(user.firebase_uid.encode()).hexdigest(),
        event_type="case_deleted",
        outcome="success",
    ))
    await db.commit()


async def _require_case(case_id: str, user_id: str, db: AsyncSession) -> UserCase:
    result = await db.execute(
        select(UserCase).where(UserCase.id == case_id, UserCase.user_id == user_id)
    )
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


def _case_to_response(case: UserCase) -> CaseResponse:
    return CaseResponse(
        case_id=case.id,
        title=case.title,
        domain=case.domain,
        jurisdiction_state=case.jurisdiction_state,
        status=case.status,
        created_at=case.created_at,
        updated_at=case.updated_at,
    )
