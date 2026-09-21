"""Safety gate — keyword/regex first pass + LLM classifier confirmation."""
import re
from pydantic import BaseModel
from app.orchestrator.context import PipelineContext, EmergencyContact
from app.core.logging import get_logger

logger = get_logger(__name__)

# High-risk keyword patterns (Stage 1 — deterministic)
_HIGH_RISK_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\barrest(ed|ing)?\b",
        r"\bwarrant\b",
        r"\bpolice\b.{0,30}\b(case|complaint|fir|station)\b",
        r"\bdomestic\s+violence\b",
        r"\babuse(d|r|rs)?\b",
        r"\bthreaten(ing|ed)?\b",
        r"\bphysical(ly)?\s+(harm|hurt|attack)\b",
        r"\bchild\s+(safety|abuse|harm)\b",
        r"\bevict(ion|ed|ing)?\s+(today|now|tonight|tomorrow|24\s*hours|immediately)\b",
        r"\bcourt\s+(tomorrow|today|tonight|in\s+\d+\s+hours?)\b",
        r"\bself.harm\b",
        r"\bsuicid(e|al)\b",
        r"\bwant\s+to\s+(die|end\s+my\s+life|kill\s+myself)\b",
        r"\bimminent\s+(threat|danger)\b",
        r"\bhelp\s+me\s+(please)?.{0,10}(urgent|emergency|danger)\b",
    ]
]


class SafetyDecision(BaseModel):
    risk_level: str = "safe"  # "safe" | "high_risk"
    categories: list[str] = []


def _keyword_scan(text: str) -> tuple[bool, list[str]]:
    categories = []
    for pattern in _HIGH_RISK_PATTERNS:
        if pattern.search(text):
            categories.append(pattern.pattern[:30])
    return bool(categories), categories


async def run_safety_gate(ctx: PipelineContext) -> PipelineContext:
    """Run the safety gate. Sets ctx.safety_status and ctx.emergency_resources."""
    text = ctx.raw_query

    # Stage 1: keyword/regex (deterministic — no LLM)
    is_high_risk, categories = _keyword_scan(text)

    if not is_high_risk:
        # Stage 2: LLM classifier for ambiguous cases
        try:
            from app.core.groq_client import groq_json
            from app.core.config import settings

            if settings.GROQ_API_KEY:
                prompt = f"""Classify the following user message for legal risk level.

Message: {text[:500]}

Return JSON:
{{
  "risk_level": "safe" or "high_risk",
  "categories": []
}}

Mark as "high_risk" ONLY if the message indicates: arrest, active domestic violence, 
child in immediate danger, imminent physical threat, self-harm intent, 
eviction happening today/now, or court deadline within 24 hours.
For normal tenancy questions, return "safe"."""

                decision = await groq_json(prompt, SafetyDecision, model="classify")
                if decision.risk_level == "high_risk":
                    is_high_risk = True
                    categories = decision.categories
        except Exception as exc:
            logger.warning("safety_llm_failed", error=str(exc))
            # Fail-open for LLM failures on non-keyword cases

    ctx.safety_status = "high_risk" if is_high_risk else "safe"

    if is_high_risk:
        from app.safety.emergency_resources import get_emergency_resources
        ctx.emergency_resources = get_emergency_resources(categories)
        logger.info("safety_gate_triggered", categories=categories)

    return ctx
