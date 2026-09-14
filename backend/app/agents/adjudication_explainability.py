"""
Adjudication & Explainability Unified Agent (Combines CLAUDE.md §6.2 & §6.3).

Combines the decision-making adjudication step (determining APPROVE/DENY/ESCALATE,
payout, confidence, and internal rationale via business-rule oracle) with the
customer-facing explainability generation (attaching policy/evidence citations,
verifying citations, and detecting unbacked claims) into a single agent cycle.
"""
from typing import Any, Optional

from app.agents.adjudication import PROXY_FIELDS, build_adjudication_context, run_adjudication
from app.agents.explainability import run_explainability
from app.models.domain import ClaimModel, PolicyModel


def run_adjudication_and_explainability(
    claim: ClaimModel,
    policy: PolicyModel,
    *,
    prohibited_fields: Optional[list[str]] = None,
    inject_failure: bool = True,
    intake_action: Optional[str] = None,
) -> dict[str, Any]:
    """
    Unified agent that both adjudicates a claim and generates its customer-facing explanation.

    Returns a combined dictionary containing all adjudication attributes alongside
    the evidence-backed explanation and validation flags.
    """
    if intake_action is not None and intake_action not in ("STRUCTURE_CLAIM", "STRUCTURE_CLAIM_FROM_DOCUMENTS"):
        # Intake could not structure the claim (unresolved/missing visual evidence)
        context = build_adjudication_context(claim, policy, prohibited_fields=prohibited_fields)
        adjudication_result = {
            "decision": "ESCALATE",
            "payout": 0.0,
            "reason": intake_action,
            "confidence": 0.5,
            "context_used": context,
        }
    else:
        adjudication_result = run_adjudication(claim, policy, prohibited_fields=prohibited_fields)

    explainability_result = run_explainability(
        claim,
        adjudication_result,
        inject_failure=inject_failure,
    )

    return {
        # Adjudication fields
        "decision": adjudication_result["decision"],
        "payout": adjudication_result["payout"],
        "reason": adjudication_result["reason"],
        "confidence": adjudication_result["confidence"],
        "context_used": adjudication_result["context_used"],
        # Explainability fields
        "explanation": explainability_result["explanation"],
        "evidence_references": explainability_result["evidence_references"],
        "citation_valid": explainability_result["citation_valid"],
        "supported_by_evidence": explainability_result["supported_by_evidence"],
        "fabricated_claim": explainability_result.get("fabricated_claim"),
        # Nested references for compatibility
        "adjudication": adjudication_result,
        "explainability": explainability_result,
    }
