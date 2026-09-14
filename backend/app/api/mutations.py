from typing import List
from fastapi import APIRouter
from app.schemas.failure import Mutation

router = APIRouter(prefix="/mutations", tags=["Mutations"])


@router.get("", response_model=List[Mutation])
def list_mutations() -> List[Mutation]:
    """
    Returns applied behavioral mutations. Empty in Phase 1; populated in Phase 7+.
    """
    return []
