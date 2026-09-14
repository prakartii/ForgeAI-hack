"""
Failure Detection Subsystem.
CLAUDE.md §11, §13, §14, §15:
Detects behavioral failures:
- Fairness: identical claim facts producing disparate decisions due to proxy factors.
- Workflow: sequence bypass, unverified customer communication, unevidenced appeals.
- Evidence: missing citations, non-existent policy clauses, contradictory explanations.
"""

from app.failures.detectors import (
    detect_decision_correctness_failure,
    detect_evidence_failure,
    detect_fairness_failure,
    detect_workflow_failure,
)
from app.failures.scanner import scan_claims, scan_fairness_groups

__all__ = [
    "detect_decision_correctness_failure",
    "detect_evidence_failure",
    "detect_fairness_failure",
    "detect_workflow_failure",
    "scan_claims",
    "scan_fairness_groups",
]
