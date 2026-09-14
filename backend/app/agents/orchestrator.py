"""
Insurance agent pipeline orchestrator (CLAUDE.md §6, §9, §14).

Runs Intake -> Adjudication -> Explainability -> Verification -> Customer
Communication for one claim, wrapping every agent call in a TraceRecorder
(CLAUDE.md §9) and driving the workflow through the WorkflowStateMachine
(CLAUDE.md §14). This is the runtime hook enforcement (Phase 8) attaches
to: `prohibited_fields` and `workflow_enforce` are the two levers a
Behavior ABI compiles into actual runtime controls, rather than being
decided by agent version. When they are not passed explicitly, they
default to the CLAUDE.md §29 controlled v1 behavior (proxy fields exposed,
workflow bypass allowed) for agent_version="v1", and to the fixed v2
behavior otherwise.

This module only reaches into app.traces and app.workflow -- never into
app.abi or app.enforcement directly -- keeping the demonstration
environment decoupled from FailureFoundry's governance internals per
CLAUDE.md §4's system boundary table.
"""
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.agents.adjudication import PROXY_FIELDS, build_adjudication_context, run_adjudication
from app.agents.adjudication_explainability import run_adjudication_and_explainability
from app.agents.appeals import run_appeals
from app.agents.explainability import run_explainability
from app.agents.intake import run_intake
from app.models.domain import ClaimModel, PolicyModel
from app.traces.wrapper import TraceRecorder
from app.workflow.state_machine import WorkflowStateMachine, WorkflowViolation


def run_claim_pipeline(
    db: Session,
    claim: ClaimModel,
    policy: PolicyModel,
    *,
    agent_version: str = "v1",
    prohibited_fields: Optional[list[str]] = None,
    workflow_enforce: Optional[bool] = None,
    scenario_id: Optional[str] = None,
    counterfactual_group: Optional[str] = None,
    abi_version: Optional[str] = None,
    mutation_id: Optional[str] = None,
) -> dict[str, Any]:
    if workflow_enforce is None:
        workflow_enforce = agent_version != "v1"
    if prohibited_fields is None:
        prohibited_fields = [] if agent_version == "v1" else PROXY_FIELDS

    def trace(agent_name: str) -> TraceRecorder:
        return TraceRecorder(
            db,
            claim_id=claim.claim_id,
            agent_name=agent_name,
            agent_version=agent_version,
            scenario_id=scenario_id,
            counterfactual_group=counterfactual_group,
            abi_version=abi_version,
            mutation_id=mutation_id,
        )

    wf = WorkflowStateMachine(claim.claim_id, enforce=workflow_enforce)
    result: dict[str, Any] = {"status": "IN_PROGRESS"}

    with trace("intake") as tr:
        intake_result = run_intake(claim)
        tr.record_event(
            input_payload={"claim_id": claim.claim_id},
            output_payload=intake_result,
            handoffs=[{"to": "adjudication"}],
        )
    result["intake"] = intake_result
    wf.transition("ADJUDICATION")

    with trace("adjudication") as tr:
        # Run combined Adjudication and Explainability agent
        combined_result = run_adjudication_and_explainability(
            claim,
            policy,
            prohibited_fields=prohibited_fields,
            intake_action=intake_result["action"],
            inject_failure=True,
        )
        adjudication_result = combined_result["adjudication"]
        tr.record_event(
            input_payload={"context_keys": sorted(adjudication_result["context_used"].keys())},
            output_payload={k: v for k, v in adjudication_result.items() if k != "context_used"},
            handoffs=[{"to": "explainability"}],
        )
    result["adjudication"] = adjudication_result
    result["combined_agent"] = combined_result

    if not workflow_enforce:
        # CLAUDE.md §29 controlled v1 weakness: Adjudication can reach
        # customer communication directly, with no explanation or
        # verification step in between.
        wf.transition("CUSTOMER_COMMUNICATION")
        result["explainability"] = None
        result["workflow_state"] = wf.state
        result["status"] = "COMMUNICATED_WITHOUT_VERIFICATION"
        return result

    wf.transition("EXPLANATION")
    explainability_result = combined_result["explainability"]
    with trace("explainability") as tr:
        tr.record_event(
            input_payload={"decision": adjudication_result["decision"]},
            output_payload=explainability_result,
            handoffs=[{"to": "verification"}],
        )
    result["explainability"] = explainability_result

    wf.transition("VERIFICATION")
    if explainability_result["citation_valid"] and explainability_result["supported_by_evidence"]:
        wf.mark_explanation_verified()

    try:
        wf.transition("CUSTOMER_COMMUNICATION")
        result["status"] = "COMPLETED"
    except WorkflowViolation as violation:
        result["status"] = "BLOCKED_CUSTOMER_COMMUNICATION"
        result["block_reason"] = str(violation)

    result["workflow_state"] = wf.state
    return result


def run_appeal(
    db: Session,
    claim: ClaimModel,
    previous_decision: str,
    *,
    agent_version: str = "v1",
    has_new_evidence: Optional[bool] = None,
    scenario_id: Optional[str] = None,
) -> dict[str, Any]:
    with TraceRecorder(
        db,
        claim_id=claim.claim_id,
        agent_name="appeals",
        agent_version=agent_version,
        scenario_id=scenario_id,
    ) as tr:
        appeal_result = run_appeals(claim, previous_decision, has_new_evidence=has_new_evidence)
        tr.record_event(
            input_payload={"previous_decision": previous_decision},
            output_payload=appeal_result,
        )
    return appeal_result
