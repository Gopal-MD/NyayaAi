"""Fixed sequential orchestrator pipeline."""
from app.orchestrator.context import PipelineContext, PipelineAbortError
from app.core.logging import get_logger

logger = get_logger(__name__)

_LIMITATION = (
    "NyayaAi provides legal information to help you understand and prepare. "
    "It is not legal advice and does not replace a qualified lawyer."
)
_ABSTENTION = (
    "I couldn't verify this information from an authoritative source. "
    "Please check the relevant government/legal source or consult a qualified lawyer."
)


async def run_pipeline(ctx: PipelineContext) -> PipelineContext:
    """Run the fixed sequential pipeline. Returns the final context."""
    try:
        # Step 1: Safety gate (always first)
        from app.safety.gate import run_safety_gate
        ctx = await run_safety_gate(ctx)
        if ctx.safety_status == "high_risk":
            ctx.final_answer = (
                "This situation may require immediate help. "
                "Please contact the resources below."
            )
            ctx.final_language = ctx.language
            raise PipelineAbortError("high_risk", ctx)

        # Step 2: Language detect + translate query to English
        from app.translation.detector import detect_language
        from app.translation.translator import translate_to_en
        ctx.detected_language = detect_language(ctx.raw_query)
        if ctx.detected_language != "en":
            ctx.query_en = await translate_to_en(ctx.raw_query, ctx.detected_language)
        else:
            ctx.query_en = ctx.raw_query

        # Step 3: Intent + domain detect
        from app.orchestrator.intent_detector import detect_intent
        ctx = await detect_intent(ctx)

        # Step 4: Fact extraction (from query context)
        # Facts are pulled from case DB; here we just note any query-level facts

        # Step 5: Missing info check
        from app.orchestrator.missing_info_checker import check_missing_info
        ctx = check_missing_info(ctx)
        if ctx.clarifying_question:
            ctx.final_answer = ctx.clarifying_question
            ctx.final_language = ctx.language
            return ctx

        # Step 6: Retrieval + rerank
        from app.rag.retriever import hybrid_search
        from app.rag.reranker import rerank
        query = ctx.query_en or ctx.raw_query
        ctx.retrieved_chunks = await hybrid_search(query, ctx.jurisdiction or "TN")
        ctx.reranked_chunks = await rerank(query, ctx.retrieved_chunks)

        # Step 7: Grounded generation (cite-or-abstain)
        from app.orchestrator.generator import generate_answer
        ctx = await generate_answer(ctx)

        # Step 8: Citation validation
        from app.rag.citation_validator import validate_all_citations
        ctx = await validate_all_citations(ctx)

        # Step 9: Action plan builder (adds to context, doesn't change answer)
        from app.orchestrator.action_plan_builder import build_action_plan_from_context
        ctx = build_action_plan_from_context(ctx)

        # Step 10: Translate output to user language
        from app.translation.translator import translate_output
        ctx = await translate_output(ctx)

    except PipelineAbortError as e:
        ctx = e.context
        ctx.final_language = ctx.final_language or ctx.language

    except Exception as exc:
        logger.error("pipeline_error", error=str(exc), user_id=ctx.user_id)
        ctx.final_answer = _ABSTENTION
        ctx.abstained = True
        ctx.final_language = ctx.language

    # Always append limitation text
    if ctx.final_answer and not ctx.final_answer.endswith(_LIMITATION):
        ctx.final_answer = ctx.final_answer + "\n\n" + _LIMITATION

    return ctx
