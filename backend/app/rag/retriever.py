"""Hybrid BM25 + dense retrieval with jurisdiction filtering."""
from app.orchestrator.context import RetrievedChunk
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


async def hybrid_search(
    query: str,
    jurisdiction: str | None = "TN",
    top_k: int | None = None,
) -> list[RetrievedChunk]:
    """Hybrid BM25 + dense search with jurisdiction filter."""
    top_k = top_k or settings.RETRIEVAL_TOP_K

    # Dense retrieval
    try:
        from app.rag.embedder import embed_query
        from app.rag.store import query_dense
        q_emb = embed_query(query)
        dense_results = query_dense(q_emb, n_results=top_k)
    except Exception as exc:
        logger.warning("dense_retrieval_failed", error=str(exc))
        dense_results = []

    # BM25 retrieval
    try:
        from app.rag.bm25_index import query_bm25
        bm25_results = query_bm25(query, n_results=top_k)
    except Exception as exc:
        logger.warning("bm25_retrieval_failed", error=str(exc))
        bm25_results = []

    # Reciprocal rank fusion
    fused = _reciprocal_rank_fusion(dense_results, bm25_results)

    # Build RetrievedChunk objects, applying jurisdiction filter
    chunks = []
    seen_ids = set()
    for item in fused[:top_k]:
        cid = item["chunk_id"]
        if cid in seen_ids:
            continue
        seen_ids.add(cid)

        meta = item.get("metadata", {})
        chunk_jurisdiction = meta.get("jurisdiction", "central")

        # Exclude chunks whose jurisdiction doesn't match (unless central)
        if jurisdiction and chunk_jurisdiction not in ("central", jurisdiction.upper()):
            logger.debug(
                "chunk_jurisdiction_excluded",
                chunk_id=cid,
                chunk_jur=chunk_jurisdiction,
                user_jur=jurisdiction,
            )
            continue

        chunks.append(RetrievedChunk(
            chunk_id=cid,
            source_id=meta.get("source_id", ""),
            section_title=meta.get("section_title", ""),
            section_number=meta.get("section_number", ""),
            content=item.get("content", ""),
            score=item.get("score", 0.0),
            metadata=meta,
        ))

    return chunks


def _reciprocal_rank_fusion(
    dense: list[dict],
    bm25: list[dict],
    k: int = 60,
) -> list[dict]:
    """Fuse two ranked lists using Reciprocal Rank Fusion."""
    scores: dict[str, float] = {}
    content_map: dict[str, dict] = {}

    for rank, item in enumerate(dense):
        cid = item["chunk_id"]
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (rank + k)
        content_map[cid] = item

    for rank, item in enumerate(bm25):
        cid = item["chunk_id"]
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (rank + k)
        if cid not in content_map:
            content_map[cid] = item

    sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
    return [
        {**content_map[cid], "score": scores[cid]}
        for cid in sorted_ids
    ]
