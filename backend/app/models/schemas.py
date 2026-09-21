"""Pydantic v2 request/response schemas for all API endpoints."""
from datetime import datetime, date
from typing import Any, Literal
from pydantic import BaseModel, Field, field_validator


# ── Auth ─────────────────────────────────────────────────────────────────────

class TokenVerifyRequest(BaseModel):
    id_token: str

class UserResponse(BaseModel):
    user_id: str
    email: str
    display_name: str
    preferred_language: str = "en"
    is_anonymous: bool = False
    auto_delete_days: int = 30


# ── Cases ────────────────────────────────────────────────────────────────────

class CaseCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    domain: str = "tenancy"

class CaseResponse(BaseModel):
    case_id: str
    title: str
    domain: str
    jurisdiction_state: str | None
    status: str
    created_at: datetime
    updated_at: datetime

class CaseListResponse(BaseModel):
    cases: list[CaseResponse]
    total: int


# ── Documents ────────────────────────────────────────────────────────────────

class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    extraction_method: str
    page_count: int
    pii_entities_masked: int
    ready_for_analysis: bool

class ClauseAnalysisItem(BaseModel):
    clause_id: str
    label: str
    page: int | None
    quote: str | None
    risk_level: Literal["green", "yellow", "red"]
    reason: str
    citation: dict | None = None

class DeadlineItem(BaseModel):
    label: str
    due_date: str | None
    source_type: str
    source_ref: str

class StructuredFacts(BaseModel):
    landlord_name: str | None = None
    tenant_names: list[str] = []
    property_address: str | None = None
    monthly_rent: float | None = None
    security_deposit: float | None = None
    lease_start: str | None = None
    lease_end: str | None = None
    lock_in_months: int | None = None
    notice_period_landlord_days: int | None = None
    notice_period_tenant_days: int | None = None
    termination_clauses: list[str] = []
    penalty_clauses: list[str] = []
    maintenance_obligations: list[str] = []
    subletting_restrictions: list[str] = []
    missing_fields: list[str] = []

class DocumentAnalysisResponse(BaseModel):
    analysis_id: str
    document_type: str
    structured_facts: StructuredFacts
    clause_analysis: list[ClauseAnalysisItem]
    deadlines: list[DeadlineItem]
    summary: str
    glossary_terms: list[str]
    lawyer_questions: list[str]
    limitation_text: str


# ── Chat ─────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    case_id: str
    message: str = Field(min_length=1, max_length=4000)
    language: str = "en"
    mode: Literal["chat", "document_qa", "legal_search"] = "chat"
    document_id: str | None = None

class EvidenceItem(BaseModel):
    track: Literal["user_document", "official_source", "unverified"]
    quote: str | None = None
    page: int | None = None
    clause: str | None = None
    source_name: str | None = None
    source_url: str | None = None
    last_verified: str | None = None

class ChatResponse(BaseModel):
    message_id: str
    answer: str
    language: str
    evidence: list[EvidenceItem] = []
    citations_validated: bool = False
    safety_status: Literal["safe", "high_risk"] = "safe"
    emergency_resources: list[dict] = []
    machine_translated: bool = False
    english_original: str | None = None
    clarifying_question: str | None = None
    abstained: bool = False
    limitation_text: str = (
        "NyayaAi provides legal information to help you understand and prepare. "
        "It is not legal advice and does not replace a qualified lawyer."
    )


# ── Legal Search ──────────────────────────────────────────────────────────────

class LegalSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    jurisdiction: str = "TN"
    language: str = "en"

class LegalSearchResponse(BaseModel):
    answer: str
    citations: list[dict] = []
    abstained: bool = False
    limitation_text: str = (
        "NyayaAi provides legal information to help you understand and prepare. "
        "It is not legal advice and does not replace a qualified lawyer."
    )


# ── Action Plan ───────────────────────────────────────────────────────────────

class ActionPlanRequest(BaseModel):
    case_id: str
    analysis_id: str | None = None

class ActionPlanSections(BaseModel):
    what_i_understood: str
    possible_legal_area: str
    what_you_can_do_next: list[str]
    documents_you_may_need: list[str]
    important_dates: list[dict]
    official_resources: list[dict]
    when_to_seek_a_lawyer: str
    important_limitation: str

class ActionPlanResponse(BaseModel):
    plan_id: str
    sections: ActionPlanSections


# ── Referrals ─────────────────────────────────────────────────────────────────

class ReferralRequest(BaseModel):
    case_id: str
    state: str | None = None
    district: str | None = None
    language: str | None = None
    domain: str = "tenancy"
    income_eligible: bool | None = None

class ProviderItem(BaseModel):
    id: str
    name: str
    provider_type: str
    state: str | None
    phone: str | None
    languages: list[str]
    domains: list[str]
    verified_at: str | None

class ReferralResponse(BaseModel):
    providers: list[ProviderItem]
    eligibility_applied: bool = False


# ── Deadlines ─────────────────────────────────────────────────────────────────

class DeadlineListResponse(BaseModel):
    deadlines: list[DeadlineItem]


# ── Feedback ──────────────────────────────────────────────────────────────────

class FeedbackRequest(BaseModel):
    message_id: str
    rating: int = Field(ge=1, le=5)
    comment: str | None = None

class FeedbackResponse(BaseModel):
    feedback_id: str
    status: str = "received"


# ── Error ─────────────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    error: str
    detail: str
    retry_after_seconds: int | None = None


# ── Voice ─────────────────────────────────────────────────────────────────────

class TranscriptResponse(BaseModel):
    transcript: str
    language: str
    confidence: float | None = None
