from typing import List, Dict, Any
from fastapi import APIRouter

router = APIRouter(prefix="/agents", tags=["Agents"])


@router.get("", response_model=List[Dict[str, Any]])
def list_agents() -> List[Dict[str, Any]]:
    """
    Returns registered agents in the FairClaim demonstration environment.
    Phase 1 endpoint definition.
    """
    return [
        {
            "name": "IntakeAgent",
            "role": "Document extraction, claim fact parsing, structured JSON generation",
            "status": "ready",
            "supported_versions": ["v1", "v2"],
        },
        {
            "name": "AdjudicationAgent",
            "role": "Deterministic prechecks, legitimate-factor extraction, coverage decision",
            "status": "ready",
            "supported_versions": ["v1", "v2"],
        },
        {
            "name": "ExplainabilityAgent",
            "role": "Evidence selection, customer explanation generation, citation verification",
            "status": "ready",
            "supported_versions": ["v1", "v2"],
        },
        {
            "name": "AppealsAgent",
            "role": "Material evidence check, decision reassessment, escalation routing",
            "status": "ready",
            "supported_versions": ["v1", "v2"],
        },
    ]
