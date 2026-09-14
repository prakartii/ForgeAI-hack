from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.neo4j import get_neo4j_client, Neo4jClient
from app.config.settings import get_settings, Settings
from app.schemas.base import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def health_check(
    db: Session = Depends(get_db),
    neo4j: Neo4jClient = Depends(get_neo4j_client),
    settings: Settings = Depends(get_settings),
) -> HealthResponse:
    """
    Health check endpoint returning application, environment, and polyglot database connectivity status.
    SQLite is primary system of record; Neo4j is graph projection.
    """
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    graph_check = neo4j.check_connection()
    graph_status = graph_check.get("status", "standby")

    return HealthResponse(
        status="ok" if db_status == "connected" else "degraded",
        app=settings.app_name,
        version="0.1.0",
        environment=settings.app_env,
        database=db_status,
        graph_database=graph_status,
        timestamp=datetime.now(timezone.utc),
    )
