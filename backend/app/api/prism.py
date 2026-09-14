from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.trace import AgentRunModel, TraceEventModel
from app.prism import get_prism_client

router = APIRouter(prefix="/prism", tags=["PRISM"])


@router.get("/status", response_model=Dict[str, Any])
def prism_status() -> Dict[str, Any]:
    """
    Returns the real integration status of the PRISM SDK connection.
    Does not fake PRISM evidence or leak secrets.
    """
    return get_prism_client().status()


@router.post("/runs/{run_id}/submit", response_model=Dict[str, Any])
def submit_run_to_prism(run_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Submits one AgentRun's trace events to PRISM as a trajectory. Returns
    "not_configured" (never a fabricated trajectory id) when PRISM
    credentials are absent, per CLAUDE.md sec21/sec31.
    """
    run = db.query(AgentRunModel).filter_by(run_id=run_id).one_or_none()
    if run is None:
        raise HTTPException(status_code=404, detail=f"run {run_id} not found")

    client = get_prism_client()
    if not client.is_configured:
        return {"status": "not_configured", "prism_session_id": None}

    events = db.query(TraceEventModel).filter_by(run_id=run_id).order_by(TraceEventModel.id.asc()).all()
    trajectory_id = client.submit_agent_run(run, events)
    if trajectory_id:
        run.prism_session_id = trajectory_id
        db.commit()
        return {"status": "submitted", "prism_session_id": trajectory_id}
    return {"status": "submission_failed", "prism_session_id": None}


@router.get("/runs/{run_id}/evidence", response_model=Dict[str, Any])
def get_run_prism_evidence(run_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Fetches PRISM's own evaluation for a run already submitted to PRISM.
    Returns "unavailable" (never a placeholder score) when there is no
    prism_session_id on the run or PRISM is not configured.
    """
    run = db.query(AgentRunModel).filter_by(run_id=run_id).one_or_none()
    if run is None:
        raise HTTPException(status_code=404, detail=f"run {run_id} not found")

    client = get_prism_client()
    if not client.is_configured or not run.prism_session_id:
        return {"status": "unavailable", "evaluation": None}

    evaluation = client.fetch_evaluation(run.prism_session_id)
    if evaluation is None:
        return {"status": "unavailable", "evaluation": None}
    return {"status": "available", "evaluation": evaluation}
