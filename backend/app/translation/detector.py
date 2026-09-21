"""Language detection."""
from app.core.logging import get_logger

logger = get_logger(__name__)


def detect_language(text: str) -> str:
    """Detect language of text. Returns ISO code: en, ta, hi."""
    try:
        from langdetect import detect, LangDetectException
        lang = detect(text[:500])
        # Map to supported languages
        if lang in ("ta",):
            return "ta"
        if lang in ("hi",):
            return "hi"
        return "en"
    except Exception as exc:
        logger.warning("language_detection_failed", error=str(exc))
        return "en"
