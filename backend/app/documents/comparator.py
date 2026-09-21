"""Simple clause comparison for two extracted documents."""
import re


def _clauses(text: str) -> dict[str, str]:
    clauses = {}
    for line in text.splitlines():
        clean = line.strip()
        if not clean:
            continue
        match = re.match(r"(?:section\s+)?(\d+(?:\.\d+)?)\s*[.)-]\s*(.*)", clean, re.IGNORECASE)
        key = match.group(1) if match else clean.lower()[:60]
        clauses[key] = match.group(2).strip() if match else clean
    return clauses


async def compare_documents(first_text: str, second_text: str) -> dict:
    first = _clauses(first_text)
    second = _clauses(second_text)
    changes = []
    for key in sorted(set(first) | set(second)):
        if key not in first:
            changes.append({"clause_ref": key, "change_type": "added", "before": None, "after": second[key]})
        elif key not in second:
            changes.append({"clause_ref": key, "change_type": "removed", "before": first[key], "after": None})
        elif first[key] != second[key]:
            changes.append({"clause_ref": key, "change_type": "modified", "before": first[key], "after": second[key]})
    return {
        "changes": changes,
        "summary": f"Compared {len(set(first) | set(second))} clause entries.",
        "limitation_text": "NyayaAi provides legal information to help you understand and prepare. It is not legal advice and does not replace a qualified lawyer.",
    }
