from typing import Any, Dict, List
from sqlalchemy import String, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class BehaviorABIModel(Base):
    """
    Versioned, executable behavioral contract.
    CLAUDE.md §16: Behavior ABI definition.
    """
    __tablename__ = "behavior_abis"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    abi_version: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(String(512), nullable=False)
    prohibited_factors: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    permitted_factors: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    invariants: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    workflow_rules: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    release_constraints: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ABIRuleModel(Base):
    """
    Specific executable clause or constraint compiled within a Behavior ABI.
    CLAUDE.md §8 & §16.2: ABIRule model.
    """
    __tablename__ = "abi_rules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    rule_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    abi_version: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    rule_type: Mapped[str] = mapped_column(String(64), nullable=False)  # PROHIBITED_FACTOR, REQUIRED_STEP, INVARIANT
    clause: Mapped[str] = mapped_column(String(512), nullable=False)
    executable_action: Mapped[str] = mapped_column(String(512), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), default="CRITICAL", nullable=False)
