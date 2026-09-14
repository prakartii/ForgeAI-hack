from typing import List
from fastapi import APIRouter
from app.schemas.trace import TraceEvent

router = APIRouter(prefix="/traces", tags=["Traces"])


@router.get("", response_model=List[TraceEvent])
def list_traces() -> List[TraceEvent]:
    """
    Returns trace events. Empty in Phase 1; populated in Phase 4+.
    """
    return []
