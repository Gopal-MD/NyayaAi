"""Cross-encoder reranker (bge-reranker-base) with similarity threshold."""
from functools import lru_cache
from app.orchestrator.context import RetrievedChunk
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def _get_reranker():
    from sentence_transformers import CrossEncoder
    import os
    os.makedirs(settings.HF_CACHE_DIR, exist_ok=True)
    logger.info("loading_reranker", model=settings.RERANKER_MODEL)
    return CrossEncoder(settings.RERANKER_MODEL, max_length=512)


async def rerank(
    query: str,
    chunks: list[RetrievedChunk],
    top_n: int | None = None,
) -> list[RetrievedChunk]:
    """Rerank chunks using cross-encoder. Drops below similarity threshold."""
    if not chunks:
        return []

    top_n = top_n or settings.RERANK_TOP_N

    try:
        reranker = _get_reranker()
        pairs = [(query, c.content[:512]) for c in chunks]
        scores = reranker.predict(pairs)

        scored = [(float(s), c) for s, c in zip(scores, chunks)]
        scored.sort(key=lambda x: x[0], reverse=True)

        # Apply threshold and top_n
        result = []
        for score, chunk in scored[:top_n]:
            if score >= settings.SIMILARITY_THRESHOLD:
                chunk.score = score
                result.append(chunk)

        return result

    except Exception as exc:
        logger.warning("reranker_failed", error=str(exc))
        # Fall back to returning top_n by original score
        return sorted(chunks, key=lambda c: c.score, reverse=True)[:top_n]
