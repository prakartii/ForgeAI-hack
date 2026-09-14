from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import Field
from app.schemas.base import SchemaModel


# --- Policy Schemas ---
class PolicyBase(SchemaModel):
    policy_id: str
    active_start: Optional[str] = None
    active_end: Optional[str] = None
    is_active: bool = True
    covered_perils: List[str] = Field(default_factory=list)
    deductible: float = 0.0
    coverage_limit: float = 0.0
    exclusions: List[str] = Field(default_factory=list)
    metadata_info: Dict[str, Any] = Field(default_factory=dict)


class PolicyCreate(PolicyBase):
    pass


class Policy(PolicyBase):
    id: int
    created_at: datetime
    updated_at: datetime


# --- Claim Schemas ---
class ClaimBase(SchemaModel):
    claim_id: str
    policy_id: str
    loss_date: Optional[str] = None
    peril: str
    damage_type: str
    verified_damage: float = 0.0
    evidence_status: str = "pending"
    proxy_variants: Dict[str, Any] = Field(default_factory=dict)
    details: Dict[str, Any] = Field(default_factory=dict)


class ClaimCreate(ClaimBase):
    pass


class Claim(ClaimBase):
    id: int
    created_at: datetime
    updated_at: datetime


# --- Document Schemas ---
class DocumentBase(SchemaModel):
    document_id: str
    claim_id: str
    doc_type: str
    file_path: Optional[str] = None
    extracted_text: Optional[str] = None
    evidence_references: List[str] = Field(default_factory=list)


class DocumentCreate(DocumentBase):
    pass


class Document(DocumentBase):
    id: int
    created_at: datetime
    updated_at: datetime


# --- Evidence Schemas ---
class EvidenceBase(SchemaModel):
    evidence_id: str
    claim_id: str
    evidence_type: str
    description: str
    verified: bool = False
    source_ref: Optional[str] = None


class EvidenceCreate(EvidenceBase):
    pass


class Evidence(EvidenceBase):
    id: int
    created_at: datetime
    updated_at: datetime


# --- WorkflowState Schemas ---
class WorkflowStateBase(SchemaModel):
    state_id: str
    claim_id: str
    run_id: Optional[str] = None
    current_agent: str
    required_next_step: str
    explanation_verified: bool = False
    customer_communication_allowed: bool = False
    history: List[Dict[str, Any]] = Field(default_factory=list)


class WorkflowStateCreate(WorkflowStateBase):
    pass


class WorkflowState(WorkflowStateBase):
    id: int
    created_at: datetime
    updated_at: datetime


# --- GroundTruth Schemas ---
class GroundTruthBase(SchemaModel):
    oracle_id: str
    claim_id: str
    expected_decision: str  # APPROVE, DENY, ESCALATE
    expected_payout: float = 0.0
    reason: str
    required_evidence: List[str] = Field(default_factory=list)
    expected_handoffs: List[str] = Field(default_factory=list)


class GroundTruthCreate(GroundTruthBase):
    pass


class GroundTruth(GroundTruthBase):
    id: int
    created_at: datetime
    updated_at: datetime
