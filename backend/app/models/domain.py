from typing import Optional, Any, Dict, List
from sqlalchemy import String, Float, Boolean, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class PolicyModel(Base):
    """
    Synthetic Insurance Policy table.
    CLAUDE.md §7: policy_id, active dates, covered perils, deductible, coverage limit, exclusions.
    """
    __tablename__ = "policies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    policy_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    active_start: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    active_end: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    covered_perils: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    deductible: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    coverage_limit: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    exclusions: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    metadata_info: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class ClaimModel(Base):
    """
    Synthetic Insurance Claim table.
    CLAUDE.md §7: claim_id, loss date, peril, damage type, verified damage, evidence status, proxy variants.
    """
    __tablename__ = "claims"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    claim_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    policy_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    loss_date: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    peril: Mapped[str] = mapped_column(String(64), nullable=False)
    damage_type: Mapped[str] = mapped_column(String(128), nullable=False)
    verified_damage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    evidence_status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    proxy_variants: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    details: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class DocumentModel(Base):
    """
    Claim document metadata and extracted content.
    CLAUDE.md §7: policy declaration, FNOL, repair estimate, adjuster note, evidence references.
    """
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    document_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    claim_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    doc_type: Mapped[str] = mapped_column(String(64), nullable=False)  # FNOL, repair_estimate, etc.
    file_path: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    extracted_text: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    evidence_references: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)


class EvidenceModel(Base):
    """
    Supporting evidence verified for a claim.
    CLAUDE.md §8: domain data Evidence object.
    """
    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    evidence_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    claim_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(String(512), nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    source_ref: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)


class WorkflowStateModel(Base):
    """
    Explicit, deterministic workflow state.
    CLAUDE.md §7: current agent, required next step, explanation_verified, customer_communication_allowed.
    """
    __tablename__ = "workflow_states"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    state_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    claim_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    run_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    current_agent: Mapped[str] = mapped_column(String(64), nullable=False)
    required_next_step: Mapped[str] = mapped_column(String(64), nullable=False)
    explanation_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    customer_communication_allowed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    history: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)


class GroundTruthModel(Base):
    """
    Deterministic business-rule oracle outcome for testing and evaluation.
    CLAUDE.md §7: decision, payout, reason, required evidence, expected handoffs.
    """
    __tablename__ = "ground_truth"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    oracle_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    claim_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    expected_decision: Mapped[str] = mapped_column(String(32), nullable=False)  # APPROVE, DENY, ESCALATE
    expected_payout: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    reason: Mapped[str] = mapped_column(String(512), nullable=False)
    required_evidence: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    expected_handoffs: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
