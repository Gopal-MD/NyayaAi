"""Deterministic PII detection and masking for stored document text."""
import re


_PATTERNS = [
    (re.compile(r"\b\d{4}[ -]?\d{4}[ -]?\d{4}\b"), "[AADHAAR-REDACTED]"),
    (re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b", re.IGNORECASE), "[PAN-REDACTED]"),
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), "[EMAIL-REDACTED]"),
    (re.compile(r"(?<!\d)(?:\+91[ -]?)?[6-9]\d{9}(?!\d)"), "[PHONE-REDACTED]"),
]


def mask_pii(text: str) -> tuple[str, int]:
    masked = text
    count = 0
    for pattern, replacement in _PATTERNS:
        masked, replacements = pattern.subn(replacement, masked)
        count += replacements
    return masked, count
