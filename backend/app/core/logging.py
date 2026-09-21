"""Structured logging with PII/document-text redaction filter."""
import logging
import re
import structlog
from app.core.config import settings

# Patterns that must never appear in logs
_AADHAAR_RE = re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")
_PAN_RE = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")
_REDACT_KEYS = {
    "document_text",
    "extracted_text",
    "masked_text",
    "clause_text",
    "raw_text",
    "content",
    "page_text",
}


class PIIRedactFilter(logging.Filter):
    """Removes PII and document content from log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, dict):
            record.msg = _redact_processor(None, None, record.msg.copy())
            record.args = ()
            return True

        msg = str(record.getMessage())
        msg = _AADHAAR_RE.sub("[AADHAAR-REDACTED]", msg)
        msg = _PAN_RE.sub("[PAN-REDACTED]", msg)
        record.msg = msg
        record.args = ()
        return True


def _redact_processor(logger, method, event_dict: dict) -> dict:
    """structlog processor that strips sensitive keys."""
    for key in list(event_dict.keys()):
        if key in _REDACT_KEYS:
            event_dict[key] = "[REDACTED]"
        elif isinstance(event_dict.get(key), str):
            val = event_dict[key]
            val = _AADHAAR_RE.sub("[AADHAAR-REDACTED]", val)
            val = _PAN_RE.sub("[PAN-REDACTED]", val)
            event_dict[key] = val
    return event_dict


def setup_logging() -> None:
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            _redact_processor,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ]
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.addFilter(PIIRedactFilter())

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(log_level)


def get_logger(name: str):
    return structlog.get_logger(name)
