"""Load and cache emergency contacts from data file — never hardcoded."""
import json
import os
from functools import lru_cache
from app.orchestrator.context import EmergencyContact
from app.core.logging import get_logger

logger = get_logger(__name__)

_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "../../data/emergency_contacts.json"
)


@lru_cache(maxsize=1)
def _load_contacts() -> list[dict]:
    try:
        with open(_DATA_PATH) as f:
            data = json.load(f)
            return data.get("contacts", [])
    except FileNotFoundError:
        logger.warning("emergency_contacts_not_found", path=_DATA_PATH)
        return []
    except Exception as exc:
        logger.error("emergency_contacts_load_error", error=str(exc))
        return []


def get_emergency_resources(categories: list[str] | None = None) -> list[EmergencyContact]:
    """Return relevant emergency contacts based on risk categories."""
    contacts = _load_contacts()
    result = []
    for c in contacts:
        try:
            result.append(EmergencyContact(
                id=c.get("id", ""),
                name=c.get("name", ""),
                number=c.get("number", ""),
                type=c.get("type", ""),
                scope=c.get("scope", "national"),
                languages=c.get("languages", []),
                description=c.get("description", ""),
            ))
        except Exception:
            pass
    return result
