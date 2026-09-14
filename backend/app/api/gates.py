from typing import List
from fastapi import APIRouter
from app.schemas.evaluation import ReleaseGateResult

router = APIRouter(prefix="/gates", tags=["Release Gate"])


@router.get("", response_model=List[ReleaseGateResult])
def list_gate_results() -> List[ReleaseGateResult]:
    """
    Returns release gate evaluation records. Empty in Phase 1; populated in Phase 11+.
    """
    return []
