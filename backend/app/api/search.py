"""Search router: GET /sources, POST /legal-search"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.auth import CurrentUser
from app.core.db import get_db
from app.models.db import Source
from app.models.schemas import LegalSearchRequest, LegalSearchResponse
from app.orchestrator.pipeline import run_pipeline
from app.orchestrator.context import PipelineContext

router = APIRouter()


@router.get("/sources")
async def list_sources(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Source).where(Source.status == "active")
    )
    sources = result.scalars().all()
    return {
        "sources": [
            {
                "id": s.source_key,
                "title": s.title,
                "authority": s.authority,
                "jurisdiction": s.jurisdiction,
                "domain": s.domain,
                "url": s.url,
                "status": s.status,
                "effective_date": s.effective_date,
                "last_verified": s.last_verified,
            }
            for s in sources
        ]
    }


@router.post("/legal-search", response_model=LegalSearchResponse)
async def legal_search(
    body: LegalSearchRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    ctx = PipelineContext(
        user_id=current_user["user_id"],
        case_id="search",
        raw_query=body.query,
        language=body.language,
        mode="legal_search",
        jurisdiction=body.jurisdiction,
    )
    ctx = await run_pipeline(ctx)

    return LegalSearchResponse(
        answer=ctx.final_answer or "",
        citations=[e.model_dump() for e in (ctx.evidence or [])],
        abstained=ctx.abstained,
    )
