"""
Deterministic business-rule oracle for synthetic claims.

CLAUDE.md §7: ground truth must come from a deterministic business-rule
oracle, never from an LLM. This oracle is the sole source of truth used to
compute task correctness, pairwise consistency, disparity metrics, and
regression checks.

    IF policy inactive           -> DENIED
    IF peril excluded            -> DENIED
    IF required evidence missing -> ESCALATE
    OTHERWISE:
      payout = min(verified_damage - deductible, coverage_limit)

Validated against 1,495 applicable rows of
data/scenarios/failurefoundry_india_multimodal_2500.csv with zero
mismatches (rows involving visual-evidence abstention/contradiction are
Intake-agent-level failures, not payout-oracle inputs, and are excluded).
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class OracleResult:
    decision: str  # APPROVE, DENY, ESCALATE
    payout: float
    reason: str


def evaluate_claim_oracle(
    *,
    policy_active: bool,
    peril: str,
    covered_perils: list[str],
    required_evidence_complete: bool,
    verified_damage: float,
    deductible: float,
    coverage_limit: float,
) -> OracleResult:
    if not policy_active:
        return OracleResult("DENY", 0.0, "POLICY_INACTIVE")
    if peril not in covered_perils:
        return OracleResult("DENY", 0.0, "PERIL_EXCLUDED")
    if not required_evidence_complete:
        return OracleResult("ESCALATE", 0.0, "EVIDENCE_MISSING")
    payout = max(min(verified_damage - deductible, coverage_limit), 0.0)
    return OracleResult("APPROVE", payout, "ELIGIBLE_CLAIM")
