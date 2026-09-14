from typing import Optional, Any, Dict
from sqlalchemy import String, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class FailureModel(Base):
    """
    Diagnosed agent failure event.
    CLAUDE.md §8: Failure model.
    """
    __tablename__ = "failures"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    failure_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    failure_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)  # FAIRNESS, WORKFLOW, EVIDENCE, etc.
    severity: Mapped[str] = mapped_column(String(32), default="CRITICAL", nullable=False)  # CRITICAL, HIGH, MEDIUM, LOW
    description: Mapped[str] = mapped_column(String(512), nullable=False)
    affected_agent: Mapped[str] = mapped_column(String(64), nullable=False)
    scenario_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    run_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    prism_session_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    diagnosis: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class MutationModel(Base):
    """
    Targeted behavioral mutation applied to remedy a diagnosed failure.
    CLAUDE.md §17: mutation_id, source_failure_id, source_abi_version, description, affected_component, before_state, after_state.
    """
    __tablename__ = "mutations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    mutation_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    source_failure_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    source_abi_version: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(String(512), nullable=False)
    affected_component: Mapped[str] = mapped_column(String(64), nullable=False)
    before_state: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    after_state: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
