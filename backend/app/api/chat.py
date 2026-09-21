"""Chat router: POST /chat"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.auth import CurrentUser
from app.core.db import get_db
from app.core.security import limiter
from app.core.config import settings
from app.models.db import User, UserCase, Conversation, Message, UploadedDocument
from app.models.schemas import ChatRequest, ChatResponse
from app.orchestrator.pipeline import run_pipeline
from app.orchestrator.context import PipelineContext

router = APIRouter()


@router.post("", response_model=ChatResponse)
@limiter.limit(settings.RATE_LIMIT_CHAT)
async def chat(
    request,
    body: ChatRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(User.firebase_uid == current_user["user_id"])
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found. Call /auth/verify first.")

    # Verify case ownership
    result = await db.execute(
        select(UserCase).where(UserCase.id == body.case_id, UserCase.user_id == user.id)
    )
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")

    # Get or create conversation
    result = await db.execute(
        select(Conversation)
        .where(Conversation.case_id == body.case_id)
        .order_by(Conversation.created_at.desc())
        .limit(1)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        conv = Conversation(case_id=body.case_id, mode=body.mode)
        db.add(conv)
        await db.flush()

    # Fetch document text if in document_qa mode
    document_text: str | None = None
    if body.mode == "document_qa" and body.document_id:
        result = await db.execute(
            select(UploadedDocument)
            .where(UploadedDocument.id == body.document_id)
        )
        doc = result.scalar_one_or_none()
        if doc:
            document_text = doc.masked_text

    # Save user message
    user_msg = Message(
        conversation_id=conv.id,
        role="user",
        content=body.message,
        language=body.language,
    )
    db.add(user_msg)
    await db.flush()

    # Run pipeline
    ctx = PipelineContext(
        user_id=user.id,
        case_id=body.case_id,
        raw_query=body.message,
        language=body.language,
        mode=body.mode,
        jurisdiction=case.jurisdiction_state,
        document_text=document_text,
    )
    ctx = await run_pipeline(ctx)

    # Save assistant message
    assistant_msg = Message(
        conversation_id=conv.id,
        role="assistant",
        content=ctx.final_answer or "",
        language=ctx.final_language or body.language,
        citations=[e.model_dump() for e in (ctx.evidence or [])],
        safety_status=ctx.safety_status,
    )
    db.add(assistant_msg)
    await db.commit()
    await db.refresh(assistant_msg)

    return ChatResponse(
        message_id=assistant_msg.id,
        answer=ctx.final_answer or "",
        language=ctx.final_language or body.language,
        evidence=ctx.evidence or [],
        citations_validated=ctx.citations_validated,
        safety_status=ctx.safety_status,
        emergency_resources=[e.model_dump() for e in ctx.emergency_resources],
        machine_translated=ctx.machine_translated,
        english_original=ctx.english_original,
        clarifying_question=ctx.clarifying_question,
        abstained=ctx.abstained,
    )
