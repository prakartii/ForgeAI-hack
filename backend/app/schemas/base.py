from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class SchemaModel(BaseModel):
    """
    Base Pydantic model for all FailureFoundry schemas.
    Configured for ORM compatibility and attribute population.
    """
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class HealthResponse(SchemaModel):
    """
    Health check response model.
    """
    status: str
    app: str
    version: str
    environment: str
    database: str
    graph_database: Optional[str] = "standby"
    timestamp: datetime
