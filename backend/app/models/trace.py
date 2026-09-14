from typing import Optional, Any, Dict, List
from sqlalchemy import String, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class AgentRunModel(Base):
    """
    Records an agent execution run.
    CLAUDE.md §8 & §9: AgentRun model.
    """
    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    claim_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    agent_name: Mapped[str] = mapped_column(String(64), nullable=False)
    agent_version: Mapped[str] = mapped_column(String(32), default="v1", nullable=False)
    scenario_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    counterfactual_group: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    abi_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    mutation_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    prism_session_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)  # pending, running, completed, failed


class TraceEventModel(Base):
    """
    Granular trace event capturing LLM, tool, or state actions.
    CLAUDE.md §9: Required trace envelope.
    """
    __tablename__ = "trace_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    run_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    claim_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    agent_name: Mapped[str] = mapped_column(String(64), nullable=False)
    agent_version: Mapped[str] = mapped_column(String(32), nullable=False)
    input_payload: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    output_payload: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    model_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    prompt_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    tool_calls: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    handoffs: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    errors: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    retries: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    timestamps: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    state_changes: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    scenario_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    counterfactual_group: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    abi_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    mutation_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    prism_session_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
