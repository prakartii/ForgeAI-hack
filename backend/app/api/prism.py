from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.trace import AgentRunModel, TraceEventModel
from app.prism import get_prism_client

router = APIRouter(prefix="/prism", tags=["PRISM"])

ABIS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "abis"


@router.get("/status", response_model=Dict[str, Any])
def prism_status() -> Dict[str, Any]:
    """
    Returns the real integration status of the PRISM SDK connection.
    Does not fake PRISM evidence or leak secrets.
    """
    return get_prism_client().status()


@router.get("/verdict", response_model=Dict[str, Any])
def prism_verdict() -> Dict[str, Any]:
    """
    PRISM's own aggregated governance verdict across our submitted
    trajectories (real overall_score / critical_rule_failed, not our
    scoring) -- the same figures the Release Gate's prism_evidence clause
    now actually consumes, exposed standalone so the dashboard can show
    it without waiting on a full metrics computation.
    """
    return get_prism_client().get_verdict()


@router.post("/kb/seed", response_model=Dict[str, Any])
def seed_prism_knowledge_base() -> Dict[str, Any]:
    """
    Uploads the compiled Behavior ABI specs (abis/*.yaml) into PRISM's
    Knowledge Base, idempotently. The Explainability Agent's kb_search
    grounding (CLAUDE.md §16) only has something real to retrieve once
    this has been run -- call it once per environment, not per request.
    """
    # PRISM's Knowledge Base only accepts .txt/.md/.pdf (verified: a .yaml
    # upload returns 400 "Only .txt, .md, .pdf supported.") -- same YAML
    # content, uploaded under a .txt name instead of being rejected outright.
    abi_texts = {f"{p.stem}_abi.txt": p.read_text() for p in sorted(ABIS_DIR.glob("*.yaml"))}
    if not abi_texts:
        return {"status": "no_abi_files_found", "uploaded": [], "already_present": []}
    return get_prism_client().ensure_abi_kb_seeded(abi_texts)


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


@router.post("/runs/{run_id}/reevaluate", response_model=Dict[str, Any])
def reevaluate_run_in_prism(run_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Forces PRISM to re-run its evaluator for an already-submitted run,
    live -- not served from cache. Requires the run to already carry a
    prism_session_id (submit it first). Returns "unavailable" rather than
    a stale/fabricated result when PRISM isn't configured or the run was
    never submitted.
    """
    run = db.query(AgentRunModel).filter_by(run_id=run_id).one_or_none()
    if run is None:
        raise HTTPException(status_code=404, detail=f"run {run_id} not found")

    client = get_prism_client()
    if not client.is_configured or not run.prism_session_id:
        return {"status": "unavailable", "evaluation": None}

    evaluation = client.retrigger_evaluation(run.prism_session_id)
    if evaluation is None:
        return {"status": "unavailable", "evaluation": None}
    return {"status": "reevaluated", "evaluation": evaluation}
