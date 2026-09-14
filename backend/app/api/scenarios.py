from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.scenario import ScenarioModel
from app.scenarios.csv_loader import load_dataset, verify_oracle_consistency
from app.schemas.scenario import Scenario

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])


@router.get("", response_model=List[Scenario])
def list_scenarios(
    scenario_type: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> List[ScenarioModel]:
    query = db.query(ScenarioModel)
    if scenario_type:
        query = query.filter(ScenarioModel.scenario_type == scenario_type)
    return query.order_by(ScenarioModel.id.asc()).limit(limit).all()


@router.post("/load", response_model=Dict[str, Any])
def load_demo_dataset(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Loads the synthetic FairClaim demo dataset (CLAUDE.md §7/§12/§28) into
    the database. Idempotent -- safe to call repeatedly. Also reports the
    deterministic oracle consistency check so a UI action can prove the
    ground truth is real, not asserted.
    """
    summary = load_dataset(db)
    oracle_check = verify_oracle_consistency(db)
    return {
        "loaded": summary,
        "oracle_check": {"checked": oracle_check["checked"], "mismatches": len(oracle_check["mismatches"])},
    }
