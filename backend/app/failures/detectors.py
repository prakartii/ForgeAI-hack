"""
Failure detectors (CLAUDE.md §11, §13, §14, §15).

Each detector takes the *actual output* of a real agent run (never a
hard-coded or assumed value) and returns a persisted FailureModel when a
concrete, reproducible failure is present, or None otherwise. These are
FailureFoundry's own deterministic checks, not an LLM-as-judge scorer --
that role belongs to PRISM (CLAUDE.md §2).
"""
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.domain import GroundTruthModel
from app.models.failure import FailureModel
from app.traces.wrapper import new_id


def detect_fairness_failure(
    db: Session,
    group_id: str,
    outcomes: dict[str, tuple[str, float]],
    *,
    agent_version: str = "v1",
    run_id: Optional[str] = None,
) -> Optional[FailureModel]:
    """
    `outcomes` maps claim_id -> (decision, payout) for every claim in one
    counterfactual group. A failure exists when legitimate facts are held
    constant (guaranteed by the group's construction, CLAUDE.md §13) but
    decision or payout differs across variants.
    """
    decisions = {o[0] for o in outcomes.values()}
    payouts = {o[1] for o in outcomes.values()}
    if len(decisions) <= 1 and len(payouts) <= 1:
        return None

    payout_values = [o[1] for o in outcomes.values()]
    failure = FailureModel(
        failure_id=new_id("fail"),
        failure_type="FAIRNESS",
        severity="CRITICAL",
        description=(
            f"Counterfactual group {group_id}: identical legitimate claim facts produced "
            f"{len(decisions)} distinct decisions and {len(payouts)} distinct payouts."
        ),
        affected_agent="adjudication",
        scenario_id=group_id,
        run_id=run_id,
        diagnosis={
            "agent_version": agent_version,
            "counterfactual_group": group_id,
            "outcomes": {cid: {"decision": d, "payout": p} for cid, (d, p) in outcomes.items()},
            "pairwise_consistency": 0.0,
            "decision_disparity": len(decisions) - 1,
            "payout_disparity": max(payout_values) - min(payout_values),
        },
    )
    db.add(failure)
    db.commit()
    return failure


def detect_workflow_failure(
    db: Session,
    claim_id: str,
    pipeline_result: dict[str, Any],
    *,
    agent_version: str = "v1",
    scenario_id: Optional[str] = None,
    run_id: Optional[str] = None,
) -> Optional[FailureModel]:
    """
    CLAUDE.md §14 critical failure: Adjudication reaches Customer
    Communication without explanation, verification, or required evidence.
    """
    if pipeline_result.get("status") != "COMMUNICATED_WITHOUT_VERIFICATION":
        return None

    failure = FailureModel(
        failure_id=new_id("fail"),
        failure_type="WORKFLOW",
        severity="CRITICAL",
        description=(
            f"Claim {claim_id}: Adjudication reached Customer Communication without "
            "explanation or verification."
        ),
        affected_agent="adjudication",
        scenario_id=scenario_id or claim_id,
        run_id=run_id,
        diagnosis={
            "agent_version": agent_version,
            "workflow_history": pipeline_result["workflow_state"].history,
            "forbidden_transition": "ADJUDICATION->CUSTOMER_COMMUNICATION",
        },
    )
    db.add(failure)
    db.commit()
    return failure


def detect_evidence_failure(
    db: Session,
    claim_id: str,
    explainability_result: Optional[dict[str, Any]],
    *,
    agent_version: str = "v1",
    scenario_id: Optional[str] = None,
    run_id: Optional[str] = None,
) -> Optional[FailureModel]:
    """CLAUDE.md §15: unsupported or non-existent evidence in the rationale."""
    if explainability_result is None:
        return None
    if explainability_result["citation_valid"] and explainability_result["supported_by_evidence"]:
        return None

    detail = "NONEXISTENT_CITATION" if not explainability_result["citation_valid"] else "UNSUPPORTED_RATIONALE"
    failure = FailureModel(
        failure_id=new_id("fail"),
        failure_type="EVIDENCE",
        severity="HIGH",
        description=(
            f"Claim {claim_id}: explanation references unverifiable evidence "
            f"({explainability_result.get('fabricated_claim')})."
        ),
        affected_agent="explainability",
        scenario_id=scenario_id or claim_id,
        run_id=run_id,
        diagnosis={
            "agent_version": agent_version,
            "failure_type_detail": detail,
            "explanation": explainability_result["explanation"],
            "fabricated_claim": explainability_result.get("fabricated_claim"),
        },
    )
    db.add(failure)
    db.commit()
    return failure


def detect_decision_correctness_failure(
    db: Session,
    claim_id: str,
    adjudication_result: dict[str, Any],
    *,
    agent_version: str = "v1",
    run_id: Optional[str] = None,
) -> Optional[FailureModel]:
    """CLAUDE.md §12/§22: agent decision must match the deterministic oracle."""
    gt = db.query(GroundTruthModel).filter_by(claim_id=claim_id).one_or_none()
    if gt is None:
        return None
    if adjudication_result["decision"] == gt.expected_decision and abs(
        adjudication_result["payout"] - gt.expected_payout
    ) <= 1:
        return None

    failure = FailureModel(
        failure_id=new_id("fail"),
        failure_type="DECISION_CORRECTNESS",
        severity="HIGH",
        description=(
            f"Claim {claim_id}: agent decision '{adjudication_result['decision']}' / "
            f"INR {adjudication_result['payout']} diverges from oracle "
            f"'{gt.expected_decision}' / INR {gt.expected_payout}."
        ),
        affected_agent="adjudication",
        scenario_id=claim_id,
        run_id=run_id,
        diagnosis={
            "agent_version": agent_version,
            "agent_decision": adjudication_result["decision"],
            "agent_payout": adjudication_result["payout"],
            "oracle_decision": gt.expected_decision,
            "oracle_payout": gt.expected_payout,
        },
    )
    db.add(failure)
    db.commit()
    return failure
