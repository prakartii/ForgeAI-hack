from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import Field
from app.schemas.base import SchemaModel


class ReleaseStatus(str, Enum):
    PASS = "PASS"
    BLOCKED = "BLOCKED"


class RegressionTestBase(SchemaModel):
    test_id: str
    failure_type: str
    input_data: Dict[str, Any] = Field(default_factory=dict)
    expected_behavior: str
    abi_version_introduced: str
    still_passing: bool = True
    last_tested_version: Optional[str] = None


class RegressionTestCreate(RegressionTestBase):
    pass


class RegressionTest(RegressionTestBase):
    id: int
    created_at: datetime
    updated_at: datetime


class EvaluationResultBase(SchemaModel):
    evaluation_id: str
    run_id: Optional[str] = None
    agent_version: str
    metric_name: str
    metric_value: float
    passed: bool
    prism_evaluator_name: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class EvaluationResultCreate(EvaluationResultBase):
    pass


class EvaluationResult(EvaluationResultBase):
    id: int
    created_at: datetime
    updated_at: datetime


class ReleaseGateResultBase(SchemaModel):
    gate_id: str
    candidate_version: str
    status: ReleaseStatus
    violated_clauses: List[str] = Field(default_factory=list)
    failure_summary: Dict[str, Any] = Field(default_factory=dict)
    prism_evidence_ref: Optional[str] = None


class ReleaseGateResultCreate(ReleaseGateResultBase):
    pass


class ReleaseGateResult(ReleaseGateResultBase):
    id: int
    created_at: datetime
    updated_at: datetime
