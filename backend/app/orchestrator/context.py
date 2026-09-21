"""PipelineContext — shared state passed through every pipeline step."""
from typing import Any, Literal
from pydantic import BaseModel, Field


class EmergencyContact(BaseModel):
    id: str
    name: str
    number: str
    type: str
    scope: str
    languages: list[str] = []
    description: str = ""


class RetrievedChunk(BaseModel):
    chunk_id: str
    source_id: str
    section_title: str = ""
    section_number: str = ""
    content: str
    score: float = 0.0
    metadata: dict = {}


class CitationAttempt(BaseModel):
    chunk_id: str
    quoted_text: str
    claim: str = ""
    validated: bool = False
    track: Literal["user_document", "official_source", "unverified"] = "unverified"
    page_ref: str | None = None
    clause_ref: str | None = None


class EvidenceItem(BaseModel):
    track: Literal["user_document", "official_source", "unverified"]
    quote: str | None = None
    page: int | None = None
    clause: str | None = None
    source_name: str | None = None
    source_url: str | None = None
    last_verified: str | None = None


class PipelineContext(BaseModel):
    # Input
    user_id: str
    case_id: str
    raw_query: str
    language: str = "en"
    mode: Literal["chat", "document_qa", "legal_search"] = "chat"
    document_text: str | None = None

    # Safety
    safety_status: Literal["safe", "high_risk", "unknown"] = "unknown"
    emergency_resources: list[EmergencyContact] = []

    # Language
    query_en: str | None = None
    detected_language: str | None = None

    # Intent
    intent: str | None = None
    domain: str | None = None
    jurisdiction: str | None = None

    # Facts
    extracted_facts: dict = {}
    missing_required_facts: list[str] = []
    clarifying_question: str | None = None

    # Retrieval
    retrieved_chunks: list[RetrievedChunk] = []
    reranked_chunks: list[RetrievedChunk] = []

    # Generation
    raw_answer: str | None = None
    citations: list[CitationAttempt] = []
    citations_validated: bool = False
    generation_attempts: int = 0

    # Evidence (final, validated)
    evidence: list[EvidenceItem] = []

    # Action Plan
    action_plan: dict | None = None

    # Output
    final_answer: str | None = None
    final_language: str | None = None
    machine_translated: bool = False
    english_original: str | None = None
    abstained: bool = False


class PipelineAbortError(Exception):
    """Raised to short-circuit the pipeline (e.g. safety gate fires)."""
    def __init__(self, reason: str, context: PipelineContext):
        super().__init__(reason)
        self.context = context
