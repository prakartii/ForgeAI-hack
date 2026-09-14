import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
import app.models  # noqa: F401
from app.failures.scanner import scan_claims, scan_fairness_groups
from app.models.failure import FailureModel
from app.models.trace import AgentRunModel
from app.scenarios.csv_loader import load_dataset


@pytest.fixture(scope="module")
def loaded_db(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("failures_db")
    engine = create_engine(f"sqlite:///{tmp_path}/test.db")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    load_dataset(session)
    yield session
    session.close()


def test_v1_reproduces_fairness_failures_across_all_groups(loaded_db):
    failures = scan_fairness_groups(loaded_db, agent_version="v1")
    assert len(failures) > 0
    for f in failures:
        assert f.failure_type == "FAIRNESS"
        assert f.severity == "CRITICAL"
        assert f.diagnosis["pairwise_consistency"] == 0.0

    persisted = loaded_db.query(FailureModel).filter_by(failure_type="FAIRNESS").all()
    assert len(persisted) == len(failures)


def test_v2_eliminates_fairness_failures_after_enforcement(loaded_db):
    failures = scan_fairness_groups(loaded_db, agent_version="v2")
    assert failures == []


def test_workflow_bypass_is_detected_for_v1(loaded_db):
    result = scan_claims(loaded_db, ["IMG_0002"], agent_version="v1")
    assert len(result["WORKFLOW"]) == 1
    assert result["WORKFLOW"][0].failure_type == "WORKFLOW"
    assert result["WORKFLOW"][0].severity == "CRITICAL"


def test_workflow_bypass_is_absent_for_v2(loaded_db):
    result = scan_claims(loaded_db, ["IMG_0002"], agent_version="v2")
    assert result["WORKFLOW"] == []


def test_evidence_failure_detected_for_injected_nonexistent_citation(loaded_db):
    from app.models.domain import ClaimModel

    target = next(
        c for c in loaded_db.query(ClaimModel).all()
        if c.details.get("failure_injected") == "NONEXISTENT_CITATION"
    )
    result = scan_claims(loaded_db, [target.claim_id], agent_version="v2")
    assert len(result["EVIDENCE"]) == 1
    assert result["EVIDENCE"][0].diagnosis["failure_type_detail"] == "NONEXISTENT_CITATION"


def test_decision_correctness_matches_oracle_for_clean_claims(loaded_db):
    result = scan_claims(loaded_db, ["IMG_0002"], agent_version="v2")
    assert result["DECISION_CORRECTNESS"] == []


def test_failures_carry_a_real_run_id_that_resolves_to_an_agent_run(loaded_db):
    """
    A failure must be traceable back to the AgentRun that produced it
    (CLAUDE.md sec9's correlation model), so PRISM evidence submitted for
    that run can be found later via failure.run_id -> AgentRun.
    """
    fairness_failures = scan_fairness_groups(loaded_db, agent_version="v1")
    assert all(f.run_id for f in fairness_failures)
    for f in fairness_failures:
        run = loaded_db.query(AgentRunModel).filter_by(run_id=f.run_id).one()
        assert run.agent_name == "adjudication"

    workflow_result = scan_claims(loaded_db, ["IMG_0002"], agent_version="v1")
    workflow_failure = workflow_result["WORKFLOW"][0]
    assert workflow_failure.run_id is not None
    run = loaded_db.query(AgentRunModel).filter_by(run_id=workflow_failure.run_id).one()
    assert run.agent_name == "adjudication"
    assert run.claim_id == "IMG_0002"
