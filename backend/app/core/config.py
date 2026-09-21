"""Core configuration — reads all settings from environment variables."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # App
    APP_ENV: str = "development"
    APP_SECRET_KEY: str = "change-me-in-production"

    # Groq
    GROQ_API_KEY: str = ""
    GROQ_MODEL_REASONING: str = "llama-3.3-70b-versatile"
    GROQ_MODEL_CLASSIFY: str = "llama-3.1-8b-instant"
    GROQ_MODEL_WHISPER: str = "whisper-large-v3"

    # Firebase
    FIREBASE_PROJECT_ID: str = ""
    FIREBASE_SERVICE_ACCOUNT_PATH: str = ""
    FIREBASE_SERVICE_ACCOUNT_JSON: str = ""

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./nyayasaathi.db"

    # ChromaDB
    CHROMA_PERSIST_DIR: str = "./data/chroma_index"
    CHROMA_COLLECTION_NAME: str = "nyayasaathi_sources"

    # Embeddings
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    RERANKER_MODEL: str = "BAAI/bge-reranker-base"
    HF_CACHE_DIR: str = "./data/hf_cache"

    # BM25
    BM25_INDEX_PATH: str = "./data/bm25_index.pkl"

    # Retrieval
    RETRIEVAL_TOP_K: int = 20
    RERANK_TOP_N: int = 5
    SIMILARITY_THRESHOLD: float = 0.35

    # Upload
    MAX_UPLOAD_MB: int = 10

    # Rate limits
    RATE_LIMIT_CHAT: str = "30/minute"
    RATE_LIMIT_UPLOAD: str = "10/minute"

    # Privacy
    AUTO_DELETE_DAYS: int = 30

    # Demo cache
    DEMO_CACHE_ENABLED: bool = False
    DEMO_CACHE_DIR: str = "./data/demo_cache"

    # Logging
    LOG_LEVEL: str = "INFO"

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
