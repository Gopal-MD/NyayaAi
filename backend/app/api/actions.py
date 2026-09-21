"""Action plan router: POST /action-plan"""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.auth import CurrentUser
from app.core.db import get_db
from app.models.db import User, UserCase, DocumentAnalysis, UploadedDocument
from app.models.schemas import ActionPlanRequest, ActionPlanResponse, ActionPlanSections

router = APIRouter()

_LIMITATION = (
    "NyayaAi provides legal information to help you understand and prepare. "
    "It is not legal advice and does not replace a qualified lawyer."
)


@router.post("", response_model=ActionPlanResponse)
async def create_action_plan(
    body: ActionPlanRequest,
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
        select(UserCase).where(UserCase.id == body.case_id, UserCase.user_id == user.id)
    )
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")

    # Get latest analysis for the case
    analysis = None
    if body.analysis_id:
        result = await db.execute(
            select(DocumentAnalysis)
            .join(UploadedDocument, DocumentAnalysis.document_id == UploadedDocument.id)
            .where(DocumentAnalysis.id == body.analysis_id, UploadedDocument.case_id == body.case_id)
        )
        analysis = result.scalar_one_or_none()

    # Build action plan from analysis data
    facts = analysis.structured_facts if analysis else {}
    deadlines = analysis.deadlines if analysis else []
    clauses = analysis.clause_analysis if analysis else []
    questions = analysis.lawyer_questions if analysis else []

    from app.orchestrator.action_plan_builder import build_action_plan
    plan_sections = build_action_plan(facts or {}, deadlines or [], clauses or [], questions or [], case)

    return ActionPlanResponse(
        plan_id=str(uuid.uuid4()),
        sections=plan_sections,
    )
