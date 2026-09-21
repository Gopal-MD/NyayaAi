"""SQLAlchemy ORM models — all 16 tables."""
import uuid
from datetime import datetime, date
from typing import Any

from sqlalchemy import (
    Boolean, Column, Date, DateTime, ForeignKey,
    Integer, String, Text, JSON, func,
)
from sqlalchemy.orm import relationship

from app.core.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=_uuid)
    firebase_uid = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, nullable=True)
    display_name = Column(String, nullable=True)
    preferred_language = Column(String, default="en")
    auto_delete_days = Column(Integer, default=30)
    created_at = Column(DateTime, default=func.now())
    last_active_at = Column(DateTime, default=func.now(), onupdate=func.now())

    cases = relationship("UserCase", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")


class UserCase(Base):
    __tablename__ = "user_cases"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    domain = Column(String, default="tenancy")
    jurisdiction_state = Column(String, nullable=True)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    auto_delete_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="cases")
    facts = relationship("CaseFact", back_populates="case", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="case", cascade="all, delete-orphan")
    documents = relationship("UploadedDocument", back_populates="case", cascade="all, delete-orphan")
    deadlines = relationship("Deadline", back_populates="case", cascade="all, delete-orphan")
    referrals = relationship("Referral", back_populates="case", cascade="all, delete-orphan")
    generated_documents = relationship("GeneratedDocument", back_populates="case", cascade="all, delete-orphan")


class CaseFact(Base):
    __tablename__ = "case_facts"

    id = Column(String, primary_key=True, default=_uuid)
    case_id = Column(String, ForeignKey("user_cases.id", ondelete="CASCADE"), nullable=False)
    key = Column(String, nullable=False)
    value = Column(Text, nullable=True)
    source_enum = Column(String, default="user_stated")  # user_stated|document|inferred
    source_ref = Column(String, nullable=True)

    case = relationship("UserCase", back_populates="facts")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=_uuid)
    case_id = Column(String, ForeignKey("user_cases.id", ondelete="CASCADE"), nullable=False)
    mode = Column(String, default="chat")  # chat|document_qa|legal_search
    created_at = Column(DateTime, default=func.now())

    case = relationship("UserCase", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String, nullable=False)  # user|assistant
    content = Column(Text, nullable=False)
    language = Column(String, default="en")
    citations = Column(JSON, nullable=True)
    safety_status = Column(String, default="safe")
    created_at = Column(DateTime, default=func.now())

    conversation = relationship("Conversation", back_populates="messages")
    citation_records = relationship("Citation", back_populates="message", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="message", cascade="all, delete-orphan")


