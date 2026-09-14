from typing import List, Dict, Any
from fastapi import APIRouter

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
