"""
Workflow State Machine Subsystem.
CLAUDE.md §5, §7 & §14:
Explicit, deterministic workflow state transitions.
Enforces required transitions (Intake -> Adjudication -> Explainability -> Verification -> Customer Communication)
and blocks forbidden bypass transitions.
"""

from app.workflow.state_machine import (
    REQUIRED_SEQUENCE,
    WorkflowState,
    WorkflowStateMachine,
    WorkflowViolation,
)

__all__ = [
    "REQUIRED_SEQUENCE",
    "WorkflowState",
    "WorkflowStateMachine",
    "WorkflowViolation",
]
