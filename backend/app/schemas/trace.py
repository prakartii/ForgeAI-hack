from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import Field
from app.schemas.base import SchemaModel


class AgentRunBase(SchemaModel):
    run_id: str
    claim_id: str
    agent_name: str
    agent_version: str = "v1"
    scenario_id: Optional[str] = None
    counterfactual_group: Optional[str] = None
    abi_version: Optional[str] = None
    mutation_id: Optional[str] = None
    prism_session_id: Optional[str] = None
    status: str = "pending"


class AgentRunCreate(AgentRunBase):
    pass


class AgentRun(AgentRunBase):
    id: int
    created_at: datetime
    updated_at: datetime


class TraceEventBase(SchemaModel):
    event_id: str
    run_id: str
    claim_id: str
    agent_name: str
    agent_version: str
    input_payload: Dict[str, Any] = Field(default_factory=dict)
    output_payload: Dict[str, Any] = Field(default_factory=dict)
    model_metadata: Dict[str, Any] = Field(default_factory=dict)
    prompt_metadata: Dict[str, Any] = Field(default_factory=dict)
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    handoffs: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    retries: int = 0
    timestamps: Dict[str, Any] = Field(default_factory=dict)
    state_changes: List[Dict[str, Any]] = Field(default_factory=list)
    scenario_id: Optional[str] = None
    counterfactual_group: Optional[str] = None
    abi_version: Optional[str] = None
    mutation_id: Optional[str] = None
    prism_session_id: Optional[str] = None


class TraceEventCreate(TraceEventBase):
    pass


class TraceEvent(TraceEventBase):
    id: int
    created_at: datetime
    updated_at: datetime


class TraceEnvelope(SchemaModel):
    """
    Standard common trace envelope used by every agent and tool call.
    Matches CLAUDE.md §9 exactly.
    """
    run_id: str
    claim_id: str
    agent_name: str
    agent_version: str
    input: Dict[str, Any] = Field(default_factory=dict)
    output: Dict[str, Any] = Field(default_factory=dict)
    model_metadata: Dict[str, Any] = Field(default_factory=dict)
    prompt_metadata: Dict[str, Any] = Field(default_factory=dict)
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    handoffs: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    retries: int = 0
    timestamps: Dict[str, Any] = Field(default_factory=dict)
    state_changes: List[Dict[str, Any]] = Field(default_factory=list)
    scenario_id: Optional[str] = None
    counterfactual_group: Optional[str] = None
    abi_version: Optional[str] = None
    mutation_id: Optional[str] = None
    prism_session_id: Optional[str] = None
