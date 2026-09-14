"""
Enforcement Layer (CLAUDE.md §16.2): the point where a compiled Behavior
ABI's rules actually change runtime behavior, not just describe it.

`resolve_enforcement` reads a BehaviorABIModel's ABIRuleModel rows out of
the database and turns them into the exact keyword arguments
`app.agents.orchestrator.run_claim_pipeline` accepts: which context keys
to strip from Adjudication, and whether the workflow machine runs in
enforced mode. Passing the resulting `prohibited_fields` into the same
`build_adjudication_context` used by v1 is the literal, inspectable proof
CLAUDE.md §16.2 asks for -- the context object measurably loses the
`synthetic_pin_code`/etc. keys once this is applied, with no separate
"enforcement-only" code path to fake it.
"""
from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy.orm import Session

from app.models.abi import ABIRuleModel, BehaviorABIModel

# Maps an ABI's abstract prohibited-factor name (as written in
# abis/fairness.yaml, which mirrors CLAUDE.md §16's own vocabulary) to the
# concrete field name(s) actually present in this demo environment's
# Adjudication context (app.agents.adjudication.build_adjudication_context).
_ABI_FACTOR_TO_CONTEXT_FIELDS = {
    "ZIP": ["synthetic_pin_code", "state", "city"],
    "claimant_name": ["claimant_name_synthetic"],
    "narrative_style": ["narrative_style"],
    "inferred_income": [],
    "inferred_demographic_group": [],
}


@dataclass
class EnforcementDecision:
    abi_version: Optional[str]
    prohibited_fields: list[str] = field(default_factory=list)
    workflow_enforce: bool = True


def resolve_fairness_enforcement(db: Session, abi_version: str = "fair_adjudication_v1") -> EnforcementDecision:
    abi = db.query(BehaviorABIModel).filter_by(abi_version=abi_version, is_active=True).one_or_none()
    if abi is None:
        # No compiled ABI to enforce -- the caller must not silently invent
        # protection that was never actually compiled.
        return EnforcementDecision(abi_version=None, prohibited_fields=[])

    rules = db.query(ABIRuleModel).filter_by(abi_version=abi_version, rule_type="PROHIBITED_FACTOR").all()
    prohibited_fields: list[str] = []
    for rule in rules:
        # executable_action is "strip_field_from_adjudication_context:<factor>"
        factor = rule.executable_action.split(":", 1)[-1]
        prohibited_fields.extend(_ABI_FACTOR_TO_CONTEXT_FIELDS.get(factor, []))

    return EnforcementDecision(abi_version=abi_version, prohibited_fields=sorted(set(prohibited_fields)))


def resolve_workflow_enforcement(db: Session, abi_version: str = "fair_workflow_v1") -> EnforcementDecision:
    abi = db.query(BehaviorABIModel).filter_by(abi_version=abi_version, is_active=True).one_or_none()
    if abi is None:
        return EnforcementDecision(abi_version=None, workflow_enforce=False)
    return EnforcementDecision(abi_version=abi_version, workflow_enforce=True)


def resolve_enforcement(
    db: Session,
    *,
    fairness_abi_version: str = "fair_adjudication_v1",
    workflow_abi_version: str = "fair_workflow_v1",
) -> dict:
    """
    Convenience aggregate: the exact kwargs to hand to
    `run_claim_pipeline(..., prohibited_fields=..., workflow_enforce=...)`
    for a claim that must be run under whichever ABIs are currently
    compiled and active.
    """
    fairness = resolve_fairness_enforcement(db, fairness_abi_version)
    workflow = resolve_workflow_enforcement(db, workflow_abi_version)
    return {
        "prohibited_fields": fairness.prohibited_fields,
        "workflow_enforce": workflow.workflow_enforce,
        "fairness_abi_version": fairness.abi_version,
        "workflow_abi_version": workflow.abi_version,
    }
