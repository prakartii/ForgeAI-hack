from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.orchestrator import run_claim_pipeline
from app.db.session import get_db
from app.enforcement.engine import resolve_enforcement
from app.models.domain import ClaimModel, PolicyModel
from app.models.trace import AgentRunModel
from app.schemas.trace import AgentRun

router = APIRouter(prefix="/runs", tags=["Runs"])


@router.get("", response_model=List[AgentRun])
def list_runs(
    claim_id: Optional[str] = None,
    scenario_id: Optional[str] = None,
    db: Session = Depends(get_db),
) -> List[AgentRunModel]:
    query = db.query(AgentRunModel)
    if claim_id:
        query = query.filter(AgentRunModel.claim_id == claim_id)
    if scenario_id:
        query = query.filter(AgentRunModel.scenario_id == scenario_id)
    return query.order_by(AgentRunModel.id.desc()).limit(200).all()


@router.post("/execute", response_model=Dict[str, Any])
def execute_claim_pipeline(
    claim_id: str,
    agent_version: str = "v1",
    enforced: bool = False,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Runs the real Intake -> Adjudication -> Explainability -> Verification
    -> Customer Communication pipeline for one claim on demand, so the
    dashboard can trigger a live run rather than only display historical
    ones. `enforced=true` resolves whichever Behavior ABI is currently
    compiled and active instead of the version's raw v1/v2 default.
    """
    claim = db.query(ClaimModel).filter_by(claim_id=claim_id).one_or_none()
    if claim is None:
        raise HTTPException(status_code=404, detail=f"claim {claim_id} not found")
    policy = db.query(PolicyModel).filter_by(policy_id=claim.policy_id).one()

    prohibited_fields = None
    workflow_enforce = None
    abi_version = None
    if enforced:
        enforcement = resolve_enforcement(db)
        prohibited_fields = enforcement["prohibited_fields"]
        workflow_enforce = enforcement["workflow_enforce"]
        abi_version = enforcement["fairness_abi_version"]

    result = run_claim_pipeline(
        db, claim, policy, agent_version=agent_version,
        prohibited_fields=prohibited_fields, workflow_enforce=workflow_enforce,
        scenario_id=claim_id, abi_version=abi_version,
    )

    workflow_state = result.pop("workflow_state", None)
    if workflow_state is not None:
        result["workflow_state"] = {
            "current_step": workflow_state.current_step,
            "explanation_verified": workflow_state.explanation_verified,
            "customer_communication_allowed": workflow_state.customer_communication_allowed,
            "history": workflow_state.history,
        }
    return result
