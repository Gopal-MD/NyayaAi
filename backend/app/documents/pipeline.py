"""Local document analysis pipeline with optional LLM augmentation."""
import re
from datetime import datetime

from app.models.schemas import StructuredFacts

_LIMITATION = (
    "NyayaAi provides legal information to help you understand and prepare. "
    "It is not legal advice and does not replace a qualified lawyer."
)


def _first_match(pattern: str, text: str, flags: int = re.IGNORECASE) -> str | None:
    match = re.search(pattern, text, flags)
    return match.group(1).strip() if match else None


def _extract_facts(text: str) -> dict:
    facts = StructuredFacts().model_dump()
    facts["landlord_name"] = _first_match(r"(?:landlord|lessor)\s*[:\-]\s*([^\n,]+)", text)
    tenant = _first_match(r"(?:tenant|lessee)\s*[:\-]\s*([^\n,]+)", text)
    facts["tenant_names"] = [tenant] if tenant else []
    facts["property_address"] = _first_match(r"(?:property address|address)\s*[:\-]\s*([^\n]+)", text)

    for key, pattern in {
        "monthly_rent": r"(?:monthly rent|rent)\s*[:\-]?\s*(?:INR|Rs\.?|₹)?\s*([\d,]+(?:\.\d+)?)",
        "security_deposit": r"(?:security deposit|deposit)\s*[:\-]?\s*(?:INR|Rs\.?|₹)?\s*([\d,]+(?:\.\d+)?)",
    }.items():
        value = _first_match(pattern, text)
        if value:
            facts[key] = float(value.replace(",", ""))

    for key, pattern in {
        "lock_in_months": r"lock[- ]?in(?: period)?\s*[:\-]?\s*(\d+)\s*months?",
        "notice_period_landlord_days": r"landlord[^\n]{0,80}?(\d+)\s*days?[^\n]{0,20}notice",
        "notice_period_tenant_days": r"tenant[^\n]{0,80}?(\d+)\s*days?[^\n]{0,20}notice",
    }.items():
        value = _first_match(pattern, text)
        if value:
            facts[key] = int(value)

    facts["lease_start"] = _first_match(r"(?:lease|tenancy)\s+start(?:s| date)?\s*[:\-]\s*([^\n]+)", text)
    facts["lease_end"] = _first_match(r"(?:lease|tenancy)\s+end(?:s| date)?\s*[:\-]\s*([^\n]+)", text)
    facts["termination_clauses"] = [line.strip() for line in text.splitlines() if "terminat" in line.lower()][:5]
    facts["penalty_clauses"] = [line.strip() for line in text.splitlines() if any(word in line.lower() for word in ("penalty", "late fee", "forfeit"))][:5]
    facts["maintenance_obligations"] = [line.strip() for line in text.splitlines() if "maintenan" in line.lower()][:5]
    facts["subletting_restrictions"] = [line.strip() for line in text.splitlines() if "sublet" in line.lower()][:5]
    facts["missing_fields"] = [name for name, value in facts.items() if value in (None, [], "") and name not in {"missing_fields"}]
    return facts


def _clause_analysis(text: str) -> list[dict]:
    result = []
    rules = [
        ("security_deposit", "Security deposit", "yellow", "Review the deposit amount and return conditions."),
        ("lock-in", "Lock-in period", "yellow", "A lock-in period may limit early termination."),
        ("penalty", "Penalty clause", "red", "A penalty or late fee should be checked carefully."),
        ("maintenance", "Maintenance obligations", "yellow", "Confirm which repairs each party must handle."),
        ("sublet", "Subletting restriction", "yellow", "Check whether permission is required before subletting."),
        ("terminat", "Termination clause", "yellow", "Check notice and termination conditions before acting."),
    ]
    for index, line in enumerate(text.splitlines(), 1):
        lowered = line.lower()
        for keyword, label, risk, reason in rules:
            if keyword in lowered:
                result.append({
                    "clause_id": f"clause-{len(result) + 1}",
                    "label": label,
                    "page": 1,
                    "quote": line.strip(),
                    "risk_level": risk,
                    "reason": f"{reason} This may be unusual or one-sided; consider asking a lawyer.",
                    "citation": {"page": 1, "line": index},
                })
                break
    return result


def _deadlines(text: str) -> list[dict]:
    deadlines = []
    for index, line in enumerate(text.splitlines(), 1):
        match = re.search(r"(\d{1,3})\s+days?", line, re.IGNORECASE)
        if match and any(word in line.lower() for word in ("notice", "vacate", "pay", "respond")):
            deadlines.append({"label": line.strip(), "due_date": None, "source_type": "document", "source_ref": f"page 1, line {index}"})
    return deadlines[:10]


async def run_document_analysis(text: str, filename: str) -> dict:
    is_rental = any(word in text.lower() for word in ("rent", "tenant", "landlord", "lease", "tenancy"))
    facts = _extract_facts(text)
    clauses = _clause_analysis(text)
    deadlines = _deadlines(text)
    glossary = [term for term in ("security deposit", "lock-in period", "notice period", "subletting") if term in text.lower()]
    summary = "This document appears to be a rental agreement." if is_rental else "This document could not be confidently classified as a rental agreement."
    questions = [
        "Which terms should I confirm before signing or responding?",
        "What happens if either party ends the agreement early?",
        "Which repairs and payments are each party responsible for?",
    ]
    return {
        "document_type": "rental_agreement" if is_rental else "other",
        "structured_facts": facts,
        "clause_analysis": clauses,
        "deadlines": deadlines,
        "summary": summary,
        "glossary_terms": glossary,
        "lawyer_questions": questions,
        "limitation_text": _LIMITATION,
        "generated_at": datetime.utcnow().isoformat(),
    }
