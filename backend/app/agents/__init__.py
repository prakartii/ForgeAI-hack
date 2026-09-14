"""
Insurance Agent Subsystem (FairClaim Demonstration Environment).
CLAUDE.md §4 & §6:
Intake Agent, Adjudication Agent, Explainability Agent, Appeals Agent.

Architectural Rule:
This demonstration environment talks to FailureFoundry through the trace/scenario layer.
It must never directly import from app.abi or app.enforcement.
"""

from app.agents.adjudication import PROXY_FIELDS, build_adjudication_context, run_adjudication
from app.agents.adjudication_explainability import run_adjudication_and_explainability
from app.agents.appeals import run_appeals
from app.agents.explainability import run_explainability
from app.agents.intake import run_intake
from app.agents.orchestrator import run_appeal, run_claim_pipeline

__all__ = [
    "PROXY_FIELDS",
    "build_adjudication_context",
    "run_adjudication",
    "run_adjudication_and_explainability",
    "run_appeals",
    "run_explainability",
    "run_intake",
    "run_appeal",
    "run_claim_pipeline",
]
