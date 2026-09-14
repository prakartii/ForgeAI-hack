"""
Adjudication Agent (CLAUDE.md §6.2) -- the primary decision-maker.

Decision = deterministic oracle (policy/peril/evidence prechecks, then
min(verified_damage - deductible, coverage_limit)), matching CLAUDE.md §7's
requirement that ground truth come from a business-rule oracle, not an LLM.

CLAUDE.md §29's intentionally controlled v1 weakness lives entirely in
`build_adjudication_context`: by default it exposes proxy fields
(claimant name, PIN code, state, city, narrative style) to this agent's
context, and `_v1_proxy_bias` applies a small, deterministic, reproducible
penalty keyed on those fields -- standing in for a biased LLM without
requiring a real (and non-reproducible) LLM call. Passing `prohibited_fields`
(the fairness ABI's enforcement, CLAUDE.md §16.2) strips those keys from the
context before adjudication runs, which removes the bias function's own
inputs and restores oracle-identical, counterfactual-consistent decisions.
"""
from typing import Any, Optional

from app.models.domain import ClaimModel, PolicyModel
from app.scenarios.oracle import evaluate_claim_oracle

PROXY_FIELDS = ["claimant_name_synthetic", "synthetic_pin_code", "state", "city", "narrative_style"]
_BIASED_NARRATIVE_STYLES = {"INFORMAL", "HINGLISH"}


def build_adjudication_context(
    claim: ClaimModel,
    policy: PolicyModel,
    *,
    prohibited_fields: Optional[list[str]] = None,
) -> dict[str, Any]:
    context: dict[str, Any] = {
        "policy_status": "ACTIVE" if policy.is_active else "INACTIVE",
        "covered_perils": policy.covered_perils,
        "incident_peril": claim.peril,
        "verified_damage_inr": claim.verified_damage,
        "deductible_inr": policy.deductible,
        "coverage_limit_inr": policy.coverage_limit,
        "required_evidence_complete": bool(claim.details.get("required_evidence_complete", True)),
        **claim.proxy_variants,  # v1 weakness: proxy fields reach this context by default
    }
    for field in prohibited_fields or []:
        context.pop(field, None)
    return context


def _v1_proxy_bias(context: dict[str, Any]) -> float:
    """Deterministic, reproducible stand-in for a biased reasoning model."""
    bias = 0.0
    if context.get("narrative_style") in _BIASED_NARRATIVE_STYLES:
        bias -= 0.10
    pin = context.get("synthetic_pin_code")
    if pin and int(pin) % 2 == 1:
        bias -= 0.05
    return bias


def run_adjudication(
    claim: ClaimModel,
    policy: PolicyModel,
    *,
    prohibited_fields: Optional[list[str]] = None,
) -> dict[str, Any]:
    context = build_adjudication_context(claim, policy, prohibited_fields=prohibited_fields)

    oracle_result = evaluate_claim_oracle(
        policy_active=context["policy_status"] == "ACTIVE",
        peril=context["incident_peril"],
        covered_perils=context["covered_perils"],
        required_evidence_complete=context["required_evidence_complete"],
        verified_damage=context["verified_damage_inr"],
        deductible=context["deductible_inr"],
        coverage_limit=context["coverage_limit_inr"],
    )

    decision = oracle_result.decision
    payout = oracle_result.payout
    confidence = 0.9

    # Reachable only when proxy fields have NOT been stripped from context --
    # exactly the controlled v1 fairness weakness (CLAUDE.md §13, §29).
    if decision == "APPROVE" and "narrative_style" in context and "synthetic_pin_code" in context:
        bias = _v1_proxy_bias(context)
        if bias != 0.0:
            payout = round(payout * (1 + bias), 2)
            confidence = round(confidence + bias, 2)
            if payout < 0.5 * oracle_result.payout:
                decision = "ESCALATE"
                payout = 0.0

    return {
        "decision": decision,
        "payout": payout,
        "reason": oracle_result.reason,
        "confidence": confidence,
        "context_used": context,
    }
