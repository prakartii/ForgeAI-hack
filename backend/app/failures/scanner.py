"""
Failure scanner (CLAUDE.md §11): runs the real agent pipeline against the
loaded scenario set and feeds actual outputs into the detectors in
app.failures.detectors. This is what turns Phase 2's scenario data and
Phase 3's agents into concrete, persisted Failure rows.

Every failure is stamped with the `run_id` of the AgentRun that produced
it, so PRISM evidence submitted for that run (CLAUDE.md §9's trace
correlation model) can be found later by following failure.run_id ->
AgentRun.prism_session_id, rather than leaving that link unresolvable.
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
from app.models.trace import AgentRunModel
from app.traces.wrapper import TraceRecorder


def _claim_and_policy(db: Session, claim_id: str) -> tuple[ClaimModel, PolicyModel]:
    claim = db.query(ClaimModel).filter_by(claim_id=claim_id).one()
    policy = db.query(PolicyModel).filter_by(policy_id=claim.policy_id).one()
    return claim, policy


def _run_traced_adjudication(
    db: Session,
    claim: ClaimModel,
    policy: PolicyModel,
    *,
    agent_version: str,
    prohibited_fields: Optional[list[str]],
    scenario_id: Optional[str],
    counterfactual_group: Optional[str],
) -> tuple[dict, str]:
    """Runs Adjudication through a TraceRecorder so the scan leaves a real, submittable AgentRun."""
    with TraceRecorder(
        db,
        claim_id=claim.claim_id,
        agent_name="adjudication",
        agent_version=agent_version,
        scenario_id=scenario_id,
        counterfactual_group=counterfactual_group,
    ) as tr:
        result = run_adjudication(claim, policy, prohibited_fields=prohibited_fields)
        tr.record_event(
            input_payload={"context_keys": sorted(result["context_used"].keys())},
            output_payload={k: v for k, v in result.items() if k != "context_used"},
        )
    return result, tr.run_id


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
        run_ids = {}
        for claim_id in claim_ids:
            claim, policy = _claim_and_policy(db, claim_id)
            result, run_id = _run_traced_adjudication(
                db, claim, policy, agent_version=agent_version, prohibited_fields=prohibited_fields,
                scenario_id=claim_id, counterfactual_group=group_id,
            )
            outcomes[claim_id] = (result["decision"], result["payout"])
            run_ids[claim_id] = run_id
        # Attribute the failure to the baseline variant's run -- the group as a
        # whole is the unit of failure, but PRISM evidence is per-run.
        baseline_run_id = run_ids[pairs[0].baseline_claim_id]
        failure = detect_fairness_failure(db, group_id, outcomes, agent_version=agent_version, run_id=baseline_run_id)
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

        def _latest_run_id(agent_name: str) -> Optional[str]:
            run = (
                db.query(AgentRunModel)
                .filter_by(claim_id=claim_id, agent_name=agent_name)
                .order_by(AgentRunModel.id.desc())
                .first()
            )
            return run.run_id if run else None

        workflow_failure = detect_workflow_failure(
            db, claim_id, result, agent_version=agent_version, run_id=_latest_run_id("adjudication")
        )
        if workflow_failure:
            found["WORKFLOW"].append(workflow_failure)

        evidence_failure = detect_evidence_failure(
            db, claim_id, result.get("explainability"), agent_version=agent_version,
            run_id=_latest_run_id("explainability"),
        )
        if evidence_failure:
            found["EVIDENCE"].append(evidence_failure)

        decision_failure = detect_decision_correctness_failure(
            db, claim_id, result["adjudication"], agent_version=agent_version,
            run_id=_latest_run_id("adjudication"),
        )
        if decision_failure:
            found["DECISION_CORRECTNESS"].append(decision_failure)

    return found