class UploadedDocument(Base):
    __tablename__ = "uploaded_documents"

    id = Column(String, primary_key=True, default=_uuid)
    case_id = Column(String, ForeignKey("user_cases.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String, nullable=False)
    mime_type = Column(String, nullable=True)
    size_bytes = Column(Integer, nullable=True)
    extraction_method = Column(String, nullable=True)
    pii_mask_status = Column(String, default="pending")
    pii_entities_masked = Column(Integer, default=0)
    page_count = Column(Integer, nullable=True)
    masked_text = Column(Text, nullable=True)  # stored masked — never raw
    uploaded_at = Column(DateTime, default=func.now())
    auto_delete_at = Column(DateTime, nullable=True)

    case = relationship("UserCase", back_populates="documents")
    analysis = relationship("DocumentAnalysis", back_populates="document", uselist=False, cascade="all, delete-orphan")


class DocumentAnalysis(Base):
    __tablename__ = "document_analyses"

    id = Column(String, primary_key=True, default=_uuid)
    document_id = Column(String, ForeignKey("uploaded_documents.id", ondelete="CASCADE"), nullable=False, unique=True)
    document_type = Column(String, nullable=True)
    structured_facts = Column(JSON, nullable=True)
    clause_analysis = Column(JSON, nullable=True)
    deadlines = Column(JSON, nullable=True)
    summary = Column(Text, nullable=True)
    glossary_terms = Column(JSON, nullable=True)
    lawyer_questions = Column(JSON, nullable=True)
    analysis_version = Column(String, default="1.0")
    created_at = Column(DateTime, default=func.now())

    document = relationship("UploadedDocument", back_populates="analysis")


class Source(Base):
    __tablename__ = "sources"

    id = Column(String, primary_key=True, default=_uuid)
    source_key = Column(String, unique=True, nullable=False)  # matches manifest id
    title = Column(String, nullable=False)
    authority = Column(String, nullable=True)
    jurisdiction = Column(String, nullable=True)
    domain = Column(String, nullable=True)
    url = Column(String, nullable=True)
    status = Column(String, default="active")
    effective_date = Column(String, nullable=True)
    last_verified = Column(String, nullable=True)
    checksum = Column(String, nullable=True)
    version = Column(String, nullable=True)

    chunks = relationship("DocumentChunk", back_populates="source", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String, primary_key=True, default=_uuid)
    source_id = Column(String, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    chroma_id = Column(String, unique=True, nullable=False)
    section_number = Column(String, nullable=True)
    section_title = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    metadata_ = Column("metadata", JSON, nullable=True)
    indexed_at = Column(DateTime, default=func.now())

    source = relationship("Source", back_populates="chunks")
    citations = relationship("Citation", back_populates="chunk")


class Citation(Base):
    __tablename__ = "citations"

    id = Column(String, primary_key=True, default=_uuid)
    message_id = Column(String, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    track_enum = Column(String, nullable=False)  # law|user_document
    chunk_id = Column(String, ForeignKey("document_chunks.id", ondelete="SET NULL"), nullable=True)
    quoted_text = Column(Text, nullable=True)
    page_ref = Column(String, nullable=True)
    clause_ref = Column(String, nullable=True)
    validated = Column(Boolean, default=False)

    message = relationship("Message", back_populates="citation_records")
    chunk = relationship("DocumentChunk", back_populates="citations")


class Deadline(Base):
    __tablename__ = "deadlines"

    id = Column(String, primary_key=True, default=_uuid)
    case_id = Column(String, ForeignKey("user_cases.id", ondelete="CASCADE"), nullable=False)
    label = Column(String, nullable=False)
    due_date = Column(Date, nullable=True)
    source_type = Column(String, nullable=True)  # document|official|user
    source_ref = Column(String, nullable=True)
    user_confirmed = Column(Boolean, default=False)

    case = relationship("UserCase", back_populates="deadlines")


class LegalAidProvider(Base):
    __tablename__ = "legal_aid_providers"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False)
    provider_type = Column(String, nullable=True)  # DLSA|helpline|NGO
    state = Column(String, nullable=True)
    district = Column(String, nullable=True)
    languages = Column(JSON, nullable=True)
    domains = Column(JSON, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    website = Column(String, nullable=True)
    verified_at = Column(String, nullable=True)


class Referral(Base):
    __tablename__ = "referrals"

    id = Column(String, primary_key=True, default=_uuid)
    case_id = Column(String, ForeignKey("user_cases.id", ondelete="CASCADE"), nullable=False)
    provider_id = Column(String, ForeignKey("legal_aid_providers.id", ondelete="SET NULL"), nullable=True)
    eligibility_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

    case = relationship("UserCase", back_populates="referrals")
    provider = relationship("LegalAidProvider")


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(String, primary_key=True, default=_uuid)
    message_id = Column(String, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Integer, nullable=True)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

    message = relationship("Message", back_populates="feedback")
    user = relationship("User")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    user_id_hash = Column(String, nullable=True)  # hashed for privacy
    event_type = Column(String, nullable=False)
    outcome = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="audit_logs")


class GeneratedDocument(Base):
    __tablename__ = "generated_documents"

    id = Column(String, primary_key=True, default=_uuid)
    case_id = Column(String, ForeignKey("user_cases.id", ondelete="CASCADE"), nullable=False)
    doc_type = Column(String, nullable=True)  # brief|demand_letter
    filename = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())
    auto_delete_at = Column(DateTime, nullable=True)

    case = relationship("UserCase", back_populates="generated_documents")
