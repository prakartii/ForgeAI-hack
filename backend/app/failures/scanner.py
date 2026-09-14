"""
Failure scanner (CLAUDE.md §11): runs the real agent pipeline against the
loaded scenario set and feeds actual outputs into the detectors in
app.failures.detectors. This is what turns Phase 2's scenario data and
Phase 3's agents into concrete, persisted Failure rows.
"""
from typing import Optional

from sqlalchemy.orm import Session

from app.agents.adjudication import PROXY_FIELDS, run_adjudication
from app.agents.orchestrator import run_claim_pipeline
from app.failures.detectors import (
    detect_decision_correctness_failure,
    detect_evidence_failure,
    detect_fairness_failure,
    detect_workflow_failure,
)
from app.models.domain import ClaimModel, PolicyModel
from app.models.failure import FailureModel
from app.models.scenario import CounterfactualPairModel


def _claim_and_policy(db: Session, claim_id: str) -> tuple[ClaimModel, PolicyModel]:
    claim = db.query(ClaimModel).filter_by(claim_id=claim_id).one()
    policy = db.query(PolicyModel).filter_by(policy_id=claim.policy_id).one()
    return claim, policy


def scan_fairness_groups(
    db: Session,
    *,
    agent_version: str = "v1",
    prohibited_fields: Optional[list[str]] = None,
) -> list[FailureModel]:
    if prohibited_fields is None:
        prohibited_fields = [] if agent_version == "v1" else PROXY_FIELDS

    group_ids = {row[0] for row in db.query(CounterfactualPairModel.group_id).distinct().all()}
    failures = []
    for group_id in group_ids:
        pairs = db.query(CounterfactualPairModel).filter_by(group_id=group_id).all()
        claim_ids = {pairs[0].baseline_claim_id} | {p.counterfactual_claim_id for p in pairs}
        outcomes = {}
        for claim_id in claim_ids:
            claim, policy = _claim_and_policy(db, claim_id)
            result = run_adjudication(claim, policy, prohibited_fields=prohibited_fields)
            outcomes[claim_id] = (result["decision"], result["payout"])
        failure = detect_fairness_failure(db, group_id, outcomes, agent_version=agent_version)
        if failure:
            failures.append(failure)
    return failures


def scan_claims(
    db: Session,
    claim_ids: list[str],
    *,
    agent_version: str = "v1",
    prohibited_fields: Optional[list[str]] = None,
    workflow_enforce: Optional[bool] = None,
) -> dict[str, list[FailureModel]]:
    """
    Runs the full claim pipeline for each given claim id and applies the
    workflow, evidence, and decision-correctness detectors to its real
    output. Returns failures grouped by detector type for reporting.
    """
    found: dict[str, list[FailureModel]] = {"WORKFLOW": [], "EVIDENCE": [], "DECISION_CORRECTNESS": []}

    for claim_id in claim_ids:
        claim, policy = _claim_and_policy(db, claim_id)
        result = run_claim_pipeline(
            db, claim, policy, agent_version=agent_version, scenario_id=claim_id,
            prohibited_fields=prohibited_fields, workflow_enforce=workflow_enforce,
        )

        workflow_failure = detect_workflow_failure(db, claim_id, result, agent_version=agent_version)
        if workflow_failure:
            found["WORKFLOW"].append(workflow_failure)

        evidence_failure = detect_evidence_failure(
            db, claim_id, result.get("explainability"), agent_version=agent_version
        )
        if evidence_failure:
            found["EVIDENCE"].append(evidence_failure)

        decision_failure = detect_decision_correctness_failure(
            db, claim_id, result["adjudication"], agent_version=agent_version
        )
        if decision_failure:
            found["DECISION_CORRECTNESS"].append(decision_failure)

    return found
