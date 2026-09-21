"""Documents router: upload, analyze, compare."""
import io
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.auth import CurrentUser
from app.core.db import get_db
from app.core.config import settings
from app.core.security import limiter
from app.models.db import User, UserCase, UploadedDocument, DocumentAnalysis, AuditLog
from app.models.schemas import DocumentUploadResponse, DocumentAnalysisResponse, StructuredFacts
import hashlib

router = APIRouter()

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".docx"}


@router.post("/upload", response_model=DocumentUploadResponse, status_code=201)
@limiter.limit(settings.RATE_LIMIT_UPLOAD)
async def upload_document(
    request,
    current_user: CurrentUser,
    case_id: str = Form(...),
    consent_accepted: bool = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    # Consent check
    if not consent_accepted:
        raise HTTPException(
            status_code=400,
            detail="Consent must be accepted before uploading a document.",
        )

    # File type validation
    import os
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Accepted: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Read file (but cap at max size + 1 byte to detect over-limit)
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    content = await file.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds {settings.MAX_UPLOAD_MB} MB limit.",
        )

    # Get user
    result = await db.execute(
        select(User).where(User.firebase_uid == current_user["user_id"])
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found. Call /auth/verify first.")

    # Verify case belongs to user
    result = await db.execute(
        select(UserCase).where(UserCase.id == case_id, UserCase.user_id == user.id)
    )
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")

    # Extract text
    try:
        from app.documents.extractor import extract_document
        pages = extract_document(content, file.filename or "", ext)
        extraction_method = pages[0].method if pages else "none"
        page_count = len(pages)
        raw_text = "\n\n".join(p.text for p in pages)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Text extraction failed: {exc}")

    # PII masking
    try:
        from app.documents.pii import mask_pii
        masked_text, pii_count = mask_pii(raw_text)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PII masking failed: {exc}")

    # Store document record (masked text only)
    auto_delete = datetime.utcnow() + timedelta(days=user.auto_delete_days)
    doc = UploadedDocument(
        case_id=case_id,
        filename=file.filename,
        mime_type=file.content_type,
        size_bytes=len(content),
        extraction_method=extraction_method,
        pii_mask_status="masked",
        pii_entities_masked=pii_count,
        page_count=page_count,
        masked_text=masked_text,
        auto_delete_at=auto_delete,
    )
    db.add(doc)

    # Consent + audit log
    db.add(AuditLog(
        user_id=user.id,
        user_id_hash=hashlib.sha256(user.firebase_uid.encode()).hexdigest(),
        event_type="document_uploaded",
        outcome="success",
    ))
    await db.commit()
    await db.refresh(doc)

    return DocumentUploadResponse(
        document_id=doc.id,
        filename=doc.filename,
        extraction_method=extraction_method,
        page_count=page_count,
        pii_entities_masked=pii_count,
        ready_for_analysis=True,
    )


@router.post("/analyze", response_model=DocumentAnalysisResponse)
async def analyze_document(
    body: dict,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    document_id = body.get("document_id")
    case_id = body.get("case_id")

    result = await db.execute(
        select(User).where(User.firebase_uid == current_user["user_id"])
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Verify document belongs to user's case
    result = await db.execute(
        select(UploadedDocument, UserCase)
        .join(UserCase, UploadedDocument.case_id == UserCase.id)
        .where(UploadedDocument.id == document_id, UserCase.user_id == user.id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Document not found.")

    doc = row[0]
    masked_text = doc.masked_text or ""

    # Run analysis pipeline
    from app.documents.pipeline import run_document_analysis
    analysis_result = await run_document_analysis(masked_text, doc.filename or "")

    # Store analysis
    analysis = DocumentAnalysis(
        document_id=doc.id,
        document_type=analysis_result.get("document_type", "unknown"),
        structured_facts=analysis_result.get("structured_facts", {}),
        clause_analysis=analysis_result.get("clause_analysis", []),
        deadlines=analysis_result.get("deadlines", []),
        summary=analysis_result.get("summary", ""),
        glossary_terms=analysis_result.get("glossary_terms", []),
        lawyer_questions=analysis_result.get("lawyer_questions", []),
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)

    facts = analysis.structured_facts or {}
    return DocumentAnalysisResponse(
        analysis_id=analysis.id,
        document_type=analysis.document_type or "unknown",
        structured_facts=StructuredFacts(**{k: facts.get(k) for k in StructuredFacts.model_fields}),
        clause_analysis=analysis.clause_analysis or [],
        deadlines=analysis.deadlines or [],
        summary=analysis.summary or "",
        glossary_terms=analysis.glossary_terms or [],
        lawyer_questions=analysis.lawyer_questions or [],
        limitation_text=(
            "NyayaAi provides legal information to help you understand and prepare. "
            "It is not legal advice and does not replace a qualified lawyer."
        ),
    )


@router.post("/compare")
async def compare_documents(
    body: dict,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    doc_id_1 = body.get("document_id_1")
    doc_id_2 = body.get("document_id_2")

    result = await db.execute(
        select(User).where(User.firebase_uid == current_user["user_id"])
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Fetch both documents
    docs = []
    for doc_id in [doc_id_1, doc_id_2]:
        result = await db.execute(
            select(UploadedDocument, UserCase)
            .join(UserCase, UploadedDocument.case_id == UserCase.id)
            .where(UploadedDocument.id == doc_id, UserCase.user_id == user.id)
        )
        row = result.first()
        if not row:
            raise HTTPException(status_code=404, detail=f"Document {doc_id} not found.")
        docs.append(row[0])

    from app.documents.comparator import compare_documents as _compare
    comparison = await _compare(docs[0].masked_text or "", docs[1].masked_text or "")
    return comparison
