from typing import Optional, Any, Dict, List
from sqlalchemy import String, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class ScenarioModel(Base):
    """
    Controlled scenario definition.
    CLAUDE.md §12: scenario_id, type, held-constant fields, controlled changes, expected invariant, difficulty.
    """
    __tablename__ = "scenarios"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    scenario_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    scenario_type: Mapped[str] = mapped_column(String(64), nullable=False)  # FAIRNESS, WORKFLOW, EVIDENCE, etc.
    description: Mapped[str] = mapped_column(String(512), nullable=False)
    base_claim_id: Mapped[str] = mapped_column(String(64), nullable=False)
    controlled_variables: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    held_constant_variables: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    expected_invariant: Mapped[str] = mapped_column(String(512), nullable=False)
    expected_result: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    failure_type: Mapped[str] = mapped_column(String(64), nullable=False)


class CounterfactualPairModel(Base):
    """
    Pair of matched counterfactual claims holding legitimate factors constant.
    CLAUDE.md §8 & §13: CounterfactualPair.
    """
    __tablename__ = "counterfactual_pairs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    pair_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    scenario_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    group_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    baseline_claim_id: Mapped[str] = mapped_column(String(64), nullable=False)
    counterfactual_claim_id: Mapped[str] = mapped_column(String(64), nullable=False)
    variation_description: Mapped[str] = mapped_column(String(512), nullable=False)
