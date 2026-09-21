"""Intent and domain detection step."""
from app.orchestrator.context import PipelineContext
from app.core.groq_client import groq_json
from app.core.logging import get_logger
from pydantic import BaseModel

logger = get_logger(__name__)


class IntentResult(BaseModel):
    intent: str = "general_question"
    domain: str = "tenancy"
    jurisdiction_state: str | None = None


async def detect_intent(ctx: PipelineContext) -> PipelineContext:
    query = ctx.query_en or ctx.raw_query

    # If jurisdiction already known, skip extraction
    if ctx.jurisdiction:
        ctx.intent = "general_question"
        ctx.domain = "tenancy"
        return ctx

    prompt = f"""Analyse the following legal query and return JSON.

Query: {query}

Return JSON:
{{
  "intent": "clause_question|deadline_question|rights_question|procedure_question|general_question",
  "domain": "tenancy|employment|consumer|other",
  "jurisdiction_state": "<2-letter Indian state code e.g. TN, MH, DL, or null if unknown>"
}}"""

    try:
        result = await groq_json(prompt, IntentResult, model="classify")
        ctx.intent = result.intent
        ctx.domain = result.domain
        if result.jurisdiction_state and not ctx.jurisdiction:
            ctx.jurisdiction = result.jurisdiction_state
    except Exception as exc:
        logger.warning("intent_detection_failed", error=str(exc))
        ctx.intent = "general_question"
        ctx.domain = "tenancy"

    return ctx
