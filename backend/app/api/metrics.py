from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.enforcement.engine import resolve_enforcement
from app.metrics.engine import compute_metrics
from app.models.evaluation import EvaluationResultModel
from app.schemas.evaluation import EvaluationResult
from app.traces.wrapper import new_id

router = APIRouter(prefix="/metrics", tags=["Metrics"])

_NUMERIC_METRICS = [
    "task_correctness",
    "pairwise_consistency",
    "workflow_compliance",
    "evidence_completeness",
    "regression_pass_rate",
    "challenge_robustness",
]


@router.get("", response_model=List[EvaluationResult])
def list_metrics(db: Session = Depends(get_db)) -> List[EvaluationResultModel]:
    return db.query(EvaluationResultModel).order_by(EvaluationResultModel.id.desc()).limit(100).all()


@router.post("/compute", response_model=Dict[str, Any])
def compute_and_persist_metrics(
    candidate_version: str = "v2",
    enforced: bool = True,
    sample_size: Optional[int] = None,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Computes every CLAUDE.md §22 metric from real agent executions
    (optionally sampling `sample_size` claims to bound request latency)
    and persists each numeric metric as an EvaluationResult row.
    """
    from app.models.domain import ClaimModel

    claim_ids = None
    if sample_size:
        claim_ids = [row[0] for row in db.query(ClaimModel.claim_id).limit(sample_size).all()]

    prohibited_fields = None
    workflow_enforce = None
    if enforced:
        enforcement = resolve_enforcement(db)
        prohibited_fields = enforcement["prohibited_fields"]
        workflow_enforce = enforcement["workflow_enforce"]

    metrics = compute_metrics(
        db,
        candidate_version=candidate_version,
        prohibited_fields=prohibited_fields,
        workflow_enforce=workflow_enforce,
        claim_ids=claim_ids,
    )

    for name in _NUMERIC_METRICS:
        value = metrics.get(name)
        if value is None:
            continue
        db.add(
            EvaluationResultModel(
                evaluation_id=new_id("eval"),
                run_id=None,
                agent_version=candidate_version,
                metric_name=name,
                metric_value=value,
                passed=value >= 1.0 if name != "task_correctness" else value >= 0.95,
                prism_evaluator_name=None,
                details={"sample_size": metrics.get("sample_size")},
            )
        )
    db.commit()

    return metrics
