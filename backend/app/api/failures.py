from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.enforcement.engine import resolve_enforcement
from app.failures.scanner import scan_claims, scan_fairness_groups
from app.models.domain import ClaimModel
from app.models.failure import FailureModel
from app.regression.engine import register_regression_test
from app.schemas.failure import Failure

router = APIRouter(prefix="/failures", tags=["Failures"])


@router.get("", response_model=List[Failure])
def list_failures(
    failure_type: Optional[str] = None,
    resolved: Optional[bool] = None,
    db: Session = Depends(get_db),
) -> List[FailureModel]:
    query = db.query(FailureModel)
    if failure_type:
        query = query.filter(FailureModel.failure_type == failure_type)
    if resolved is not None:
        query = query.filter(FailureModel.resolved == resolved)
    return query.order_by(FailureModel.id.desc()).limit(200).all()


@router.post("/scan", response_model=Dict[str, Any])
def scan_for_failures(
    agent_version: str = "v1",
    enforced: bool = False,
    claim_sample_size: int = 50,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Runs the real fairness scan across every counterfactual group plus a
    workflow/evidence/decision-correctness scan across a sample of claims,
    persisting whatever FailureModel rows the actual agent output earns.
    `enforced=true` resolves the currently compiled Behavior ABIs instead
    of running the given agent_version unprotected.
    """
    prohibited_fields = None
    workflow_enforce = None
    if enforced:
        enforcement = resolve_enforcement(db)
        prohibited_fields = enforcement["prohibited_fields"]
        workflow_enforce = enforcement["workflow_enforce"]

    fairness_failures = scan_fairness_groups(db, agent_version=agent_version, prohibited_fields=prohibited_fields)

    claim_ids = [row[0] for row in db.query(ClaimModel.claim_id).limit(claim_sample_size).all()]
    other_failures = scan_claims(
        db, claim_ids, agent_version=agent_version,
        prohibited_fields=prohibited_fields, workflow_enforce=workflow_enforce,
    )

    # CLAUDE.md §19: every discovered failure becomes a permanent regression
    # obligation immediately, not only once someone remembers to add one.
    abi_version = "fair_adjudication_v1" if fairness_failures else "fair_workflow_v1"
    for failure in fairness_failures:
        register_regression_test(db, failure, abi_version_introduced="fair_adjudication_v1")
    for failure in other_failures["WORKFLOW"]:
        register_regression_test(db, failure, abi_version_introduced="fair_workflow_v1")
    for failure in other_failures["EVIDENCE"] + other_failures["DECISION_CORRECTNESS"]:
        register_regression_test(db, failure, abi_version_introduced=abi_version)

    return {
        "fairness_failures": len(fairness_failures),
        "workflow_failures": len(other_failures["WORKFLOW"]),
        "evidence_failures": len(other_failures["EVIDENCE"]),
        "decision_correctness_failures": len(other_failures["DECISION_CORRECTNESS"]),
    }
