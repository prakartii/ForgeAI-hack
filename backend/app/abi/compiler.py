"""
Behavior ABI Compiler (CLAUDE.md §16.1).

Compiles the versioned YAML specifications in /abis into persisted,
executable BehaviorABIModel + ABIRuleModel rows. This is what makes a
Behavior ABI more than a comment: every ABIRuleModel carries an
`executable_action` string that the Enforcement Layer (app.enforcement)
actually interprets at runtime, rather than a human-readable description
that nothing reads.

Ties an ABI back to the diagnosed Failure that justified compiling it
(when one is given), so the chain PRISM evidence -> Failure -> Behavior
ABI stays traceable end to end (CLAUDE.md §9).
"""
from pathlib import Path
from typing import Optional

import yaml
from sqlalchemy.orm import Session

from app.models.abi import ABIRuleModel, BehaviorABIModel
from app.traces.wrapper import new_id

ABIS_DIR = Path(__file__).resolve().parents[3] / "abis"


def _load_yaml_spec(filename: str) -> dict:
    with open(ABIS_DIR / filename, encoding="utf-8") as f:
        return yaml.safe_load(f)


def compile_fairness_abi(db: Session, *, source_failure_id: Optional[str] = None) -> BehaviorABIModel:
    spec = _load_yaml_spec("fairness.yaml")
    abi = db.query(BehaviorABIModel).filter_by(abi_version=spec["abi_version"]).one_or_none()
    if abi is not None:
        return abi

    abi = BehaviorABIModel(
        abi_version=spec["abi_version"],
        name="Fairness Adjudication ABI",
        description=spec["description"],
        prohibited_factors=spec["prohibited"],
        permitted_factors=spec["permitted"],
        invariants=spec["invariants"],
        workflow_rules=[],
        release_constraints=spec["release"],
    )
    db.add(abi)
    db.flush()

    for factor in spec["prohibited"]:
        db.add(
            ABIRuleModel(
                rule_id=new_id("rule"),
                abi_version=abi.abi_version,
                rule_type="PROHIBITED_FACTOR",
                clause=f"Adjudication must not use '{factor}' as a decision factor.",
                executable_action=f"strip_field_from_adjudication_context:{factor}",
                severity="CRITICAL",
            )
        )
    for invariant in spec["invariants"]:
        db.add(
            ABIRuleModel(
                rule_id=new_id("rule"),
                abi_version=abi.abi_version,
                rule_type="INVARIANT",
                clause=invariant["rule"],
                executable_action="run_counterfactual_pairwise_check",
                severity="CRITICAL",
            )
        )

    _link_source_failure(db, abi.abi_version, source_failure_id)
    db.commit()
    return abi


def compile_workflow_abi(db: Session, *, source_failure_id: Optional[str] = None) -> BehaviorABIModel:
    spec = _load_yaml_spec("workflow.yaml")
    abi = db.query(BehaviorABIModel).filter_by(abi_version=spec["abi_version"]).one_or_none()
    if abi is not None:
        return abi

    abi = BehaviorABIModel(
        abi_version=spec["abi_version"],
        name="Workflow Sequencing ABI",
        description=spec["description"],
        prohibited_factors=[],
        permitted_factors=[],
        invariants=[],
        workflow_rules=spec["requirements"],
        release_constraints=spec["release"],
    )
    db.add(abi)
    db.flush()

    for transition in spec["forbidden_transitions"]:
        db.add(
            ABIRuleModel(
                rule_id=new_id("rule"),
                abi_version=abi.abi_version,
                rule_type="REQUIRED_STEP",
                clause=(
                    f"Forbidden transition {transition['from']} -> {transition['to']}: {transition['reason']}"
                ),
                executable_action="enforce_workflow_state_machine",
                severity="CRITICAL",
            )
        )
    for requirement in spec["requirements"]:
        db.add(
            ABIRuleModel(
                rule_id=new_id("rule"),
                abi_version=abi.abi_version,
                rule_type="REQUIRED_STEP",
                clause=requirement["rule"],
                executable_action="enforce_workflow_state_machine",
                severity="CRITICAL",
            )
        )

    _link_source_failure(db, abi.abi_version, source_failure_id)
    db.commit()
    return abi


def _link_source_failure(db: Session, abi_version: str, failure_id: Optional[str]) -> None:
    if not failure_id:
        return
    from app.models.failure import FailureModel

    failure = db.query(FailureModel).filter_by(failure_id=failure_id).one_or_none()
    if failure is not None:
        failure.diagnosis = {**failure.diagnosis, "compiled_abi_version": abi_version}
