"""
Regression Engine (CLAUDE.md §19). Every discovered failure becomes a
permanent regression scenario that a candidate version must keep passing
-- a previously fixed failure must never silently disappear from the
suite.
"""
from typing import Optional

from sqlalchemy.orm import Session

from app.agents.orchestrator import run_claim_pipeline
from app.agents.adjudication import run_adjudication
from app.models.domain import ClaimModel, GroundTruthModel, PolicyModel
from app.models.evaluation import RegressionTestModel
from app.models.failure import FailureModel
from app.models.scenario import CounterfactualPairModel
from app.traces.wrapper import new_id


def _claim_and_policy(db: Session, claim_id: str) -> tuple[ClaimModel, PolicyModel]:
    claim = db.query(ClaimModel).filter_by(claim_id=claim_id).one()
    policy = db.query(PolicyModel).filter_by(policy_id=claim.policy_id).one()
    return claim, policy


def register_regression_test(
    db: Session,
    failure: FailureModel,
    *,
    abi_version_introduced: str,
) -> RegressionTestModel:
    """Idempotent: one regression test per (failure_type, scenario_id)."""
    same_type = db.query(RegressionTestModel).filter_by(failure_type=failure.failure_type).all()
    for existing in same_type:
        if existing.input_data.get("scenario_id") == failure.scenario_id:
            return existing

    test = RegressionTestModel(
        test_id=new_id("reg"),
        failure_type=failure.failure_type,
        input_data={"scenario_id": failure.scenario_id, "source_failure_id": failure.failure_id},
        expected_behavior=failure.description,
        abi_version_introduced=abi_version_introduced,
        still_passing=False,  # true only once a candidate version actually passes it
        last_tested_version=None,
    )
    db.add(test)
    db.commit()
    return test


def run_regression_suite(
    db: Session,
    *,
    candidate_version: str,
    prohibited_fields: Optional[list[str]] = None,
    workflow_enforce: Optional[bool] = None,
) -> list[RegressionTestModel]:
    tests = db.query(RegressionTestModel).all()

    for test in tests:
        scenario_id = test.input_data.get("scenario_id")
        if not scenario_id:
            continue

        if test.failure_type == "FAIRNESS":
            pairs = db.query(CounterfactualPairModel).filter_by(group_id=scenario_id).all()
            if not pairs:
                continue
            claim_ids = {pairs[0].baseline_claim_id} | {p.counterfactual_claim_id for p in pairs}
            outcomes = set()
            for claim_id in claim_ids:
                claim, policy = _claim_and_policy(db, claim_id)
                result = run_adjudication(claim, policy, prohibited_fields=prohibited_fields)
                outcomes.add((result["decision"], result["payout"]))
            test.still_passing = len(outcomes) == 1
        else:
            claim, policy = _claim_and_policy(db, scenario_id)
            pipeline_result = run_claim_pipeline(
                db,
                claim,
                policy,
                agent_version=candidate_version,
                prohibited_fields=prohibited_fields,
                workflow_enforce=workflow_enforce,
                scenario_id=scenario_id,
            )
            if test.failure_type == "WORKFLOW":
                test.still_passing = pipeline_result["status"] != "COMMUNICATED_WITHOUT_VERIFICATION"
            elif test.failure_type == "EVIDENCE":
                explainability = pipeline_result.get("explainability")
                test.still_passing = pipeline_result["status"] != "COMPLETED" or (
                    explainability is not None
                    and explainability["citation_valid"]
                    and explainability["supported_by_evidence"]
                ) or pipeline_result["status"] == "BLOCKED_CUSTOMER_COMMUNICATION"
            elif test.failure_type == "DECISION_CORRECTNESS":
                gt = db.query(GroundTruthModel).filter_by(claim_id=scenario_id).one_or_none()
                if gt is not None:
                    adjudication = pipeline_result["adjudication"]
                    test.still_passing = (
                        adjudication["decision"] == gt.expected_decision
                        and abs(adjudication["payout"] - gt.expected_payout) <= 1
                    )

        test.last_tested_version = candidate_version

        # A regression test's source Failure is "resolved" exactly when the
        # regression suite just confirmed the candidate version no longer
        # reproduces it -- and un-resolved again if a later run regresses,
        # so the release gate's critical-violation count always reflects
        # current, not stale, state.
        source_failure_id = test.input_data.get("source_failure_id")
        if source_failure_id:
            failure = db.query(FailureModel).filter_by(failure_id=source_failure_id).one_or_none()
            if failure is not None:
                failure.resolved = test.still_passing

    db.commit()
    return tests
