import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
import app.models  # noqa: F401
from app.agents.adjudication import PROXY_FIELDS, run_adjudication
from app.agents.intake import run_intake
from app.agents.orchestrator import run_appeal, run_claim_pipeline
from app.models.domain import ClaimModel, PolicyModel
from app.models.trace import AgentRunModel, TraceEventModel
from app.scenarios.csv_loader import load_dataset


@pytest.fixture(scope="module")
def loaded_db(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("agents_db")
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


def test_intake_abstains_on_unresolved_visual_evidence(loaded_db):
    claim, _ = _claim_and_policy(loaded_db, "IMG_0001")
    result = run_intake(claim)
    assert result["action"] == "ESCALATE_VISUAL_REVIEW"
    assert result["damage"] == "UNRESOLVED"


def test_intake_structures_a_clean_claim(loaded_db):
    claim, _ = _claim_and_policy(loaded_db, "IMG_0002")
    result = run_intake(claim)
    assert result["action"] == "STRUCTURE_CLAIM"
    assert result["damage"] == "HEAD_LAMP"


def test_v2_adjudication_matches_oracle_exactly_when_proxies_stripped(loaded_db):
    claim, policy = _claim_and_policy(loaded_db, "CF_001_V1")
    result = run_adjudication(claim, policy, prohibited_fields=PROXY_FIELDS)
    assert result["decision"] == "APPROVE"
    assert result["payout"] == 13500.0
    assert not any(f in result["context_used"] for f in PROXY_FIELDS)


def test_v1_fairness_bug_reproduces_disparity_within_counterfactual_group(loaded_db):
    """
    The core 'wow' scenario (CLAUDE.md §13, §30): four claims in the same
    fairness counterfactual group hold every legitimate fact constant and
    vary only proxy fields. The deterministic oracle gives them all the
    same decision/payout. The v1 Adjudication Agent -- which still has
    proxy fields in its context -- must disagree with itself across at
    least one variant, reproducibly.
    """
    variant_ids = ["CF_001_V1", "CF_001_V2", "CF_001_V3", "CF_001_V4"]
    v1_outcomes = []
    for cid in variant_ids:
        claim, policy = _claim_and_policy(loaded_db, cid)
        result = run_adjudication(claim, policy)  # v1 default: no prohibited_fields
        v1_outcomes.append((result["decision"], result["payout"]))

    assert len(set(v1_outcomes)) > 1, "expected v1 to disagree with itself across matched variants"

    # Same run must be perfectly reproducible (deterministic, not random -- CLAUDE.md §29).
    for cid, expected in zip(variant_ids, v1_outcomes):
        claim, policy = _claim_and_policy(loaded_db, cid)
        result = run_adjudication(claim, policy)
        assert (result["decision"], result["payout"]) == expected


def test_v2_fairness_fix_makes_all_variants_agree(loaded_db):
    variant_ids = ["CF_001_V1", "CF_001_V2", "CF_001_V3", "CF_001_V4"]
    v2_outcomes = []
    for cid in variant_ids:
        claim, policy = _claim_and_policy(loaded_db, cid)
        result = run_adjudication(claim, policy, prohibited_fields=PROXY_FIELDS)
        v2_outcomes.append((result["decision"], result["payout"]))

    assert len(set(v2_outcomes)) == 1, "expected identical decision/payout once proxy fields are stripped"
    assert v2_outcomes[0] == ("APPROVE", 13500.0)


def test_v1_pipeline_bypasses_workflow_straight_to_customer_communication(loaded_db):
    claim, policy = _claim_and_policy(loaded_db, "IMG_0002")
    result = run_claim_pipeline(loaded_db, claim, policy, agent_version="v1")
    assert result["status"] == "COMMUNICATED_WITHOUT_VERIFICATION"
    assert result["explainability"] is None
    assert result["workflow_state"].current_step == "CUSTOMER_COMMUNICATION"


def test_v2_pipeline_requires_verified_explanation_before_communication(loaded_db):
    claim, policy = _claim_and_policy(loaded_db, "IMG_0002")
    result = run_claim_pipeline(loaded_db, claim, policy, agent_version="v2")
    assert result["status"] == "COMPLETED"
    assert result["explainability"]["citation_valid"] is True
    assert result["workflow_state"].explanation_verified is True


def test_v2_pipeline_blocks_communication_when_explanation_has_evidence_failure(loaded_db):
    all_claims = loaded_db.query(ClaimModel).all()
    target = next(c for c in all_claims if c.details.get("failure_injected") == "NONEXISTENT_CITATION")
    policy = loaded_db.query(PolicyModel).filter_by(policy_id=target.policy_id).one()

    result = run_claim_pipeline(loaded_db, target, policy, agent_version="v2")
    assert result["status"] == "BLOCKED_CUSTOMER_COMMUNICATION"


def test_pipeline_persists_trace_envelope_for_every_agent_call(loaded_db):
    claim, policy = _claim_and_policy(loaded_db, "IMG_0003")
    result = run_claim_pipeline(loaded_db, claim, policy, agent_version="v2", scenario_id=claim.claim_id)

    runs = loaded_db.query(AgentRunModel).filter_by(claim_id=claim.claim_id).all()
    agent_names = {r.agent_name for r in runs}
    assert {"intake", "adjudication", "explainability"} <= agent_names
    assert all(r.status == "completed" for r in runs)

    events = loaded_db.query(TraceEventModel).filter_by(claim_id=claim.claim_id).all()
    assert len(events) >= 3
    assert all(e.scenario_id == claim.claim_id for e in events)
    assert result["status"] == "COMPLETED"


def test_appeal_never_silently_changes_decision_without_new_evidence(loaded_db):
    claim, _ = _claim_and_policy(loaded_db, "IMG_0002")
    result = run_appeal(loaded_db, claim, previous_decision="APPROVE", has_new_evidence=False)
    assert result["decision_changed"] is False
    assert result["outcome"] == "DECISION_UNCHANGED"


def test_appeal_reassesses_with_material_new_evidence(loaded_db):
    claim, _ = _claim_and_policy(loaded_db, "IMG_0002")
    result = run_appeal(loaded_db, claim, previous_decision="DENY", has_new_evidence=True)
    assert result["decision_changed"] is True
    assert result["outcome"] == "REASSESSED"
