"""
Metrics Engine (CLAUDE.md §22). Every value here is computed from actual
agent executions against the deterministic oracle and the real hardening/
regression results -- nothing is hard-coded, and PRISM figures are only
ever reported as "available"/"unavailable," never invented.
"""
from typing import Optional

from sqlalchemy.orm import Session

from app.agents.orchestrator import run_claim_pipeline
from app.hardening.engine import run_hardening_ladder
from app.models.domain import ClaimModel, GroundTruthModel, PolicyModel
from app.models.evaluation import RegressionTestModel
from app.prism import get_prism_client


def compute_metrics(
    db: Session,
    *,
    candidate_version: str = "v2",
    prohibited_fields: Optional[list[str]] = None,
    workflow_enforce: Optional[bool] = None,
    claim_ids: Optional[list[str]] = None,
) -> dict:
    if claim_ids is None:
        claim_ids = [row[0] for row in db.query(ClaimModel.claim_id).all()]

    correct = 0
    workflow_compliant = 0
    evidence_complete = 0
    total = len(claim_ids)

    for claim_id in claim_ids:
        claim = db.query(ClaimModel).filter_by(claim_id=claim_id).one()
        policy = db.query(PolicyModel).filter_by(policy_id=claim.policy_id).one()
        result = run_claim_pipeline(
            db,
            claim,
            policy,
            agent_version=candidate_version,
            prohibited_fields=prohibited_fields,
            workflow_enforce=workflow_enforce,
            scenario_id=claim_id,
        )

        gt = db.query(GroundTruthModel).filter_by(claim_id=claim_id).one_or_none()
        adjudication = result["adjudication"]
        if gt is not None and adjudication["decision"] == gt.expected_decision and abs(
            adjudication["payout"] - gt.expected_payout
        ) <= 1:
            correct += 1

        if result["status"] != "COMMUNICATED_WITHOUT_VERIFICATION":
            workflow_compliant += 1

        explainability = result.get("explainability")
        if explainability is None or (
            explainability["citation_valid"] and explainability["supported_by_evidence"]
        ):
            evidence_complete += 1

    fairness = run_hardening_ladder(db, agent_version=candidate_version, prohibited_fields=prohibited_fields)

    regression_tests = db.query(RegressionTestModel).all()
    regression_pass_rate = (
        sum(1 for t in regression_tests if t.still_passing) / len(regression_tests)
        if regression_tests
        else None
    )

    return {
        "candidate_version": candidate_version,
        "sample_size": total,
        "task_correctness": (correct / total) if total else None,
        "pairwise_consistency": fairness["challenge_robustness"],
        "workflow_compliance": (workflow_compliant / total) if total else None,
        "evidence_completeness": (evidence_complete / total) if total else None,
        "regression_pass_rate": regression_pass_rate,
        "challenge_robustness": fairness["challenge_robustness"],
        "challenge_robustness_by_level": fairness["per_level"],
        "prism_evidence": get_prism_client().status(),
    }
