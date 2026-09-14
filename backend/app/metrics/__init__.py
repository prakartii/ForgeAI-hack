"""
Metrics Subsystem.
CLAUDE.md §22:
Computes deterministic, ground-truth-derived metrics from real execution runs:
- Task correctness
- Pairwise consistency
- Decision disparity
- Payout disparity
- Workflow compliance
- Evidence completeness
- Regression pass rate
- Challenge robustness
"""

from app.metrics.engine import compute_metrics

__all__ = ["compute_metrics"]
