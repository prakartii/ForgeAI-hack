from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import Field
from app.schemas.base import SchemaModel


class ScenarioType(str, Enum):
    FAIRNESS = "FAIRNESS"
    WORKFLOW = "WORKFLOW"
    EVIDENCE = "EVIDENCE"
    DECISION_CORRECTNESS = "DECISION_CORRECTNESS"
    HARDENING = "HARDENING"
    REGRESSION = "REGRESSION"


class ScenarioBase(SchemaModel):
    scenario_id: str
    scenario_type: ScenarioType
    description: str
    base_claim_id: str
    controlled_variables: Dict[str, Any] = Field(default_factory=dict)
    held_constant_variables: List[str] = Field(default_factory=list)
    expected_invariant: str
    expected_result: Dict[str, Any] = Field(default_factory=dict)
    difficulty: int = 1
    failure_type: str


class ScenarioCreate(ScenarioBase):
    pass


class Scenario(ScenarioBase):
    id: int
    created_at: datetime
    updated_at: datetime


class CounterfactualPairBase(SchemaModel):
    pair_id: str
    scenario_id: str
    group_id: str
    baseline_claim_id: str
    counterfactual_claim_id: str
    variation_description: str


class CounterfactualPairCreate(CounterfactualPairBase):
    pass


class CounterfactualPair(CounterfactualPairBase):
    id: int
    created_at: datetime
    updated_at: datetime
