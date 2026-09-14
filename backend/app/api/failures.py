from typing import List
from fastapi import APIRouter
from app.schemas.failure import Failure

router = APIRouter(prefix="/failures", tags=["Failures"])


@router.get("", response_model=List[Failure])
def list_failures() -> List[Failure]:
    """
    Returns detected behavioral failures. Empty in Phase 1; populated in Phase 6+.
    """
    return []
