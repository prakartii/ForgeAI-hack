from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.trace import AgentRunModel
from app.schemas.trace import AgentRun

router = APIRouter(prefix="/runs", tags=["Runs"])


@router.get("", response_model=List[AgentRun])
def list_runs(
    claim_id: Optional[str] = None,
    scenario_id: Optional[str] = None,
    db: Session = Depends(get_db),
) -> List[AgentRunModel]:
    query = db.query(AgentRunModel)
    if claim_id:
        query = query.filter(AgentRunModel.claim_id == claim_id)
    if scenario_id:
        query = query.filter(AgentRunModel.scenario_id == scenario_id)
    return query.order_by(AgentRunModel.id.desc()).limit(200).all()
