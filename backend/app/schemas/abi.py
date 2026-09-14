from typing import List, Dict, Any
from datetime import datetime
from pydantic import Field
from app.schemas.base import SchemaModel


class ABIInvariant(SchemaModel):
    name: str
    rule: str


class BehaviorABIBase(SchemaModel):
    abi_version: str
    name: str
    description: str
    prohibited_factors: List[str] = Field(default_factory=list)
    permitted_factors: List[str] = Field(default_factory=list)
    invariants: List[Dict[str, Any]] = Field(default_factory=list)
    workflow_rules: List[Dict[str, Any]] = Field(default_factory=list)
    release_constraints: List[str] = Field(default_factory=list)
    is_active: bool = True


class BehaviorABICreate(BehaviorABIBase):
    pass


class BehaviorABI(BehaviorABIBase):
    id: int
    created_at: datetime
    updated_at: datetime


class ABIRuleBase(SchemaModel):
    rule_id: str
    abi_version: str
    rule_type: str  # PROHIBITED_FACTOR, REQUIRED_STEP, INVARIANT
    clause: str
    executable_action: str
    severity: str = "CRITICAL"


class ABIRuleCreate(ABIRuleBase):
    pass


class ABIRule(ABIRuleBase):
    id: int
    created_at: datetime
    updated_at: datetime
