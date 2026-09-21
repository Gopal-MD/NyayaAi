"""Referrals router: POST /referrals"""
import json
import os
from fastapi import APIRouter, Depends
from app.core.auth import CurrentUser
from app.models.schemas import ReferralRequest, ReferralResponse, ProviderItem

router = APIRouter()

_PROVIDERS_PATH = os.path.join(os.path.dirname(__file__), "../../data/legal_aid/providers.json")


def _load_providers() -> list[dict]:
    try:
        with open(_PROVIDERS_PATH) as f:
            return json.load(f)
    except Exception:
        return []


@router.post("", response_model=ReferralResponse)
async def find_referrals(
    body: ReferralRequest,
    current_user: CurrentUser,
):
    providers = _load_providers()

    # Filter deterministically — no AI scoring
    filtered = providers
    if body.state:
        filtered = [p for p in filtered if not p.get("state") or p["state"].upper() == body.state.upper()]
    if body.district:
        filtered = [p for p in filtered if not p.get("district") or body.district.lower() in p["district"].lower()]
    if body.language:
        filtered = [p for p in filtered if not p.get("languages") or body.language in p.get("languages", [])]
    if body.domain:
        filtered = [p for p in filtered if not p.get("domains") or body.domain in p.get("domains", [])]

    # Sort alphabetically — deterministic, not AI
    filtered.sort(key=lambda p: p.get("name", ""))

    items = [
        ProviderItem(
            id=p.get("id", ""),
            name=p.get("name", ""),
            provider_type=p.get("type", ""),
            state=p.get("state"),
            phone=p.get("phone"),
            languages=p.get("languages", []),
            domains=p.get("domains", []),
            verified_at=p.get("verified_at"),
        )
        for p in filtered
    ]

    return ReferralResponse(providers=items, eligibility_applied=body.income_eligible is not None)
