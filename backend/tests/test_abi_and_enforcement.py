import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.abi.compiler import compile_fairness_abi, compile_workflow_abi
from app.agents.adjudication import build_adjudication_context
from app.db.base import Base
import app.models  # noqa: F401
from app.enforcement.engine import resolve_enforcement, resolve_fairness_enforcement
from app.enforcement.runner import run_claim_with_enforcement
from app.failures.scanner import scan_fairness_groups
from app.models.abi import ABIRuleModel, BehaviorABIModel
from app.models.domain import ClaimModel, PolicyModel
from app.scenarios.csv_loader import load_dataset


@pytest.fixture(scope="module")
def loaded_db(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("abi_db")
    engine = create_engine(f"sqlite:///{tmp_path}/test.db")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    load_dataset(session)
    yield session
    session.close()


def _claim_and_policy(db, claim_id):
    claim = db.query(ClaimModel).filter_by(claim_id=claim_id).one()
    policy = db.query(PolicyModel).filter_by(policy_id=claim.policy_id).one()
    return claim, policy


def test_compile_fairness_abi_persists_versioned_abi_with_executable_rules(loaded_db):
    abi = compile_fairness_abi(loaded_db)
    assert abi.abi_version == "fair_adjudication_v1"
    assert "synthetic" not in " ".join(abi.prohibited_factors)  # abstract factor names from the spec

    rules = loaded_db.query(ABIRuleModel).filter_by(abi_version=abi.abi_version).all()
    assert len(rules) > 0
    assert all(rule.executable_action for rule in rules)
    prohibited_rules = [r for r in rules if r.rule_type == "PROHIBITED_FACTOR"]
    assert len(prohibited_rules) == len(abi.prohibited_factors)


def test_compile_is_idempotent(loaded_db):
    first = compile_fairness_abi(loaded_db)
    second = compile_fairness_abi(loaded_db)
    assert first.id == second.id
    assert loaded_db.query(BehaviorABIModel).filter_by(abi_version="fair_adjudication_v1").count() == 1


def test_workflow_abi_compiles_required_step_rules(loaded_db):
    abi = compile_workflow_abi(loaded_db)
    assert abi.abi_version == "fair_workflow_v1"
    rules = loaded_db.query(ABIRuleModel).filter_by(abi_version=abi.abi_version).all()
    assert all(r.executable_action == "enforce_workflow_state_machine" for r in rules)


def test_before_after_context_no_longer_contains_proxy_fields_once_abi_enforced(loaded_db):
    """
    CLAUDE.md sec16.2's literal requirement: a before/after test showing the
    Adjudication Agent's context object no longer contains the proxy keys
    after the fairness ABI is applied.
    """
    claim, policy = _claim_and_policy(loaded_db, "CF_001_V1")

    before = build_adjudication_context(claim, policy)  # no ABI applied
    assert "synthetic_pin_code" in before
    assert "claimant_name_synthetic" in before
    assert "narrative_style" in before

    compile_fairness_abi(loaded_db)
    enforcement = resolve_fairness_enforcement(loaded_db)
    assert "synthetic_pin_code" in enforcement.prohibited_fields
    assert "claimant_name_synthetic" in enforcement.prohibited_fields
    assert "narrative_style" in enforcement.prohibited_fields

    after = build_adjudication_context(claim, policy, prohibited_fields=enforcement.prohibited_fields)
    assert "synthetic_pin_code" not in after
    assert "claimant_name_synthetic" not in after
    assert "narrative_style" not in after
    # legitimate factors remain untouched
    assert after["verified_damage_inr"] == before["verified_damage_inr"]


def test_enforced_pipeline_end_to_end_fixes_fairness_and_workflow(loaded_db):
    compile_fairness_abi(loaded_db)
    compile_workflow_abi(loaded_db)

    enforcement = resolve_enforcement(loaded_db)
    assert enforcement["workflow_enforce"] is True
    assert set(enforcement["prohibited_fields"]) >= {
        "synthetic_pin_code", "claimant_name_synthetic", "narrative_style",
    }

    variant_ids = ["CF_001_V1", "CF_001_V2", "CF_001_V3", "CF_001_V4"]
    outcomes = set()
    for cid in variant_ids:
        claim, policy = _claim_and_policy(loaded_db, cid)
        result = run_claim_with_enforcement(loaded_db, claim, policy, scenario_id=cid)
        outcomes.add((result["adjudication"]["decision"], result["adjudication"]["payout"]))
        assert result["status"] == "COMPLETED"  # workflow enforced, explanation verified

    assert len(outcomes) == 1  # fairness fixed: all variants now agree


def test_rerunning_fairness_scan_under_enforcement_finds_zero_failures(loaded_db):
    compile_fairness_abi(loaded_db)
    enforcement = resolve_fairness_enforcement(loaded_db)
    failures = scan_fairness_groups(loaded_db, agent_version="v2", prohibited_fields=enforcement.prohibited_fields)
    assert failures == []
