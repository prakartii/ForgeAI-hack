from typing import List
from fastapi import APIRouter
from app.schemas.evaluation import EvaluationResult

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get("", response_model=List[EvaluationResult])
def list_metrics() -> List[EvaluationResult]:
    """
    Returns computed evaluation metrics.
    In Phase 1, returns empty list.
    No hardcoded or fabricated metrics per CLAUDE.md §22.
    """
    return []
