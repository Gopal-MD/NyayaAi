"""Embedding model wrapper using sentence-transformers (bge-m3)."""
import os
from functools import lru_cache
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def _get_model():
    from sentence_transformers import SentenceTransformer
    os.makedirs(settings.HF_CACHE_DIR, exist_ok=True)
    logger.info("loading_embedding_model", model=settings.EMBEDDING_MODEL)
    return SentenceTransformer(
        settings.EMBEDDING_MODEL,
        cache_folder=settings.HF_CACHE_DIR,
    )


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts. Returns list of float vectors."""
    if not texts:
        return []
    model = _get_model()
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return embeddings.tolist()


def embed_query(text: str) -> list[float]:
    """Embed a single query string."""
    return embed_texts([text])[0]
