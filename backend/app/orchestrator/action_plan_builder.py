"""Action plan builder — assembles ActionPlanSections from pipeline context or analysis data."""
from app.orchestrator.context import PipelineContext
from app.models.schemas import ActionPlanSections

_LIMITATION = (
    "NyayaAi provides legal information to help you understand and prepare. "
    "It is not legal advice and does not replace a qualified lawyer."
)


def build_action_plan(
    facts: dict,
    deadlines: list,
    clauses: list,
    questions: list,
    case,
) -> ActionPlanSections:
    """Build an ActionPlanSections from document analysis data."""

    # What I understood
    parts = []
    if facts.get("landlord_name"):
        parts.append(f"Landlord: {facts['landlord_name']}")
    if facts.get("tenant_names"):
        parts.append(f"Tenant(s): {', '.join(facts['tenant_names'])}")
    if facts.get("property_address"):
        parts.append(f"Property: {facts['property_address']}")
    if facts.get("monthly_rent"):
        parts.append(f"Monthly rent: ₹{facts['monthly_rent']}")
    if facts.get("security_deposit"):
        parts.append(f"Security deposit: ₹{facts['security_deposit']}")
    if facts.get("lease_start") and facts.get("lease_end"):
        parts.append(f"Lease period: {facts['lease_start']} to {facts['lease_end']}")
    what_understood = "; ".join(parts) if parts else "Rental agreement details extracted from your document."

    # Flagged clauses → what to do next
    red_yellow = [c for c in clauses if c.get("risk_level") in ("red", "yellow")]
    next_steps = []
    if red_yellow:
        next_steps.append("Review the flagged clauses in your agreement with a lawyer before signing.")
    if facts.get("notice_period_landlord_days") != facts.get("notice_period_tenant_days"):
        next_steps.append("Ask your landlord about the asymmetric notice period.")
    if not facts.get("dispute_resolution_clause"):
        next_steps.append("Ask the landlord to add a dispute resolution clause.")
    if not next_steps:
        next_steps.append("Review the agreement carefully before signing.")
    next_steps.append("Keep a signed copy of the agreement after execution.")

    # Documents
    documents = [
        "Signed copy of the rental agreement",
        "Identity proof (Aadhaar / Passport)",
        "Rent receipts after each payment",
    ]
    if facts.get("security_deposit"):
        documents.append("Receipt for security deposit payment")

    # Important dates with sources
    important_dates = []
    for d in deadlines:
        important_dates.append({
            "label": d.get("label", ""),
            "date": d.get("due_date", ""),
            "source": d.get("source_ref", "Document"),
        })

    # Official resources
    official_resources = [
        {
            "name": "NALSA Legal Services Helpline",
            "description": "Free legal aid — call for eligibility",
            "number": "TODO_VERIFY",
        },
        {
            "name": "Tamil Nadu DLSA",
            "description": "District Legal Services Authority — free legal services",
            "number": "TODO_VERIFY",
        },
    ]

    # When to seek a lawyer
    when_lawyer = "If you are unsure about any clause, if the landlord refuses to register the agreement, or if a dispute arises."
    if red_yellow:
        when_lawyer = f"As soon as possible — {len(red_yellow)} clause(s) in your agreement may be unusual or one-sided."

    return ActionPlanSections(
        what_i_understood=what_understood,
        possible_legal_area="Residential tenancy — Tamil Nadu and central tenancy law",
        what_you_can_do_next=next_steps,
        documents_you_may_need=documents,
        important_dates=important_dates,
        official_resources=official_resources,
        when_to_seek_a_lawyer=when_lawyer,
        important_limitation=_LIMITATION,
    )


def build_action_plan_from_context(ctx: PipelineContext) -> PipelineContext:
    """Attach a simple action plan dict to the context (does not replace final_answer)."""
    ctx.action_plan = {
        "jurisdiction": ctx.jurisdiction,
        "domain": ctx.domain,
        "limitation": _LIMITATION,
    }
    return ctx
