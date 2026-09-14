from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.enforcement.engine import resolve_enforcement
from app.gates.engine import evaluate_release_gate
from app.metrics.engine import compute_metrics
from app.models.evaluation import ReleaseGateResultModel
from app.schemas.evaluation import ReleaseGateResult

router = APIRouter(prefix="/gates", tags=["Release Gate"])


@router.get("", response_model=List[ReleaseGateResult])
def list_gate_results(db: Session = Depends(get_db)) -> List[ReleaseGateResultModel]:
    return db.query(ReleaseGateResultModel).order_by(ReleaseGateResultModel.id.desc()).limit(50).all()


@router.post("/run", response_model=ReleaseGateResult)
def run_release_gate(candidate_version: str = "v2", db: Session = Depends(get_db)) -> ReleaseGateResultModel:
    """
    Computes fresh metrics under the candidate version's real enforcement
    configuration and evaluates the CLAUDE.md §23 release gate against
    them. Every PASS/BLOCKED here traces back to a real, just-computed
    number, never an assumed one.
    """
    enforcement = resolve_enforcement(db)
    metrics = compute_metrics(
        db,
        candidate_version=candidate_version,
        prohibited_fields=enforcement["prohibited_fields"],
        workflow_enforce=enforcement["workflow_enforce"],
    )
    return evaluate_release_gate(db, candidate_version=candidate_version, metrics=metrics)
