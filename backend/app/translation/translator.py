"""Translation utilities: to English and to target language with protected terms."""
from app.core.logging import get_logger
from app.orchestrator.context import PipelineContext

logger = get_logger(__name__)

_LIMITATION = (
    "NyayaAi provides legal information to help you understand and prepare. "
    "It is not legal advice and does not replace a qualified lawyer."
)


async def translate_to_en(text: str, source_lang: str) -> str:
    """Translate query to English."""
    if source_lang == "en" or not text.strip():
        return text
    try:
        from app.core.groq_client import groq_text
        prompt = (
            f"Translate the following {_lang_name(source_lang)} text to English. "
            f"Return only the translation, nothing else.\n\nText: {text}"
        )
        return await groq_text(prompt, model="classify")
    except Exception as exc:
        logger.warning("translate_to_en_failed", error=str(exc))
        return text


async def translate_output(ctx: PipelineContext) -> PipelineContext:
    """Translate the final answer to the user's language if needed."""
    target_lang = ctx.detected_language or ctx.language

    if not ctx.final_answer:
        ctx.final_answer = ""
        ctx.final_language = target_lang
        return ctx

    if target_lang == "en":
        ctx.final_language = "en"
        ctx.machine_translated = False
        return ctx

    try:
        from app.core.groq_client import groq_text
        from app.translation.glossary import get_protected_terms

        protected = get_protected_terms()
        protected_note = ""
        if protected:
            protected_note = (
                f"Do NOT translate these terms — keep them exactly as-is: "
                f"{', '.join(protected[:20])}. "
                f"Also keep all section numbers, amounts (₹), dates, and party names unchanged."
            )

        # Simple language pre-pass
        simplified = await _simplify(ctx.final_answer)

        prompt = (
            f"Translate the following English legal text to {_lang_name(target_lang)}. "
            f"{protected_note} "
            f"Use simple, clear language suitable for a first-time renter.\n\n"
            f"Text:\n{simplified}"
        )
        translated = await groq_text(prompt, model="classify")

        ctx.english_original = ctx.final_answer
        ctx.final_answer = translated
        ctx.final_language = target_lang
        ctx.machine_translated = True

    except Exception as exc:
        logger.warning("translate_output_failed", error=str(exc))
        ctx.final_language = "en"
        ctx.machine_translated = False

    return ctx


async def _simplify(text: str) -> str:
    """Pre-pass: replace complex legal English with plain English."""
    try:
        from app.core.groq_client import groq_text
        prompt = (
            "Rewrite the following legal text in simple, plain English "
            "suitable for someone with no legal background. "
            "Keep all specific numbers, dates, names, and statute references unchanged.\n\n"
            f"Text:\n{text[:2000]}"
        )
        return await groq_text(prompt, model="classify")
    except Exception:
        return text


def _lang_name(code: str) -> str:
    return {"en": "English", "ta": "Tamil", "hi": "Hindi"}.get(code, "English")
