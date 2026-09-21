"""BM25 sparse index builder and query interface."""
import os
import pickle
import re
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_index_cache: tuple | None = None  # (bm25, chunk_ids, chunk_contents)


def _tokenise(text: str) -> list[str]:
    return re.findall(r"\b\w+\b", text.lower())


def build_bm25_index(chunk_ids: list[str], contents: list[str]) -> None:
    """Build a BM25 index and persist it to disk."""
    from rank_bm25 import BM25Okapi
    tokenised = [_tokenise(c) for c in contents]
    bm25 = BM25Okapi(tokenised)
    os.makedirs(os.path.dirname(settings.BM25_INDEX_PATH), exist_ok=True)
    with open(settings.BM25_INDEX_PATH, "wb") as f:
        pickle.dump({"bm25": bm25, "chunk_ids": chunk_ids, "contents": contents}, f)
    logger.info("bm25_index_built", chunks=len(chunk_ids))
    # Clear cache
    global _index_cache
    _index_cache = None


def _load_index() -> tuple | None:
    global _index_cache
    if _index_cache:
        return _index_cache
    if not os.path.exists(settings.BM25_INDEX_PATH):
        return None
    try:
        with open(settings.BM25_INDEX_PATH, "rb") as f:
            data = pickle.load(f)
        _index_cache = (data["bm25"], data["chunk_ids"], data["contents"])
        return _index_cache
    except Exception as exc:
        logger.warning("bm25_load_failed", error=str(exc))
        return None


def query_bm25(query: str, n_results: int = 20) -> list[dict]:
    """Query the BM25 index. Returns list of {chunk_id, content, score}."""
    idx = _load_index()
    if not idx:
        return []
    bm25, chunk_ids, contents = idx
    tokens = _tokenise(query)
    scores = bm25.get_scores(tokens)
    # Get top-n indices
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:n_results]
    return [
        {"chunk_id": chunk_ids[i], "content": contents[i], "score": float(scores[i])}
        for i in top_indices
        if scores[i] > 0
    ]
