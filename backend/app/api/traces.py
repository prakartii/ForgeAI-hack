from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.trace import TraceEventModel
from app.schemas.trace import TraceEvent

router = APIRouter(prefix="/traces", tags=["Traces"])


@router.get("", response_model=List[TraceEvent])
def list_traces(
    run_id: Optional[str] = None,
    claim_id: Optional[str] = None,
    db: Session = Depends(get_db),
) -> List[TraceEventModel]:
    query = db.query(TraceEventModel)
    if run_id:
        query = query.filter(TraceEventModel.run_id == run_id)
    if claim_id:
        query = query.filter(TraceEventModel.claim_id == claim_id)
    return query.order_by(TraceEventModel.id.asc()).limit(500).all()
