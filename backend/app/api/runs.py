from typing import List
from fastapi import APIRouter
from app.schemas.trace import AgentRun

router = APIRouter(prefix="/runs", tags=["Runs"])


@router.get("", response_model=List[AgentRun])
def list_runs() -> List[AgentRun]:
    """
    Returns recorded agent runs. Empty in Phase 1; populated in Phase 3+.
    """
    return []
