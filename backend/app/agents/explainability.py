"""
Explainability Agent (CLAUDE.md §6.3).

Generates an evidence-backed, customer-facing explanation consistent with
the adjudication decision. Only ever cites factors present in the
Adjudication Agent's own context (permitted factors once the fairness ABI
is enforced) -- it never invents policy clauses or evidence.

`inject_failure` deterministically reproduces the exact evidence failures
labeled in the demo dataset (NONEXISTENT_CITATION, UNSUPPORTED_POLICY_CLAUSE,
RATIONALE_DECISION_CONTRADICTION -- CLAUDE.md §15) so the enforcement and
failure-detection layers have real, reproducible cases to catch, rather
than a hypothetical one. It is independent of agent version: catching
these is the Enforcement Layer's job (§16.2), not something this agent
hides.
"""
from typing import Any, Optional

from app.agents.adjudication import PROXY_FIELDS
from app.models.domain import ClaimModel


def run_explainability(
    claim: ClaimModel,
    adjudication_result: dict[str, Any],
    *,
    inject_failure: bool = True,
    use_prism_kb: bool = False,
) -> dict[str, Any]:
    context = adjudication_result["context_used"]
    decision = adjudication_result["decision"]
    reason = adjudication_result["reason"]
    permitted_citations = [k for k in context.keys() if k not in PROXY_FIELDS]

    explanation = (
        f"Claim {claim.claim_id} was {decision} based on {reason.replace('_', ' ').lower()}. "
        f"Policy status: {context.get('policy_status')}, covered peril: {context.get('incident_peril')}, "
        f"verified damage: INR {context.get('verified_damage_inr')}, payout: INR {adjudication_result['payout']}."
    )
    citation_valid = True
    supported_by_evidence = True
    fabricated_claim = None

    failure_mode = claim.details.get("failure_injected") if inject_failure else None
    if failure_mode == "NONEXISTENT_CITATION":
        fabricated_claim = "policy clause 47 (flood waiver)"
        explanation += f" This is further supported by {fabricated_claim}."
        citation_valid = False
    elif failure_mode == "UNSUPPORTED_POLICY_CLAUSE":
        fabricated_claim = "a no-deductible loyalty waiver"
        explanation += f" {fabricated_claim.capitalize()} was also applied to this payout."
        supported_by_evidence = False
    elif failure_mode == "RATIONALE_DECISION_CONTRADICTION":
        contradiction_decision = "DENY" if decision != "DENY" else "APPROVE"
        explanation += f" Note: underwriting guidance indicates this claim should be {contradiction_decision}."
        supported_by_evidence = False

    return {
        "explanation": explanation,
        "evidence_references": permitted_citations,
        "citation_valid": citation_valid,
        "supported_by_evidence": supported_by_evidence,
        "fabricated_claim": fabricated_claim,
        "prism_kb_grounding": _prism_kb_grounding(decision, reason) if use_prism_kb else None,
    }


def _prism_kb_grounding(decision: str, reason: str) -> Optional[list[dict[str, Any]]]:
    """Real retrieval against PRISM's Knowledge Base (run POST
    /api/prism/kb/seed once first so there's something to retrieve) --
    grounds the explanation in the actual compiled ABI text PRISM holds,
    rather than only internal context keys. None (not an empty list, not
    invented content) when PRISM isn't configured or nothing was seeded;
    CLAUDE.md §31 forbids treating that as "no grounding needed" and
    faking a citation instead."""
    from app.prism import get_prism_client

    client = get_prism_client()
    if not client.is_configured:
        return None
    try:
        results = client.kb_search(f"{decision} {reason.replace('_', ' ').lower()}", limit=2)
    except Exception:
        return None
    return [
        {"document": r.get("doc_name"), "excerpt": (r.get("content") or "")[:400], "relevance_score": r.get("relevance_score")}
        for r in results
    ] or None
