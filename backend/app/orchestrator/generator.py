"""Grounded generation with cite-or-abstain logic."""
from pydantic import BaseModel
from app.orchestrator.context import PipelineContext, CitationAttempt, EvidenceItem
from app.core.groq_client import groq_json
from app.core.logging import get_logger

logger = get_logger(__name__)

_ABSTENTION = (
    "I couldn't verify this information from an authoritative source. "
    "Please check the relevant government/legal source or consult a qualified lawyer."
)


class CitationOut(BaseModel):
    chunk_id: str = ""
    quoted_text: str = ""
    claim: str = ""
    track: str = "unverified"
    page_ref: str | None = None
    clause_ref: str | None = None


class GenerationResult(BaseModel):
    answer: str = ""
    abstain: bool = False
    citations: list[CitationOut] = []


async def generate_answer(ctx: PipelineContext) -> PipelineContext:
    query = ctx.query_en or ctx.raw_query

    # Build document context
    doc_context = ""
    if ctx.document_text and ctx.mode == "document_qa":
        doc_context = f"\nDOCUMENT TEXT:\n{ctx.document_text[:6000]}\n"

    # Build retrieval context
    retrieval_context = ""
    for i, chunk in enumerate(ctx.reranked_chunks[:5]):
        meta = chunk.metadata
        retrieval_context += (
            f"\n[SOURCE {i+1}] ID={chunk.chunk_id}\n"
            f"{chunk.section_title} ({meta.get('source','')}, {meta.get('jurisdiction','')})\n"
            f"{chunk.content[:800]}\n"
        )

    if not doc_context and not retrieval_context:
        ctx.final_answer = _ABSTENTION
        ctx.abstained = True
        return ctx

    prompt = f"""You are NyayaAi, a legal information assistant for India.
You ONLY use the context provided below. Do NOT use your training knowledge for legal facts.
{doc_context}
{retrieval_context}

USER QUESTION: {query}

Respond in JSON:
{{
  "answer": "<answer using ONLY the above context, empty string if abstaining>",
  "abstain": <true|false>,
  "citations": [
    {{
      "chunk_id": "<SOURCE ID from above>",
      "quoted_text": "<verbatim quote from context>",
      "claim": "<which sentence in your answer this supports>",
      "track": "user_document|official_source|unverified",
      "page_ref": "<page number if from document>",
      "clause_ref": "<clause name if applicable>"
    }}
  ]
}}

Rules:
- If you cannot answer from the provided context, set abstain=true and answer=""
- Never invent section numbers, deposit limits, or deadlines
- Never use "illegal" or "void" without a retrieved source supporting it
- For flagged clauses use: "may be unusual or one-sided; consider asking a lawyer"
"""

    for attempt in range(2):
        try:
            result = await groq_json(prompt, GenerationResult, model="reasoning")
            ctx.generation_attempts = attempt + 1

            if result.abstain or not result.answer:
                ctx.final_answer = _ABSTENTION
                ctx.abstained = True
                ctx.citations = []
                return ctx

            ctx.raw_answer = result.answer
            ctx.citations = [
                CitationAttempt(
                    chunk_id=c.chunk_id,
                    quoted_text=c.quoted_text,
                    claim=c.claim,
                    track=c.track if c.track in ("user_document", "official_source", "unverified") else "unverified",
                    page_ref=c.page_ref,
                    clause_ref=c.clause_ref,
                )
                for c in result.citations
            ]
            return ctx

        except Exception as exc:
            logger.warning("generation_attempt_failed", attempt=attempt, error=str(exc))
            if attempt == 1:
                ctx.final_answer = _ABSTENTION
                ctx.abstained = True

    return ctx
