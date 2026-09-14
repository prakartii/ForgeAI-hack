"""
Scenario Engine Subsystem.
CLAUDE.md §11 & §12:
Generates controlled testing scenarios: FAIRNESS, WORKFLOW, EVIDENCE, DECISION_CORRECTNESS, HARDENING, REGRESSION.
Responsible for matched counterfactual pair generation holding legitimate facts constant.
"""

from app.scenarios.csv_loader import load_dataset, verify_oracle_consistency
from app.scenarios.oracle import OracleResult, evaluate_claim_oracle

__all__ = [
    "load_dataset",
    "verify_oracle_consistency",
    "OracleResult",
    "evaluate_claim_oracle",
]
