from typing import List
from fastapi import APIRouter
from app.schemas.evaluation import RegressionTest

router = APIRouter(prefix="/regressions", tags=["Regressions"])


@router.get("", response_model=List[RegressionTest])
def list_regressions() -> List[RegressionTest]:
    """
    Returns registered permanent regression tests. Empty in Phase 1; populated in Phase 10+.
    """
    return []
