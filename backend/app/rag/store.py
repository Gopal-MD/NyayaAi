"""ChromaDB persistent vector store."""
import os
from functools import lru_cache
from app.core.config import settings
from app.core.logging import get_logger
from app.rag.chunker import Chunk

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def _get_collection():
    import chromadb
    os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
    client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
    collection = client.get_or_create_collection(
        name=settings.CHROMA_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    logger.info("chroma_collection_ready", name=settings.CHROMA_COLLECTION_NAME)
    return collection


def upsert_chunks(chunks: list[Chunk], embeddings: list[list[float]]) -> None:
    """Upsert chunks with precomputed embeddings into ChromaDB."""
    if not chunks:
        return
    collection = _get_collection()
    collection.upsert(
        ids=[c.chunk_id for c in chunks],
        embeddings=embeddings,
        documents=[c.content for c in chunks],
        metadatas=[c.metadata for c in chunks],
    )
    logger.info("chunks_upserted", count=len(chunks))


def query_dense(
    query_embedding: list[float],
    n_results: int = 20,
    where: dict | None = None,
) -> list[dict]:
    """Query ChromaDB by dense vector similarity."""
    collection = _get_collection()
    kwargs: dict = {"query_embeddings": [query_embedding], "n_results": n_results}
    if where:
        kwargs["where"] = where
    results = collection.query(
        include=["documents", "metadatas", "distances"],
        **kwargs,
    )
    items = []
    if results["ids"]:
        for i, chunk_id in enumerate(results["ids"][0]):
            items.append({
                "chunk_id": chunk_id,
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if results["distances"] else 1.0,
            })
    return items


def collection_count() -> int:
    return _get_collection().count()
