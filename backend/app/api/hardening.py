from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.enforcement.engine import resolve_enforcement
from app.hardening.engine import run_hardening_ladder

router = APIRouter(prefix="/hardening", tags=["Hardening"])


@router.get("/ladders", response_model=List[Dict[str, Any]])
def list_hardening_ladders() -> List[Dict[str, Any]]:
    """
    Returns hardening difficulty challenge ladders.
    CLAUDE.md §18 definition.
    """
    return [
        {
            "track": "FAIRNESS",
            "levels": [
                {"level": 1, "description": "ZIP variation"},
                {"level": 2, "description": "ZIP + name variation"},
                {"level": 3, "description": "ZIP + name + narrative style variation"},
                {"level": 4, "description": "Multiple proxies + incomplete evidence"},
            ],
        },
        {
            "track": "WORKFLOW",
            "challenges": [
                "Missing evidence",
                "Contradictory evidence",
                "Explanation timeout",
                "Handoff failure",
                "Appeal without new evidence",
            ],
        },
    ]


@router.get("/results", response_model=Dict[str, Any])
def get_hardening_results(
    agent_version: str = "v1",
    enforced: bool = False,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Runs the real fairness hardening ladder (CLAUDE.md §18) against every
    counterfactual group and reports the measured pass rate per level.
    `enforced=true` resolves whichever Behavior ABI is currently compiled
    and active instead of running the raw agent version unprotected.
    """
    prohibited_fields: Optional[list[str]] = None
    if enforced:
        prohibited_fields = resolve_enforcement(db)["prohibited_fields"]
    return run_hardening_ladder(db, agent_version=agent_version, prohibited_fields=prohibited_fields)
