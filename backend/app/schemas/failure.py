from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import Field
from app.schemas.base import SchemaModel


class FailureSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class FailureBase(SchemaModel):
    failure_id: str
    failure_type: str  # FAIRNESS, WORKFLOW, EVIDENCE, etc.
    severity: FailureSeverity = FailureSeverity.CRITICAL
    description: str
    affected_agent: str
    scenario_id: Optional[str] = None
    run_id: Optional[str] = None
    prism_session_id: Optional[str] = None
    diagnosis: Dict[str, Any] = Field(default_factory=dict)
    resolved: bool = False


class FailureCreate(FailureBase):
    pass


class Failure(FailureBase):
    id: int
    created_at: datetime
    updated_at: datetime


class MutationBase(SchemaModel):
    mutation_id: str
    source_failure_id: str
    source_abi_version: str
    description: str
    affected_component: str
    before_state: Dict[str, Any] = Field(default_factory=dict)
    after_state: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class MutationCreate(MutationBase):
    pass


class Mutation(MutationBase):
    id: int
    created_at: datetime
    updated_at: datetime
