from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.failure import FailureModel
from app.schemas.failure import Failure

router = APIRouter(prefix="/failures", tags=["Failures"])


@router.get("", response_model=List[Failure])
def list_failures(
    failure_type: Optional[str] = None,
    resolved: Optional[bool] = None,
    db: Session = Depends(get_db),
) -> List[FailureModel]:
    query = db.query(FailureModel)
    if failure_type:
        query = query.filter(FailureModel.failure_type == failure_type)
    if resolved is not None:
        query = query.filter(FailureModel.resolved == resolved)
    return query.order_by(FailureModel.id.desc()).limit(200).all()
