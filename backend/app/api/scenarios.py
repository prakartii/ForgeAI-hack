from typing import List
from fastapi import APIRouter
from app.schemas.scenario import Scenario

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])


@router.get("", response_model=List[Scenario])
def list_scenarios() -> List[Scenario]:
    """
    Returns available test scenarios. Empty in Phase 1; populated in Phase 2+.
    """
    return []
