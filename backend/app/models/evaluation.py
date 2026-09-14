from typing import Optional, Any, Dict, List
from sqlalchemy import String, Float, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class RegressionTestModel(Base):
    """
    Permanent regression test derived from a discovered failure.
    CLAUDE.md §19: id, failure_type, input, expected_behavior, abi_version_introduced, still_passing.
    """
    __tablename__ = "regression_tests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    test_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    failure_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    input_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    expected_behavior: Mapped[str] = mapped_column(String(512), nullable=False)
    abi_version_introduced: Mapped[str] = mapped_column(String(64), nullable=False)
    still_passing: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_tested_version: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)


class EvaluationResultModel(Base):
    """
    Computed evaluation metric result.
    CLAUDE.md §22: task correctness, pairwise consistency, disparity, workflow compliance, etc.
    """
    __tablename__ = "evaluation_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    evaluation_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    run_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    agent_version: Mapped[str] = mapped_column(String(32), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    prism_evaluator_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    details: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class ReleaseGateResultModel(Base):
    """
    Decision record from the release gate.
    CLAUDE.md §23: PASS only if critical violations = 0, regressions pass, etc. Otherwise BLOCKED.
    """
    __tablename__ = "release_gate_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    gate_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    candidate_version: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)  # PASS, BLOCKED
    violated_clauses: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    failure_summary: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    prism_evidence_ref: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
