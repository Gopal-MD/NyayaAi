"""Protected legal terms glossary — terms that must not be translated."""
import json
import os
from functools import lru_cache

_GLOSSARY_PATH = os.path.join(
    os.path.dirname(__file__), "../../data/glossary/legal_terms.json"
)


@lru_cache(maxsize=1)
def load_glossary() -> list[dict]:
    try:
        with open(_GLOSSARY_PATH) as f:
            data = json.load(f)
            return data.get("terms", [])
    except Exception:
        return []


def get_protected_terms() -> list[str]:
    """Return English terms that must remain untranslated."""
    return [t["en"] for t in load_glossary() if t.get("protected", False)]


def get_term_translation(term_en: str, target_lang: str) -> str | None:
    """Look up a term translation from the glossary."""
    for t in load_glossary():
        if t.get("en", "").lower() == term_en.lower():
            return t.get(target_lang)
    return None
