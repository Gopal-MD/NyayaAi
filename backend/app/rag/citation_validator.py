"""Pure validation for citations against retrieved source chunks."""
from app.orchestrator.context import CitationAttempt, RetrievedChunk


def validate_citation(citation: CitationAttempt, retrieved_chunks: list[RetrievedChunk]) -> bool:
    if not citation.chunk_id or not citation.quoted_text or not citation.quoted_text.strip():
        return False
    matching = next((chunk for chunk in retrieved_chunks if chunk.chunk_id == citation.chunk_id), None)
    if matching is None:
        return False
    quote = citation.quoted_text.strip()
    content = matching.content
    start = content.find(quote)
    if start < 0:
        return False
    end = start + len(quote)
    if start > 0 and (content[start - 1].isalnum() or quote[0].isalnum()) and content[start - 1].isalnum() and quote[0].isalnum():
        return False
    if end < len(content) and content[end].isalnum() and quote[-1].isalnum():
        return False
    return True


def validate_citations(citations: list[CitationAttempt], retrieved_chunks: list[RetrievedChunk]) -> bool:
    return bool(citations) and all(validate_citation(citation, retrieved_chunks) for citation in citations)


async def validate_all_citations(ctx):
    """Validate generated citations and convert them into response evidence."""
    if ctx.abstained or not ctx.citations:
        ctx.citations_validated = False
        return ctx

    valid = True
    evidence = []
    chunks_by_id = {chunk.chunk_id: chunk for chunk in ctx.reranked_chunks or ctx.retrieved_chunks}
    for citation in ctx.citations:
        citation.validated = validate_citation(citation, list(chunks_by_id.values()))
        valid = valid and citation.validated
        if citation.validated:
            chunk = chunks_by_id[citation.chunk_id]
            evidence.append({
                "track": citation.track,
                "quote": citation.quoted_text,
                "page": int(citation.page_ref) if citation.page_ref and citation.page_ref.isdigit() else None,
                "clause": citation.clause_ref,
                "source_name": chunk.metadata.get("title") or chunk.source_id,
                "source_url": chunk.metadata.get("url"),
                "last_verified": chunk.metadata.get("last_verified"),
            })

    ctx.citations_validated = valid
    ctx.evidence = evidence
    if not valid:
        ctx.final_answer = (
            "I couldn't verify this information from the available sources. "
            "Please check the relevant government/legal source or consult a qualified lawyer."
        )
        ctx.abstained = True
    else:
        ctx.final_answer = ctx.raw_answer
    return ctx
