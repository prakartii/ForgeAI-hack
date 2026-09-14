from typing import Dict, Any
from fastapi import APIRouter, Depends
from app.config.settings import get_settings, Settings

router = APIRouter(prefix="/prism", tags=["PRISM"])


@router.get("/status", response_model=Dict[str, Any])
def prism_status(settings: Settings = Depends(get_settings)) -> Dict[str, Any]:
    """
    Returns the real integration status of the PRISM SDK connection.
    Does not fake PRISM evidence or leak secrets.
    """
    is_configured = bool(settings.prism_api_key and settings.prism_project_id)
    return {
        "status": "configured" if is_configured else "not_configured",
        "project_id": settings.prism_project_id if is_configured else None,
        "base_url": settings.prism_base_url,
        "message": (
            "PRISM monitor client configured"
            if is_configured
            else "PRISM credentials pending in .env (Phase 5 integration)"
        ),
    }
