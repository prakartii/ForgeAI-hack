"""
Enforced pipeline entry point (CLAUDE.md §16.2). This is the only place
that both compiles/reads Behavior ABIs (app.abi, app.enforcement) and
drives the agent runtime (app.agents.orchestrator) -- the two subsystems
that must otherwise stay decoupled per CLAUDE.md §4's system boundary
table.
"""
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.agents.orchestrator import run_claim_pipeline
from app.enforcement.engine import resolve_enforcement
from app.models.domain import ClaimModel, PolicyModel


def run_claim_with_enforcement(
    db: Session,
    claim: ClaimModel,
    policy: PolicyModel,
    *,
    agent_version: str = "v2",
    scenario_id: Optional[str] = None,
    counterfactual_group: Optional[str] = None,
) -> dict[str, Any]:
    enforcement = resolve_enforcement(db)
    return run_claim_pipeline(
        db,
        claim,
        policy,
        agent_version=agent_version,
        prohibited_fields=enforcement["prohibited_fields"],
        workflow_enforce=enforcement["workflow_enforce"],
        scenario_id=scenario_id,
        counterfactual_group=counterfactual_group,
        abi_version=enforcement["fairness_abi_version"],
    )
