"""Check for missing required information and generate clarifying questions."""
from app.orchestrator.context import PipelineContext


_JURISDICTION_REQUIRED_INTENTS = {
    "clause_question", "deadline_question", "rights_question", "procedure_question"
}


def check_missing_info(ctx: PipelineContext) -> PipelineContext:
    """Set clarifying_question if required facts are missing."""
    # Jurisdiction needed for jurisdiction-specific questions
    if (
        ctx.intent in _JURISDICTION_REQUIRED_INTENTS
        and not ctx.jurisdiction
        and ctx.mode != "document_qa"
    ):
        ctx.clarifying_question = (
            "To give you accurate information, could you tell me which state "
            "the property is located in? (e.g. Tamil Nadu, Maharashtra, Delhi)"
        )
        ctx.missing_required_facts.append("jurisdiction_state")

    return ctx
