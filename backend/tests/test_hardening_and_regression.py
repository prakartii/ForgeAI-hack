import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.abi.compiler import compile_fairness_abi
from app.db.base import Base
import app.models  # noqa: F401
from app.enforcement.engine import resolve_fairness_enforcement
from app.failures.scanner import scan_fairness_groups
from app.hardening.engine import run_hardening_ladder
from app.regression.engine import register_regression_test, run_regression_suite
from app.models.evaluation import RegressionTestModel
from app.scenarios.csv_loader import load_dataset


@pytest.fixture(scope="module")
def loaded_db(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("hardening_db")
    engine = create_engine(f"sqlite:///{tmp_path}/test.db")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    load_dataset(session)
    yield session
    session.close()


def test_v1_hardening_ladder_shows_failures_at_every_level(loaded_db):
    result = run_hardening_ladder(loaded_db, agent_version="v1")
    for level in ["L1", "L2", "L3", "L4"]:
        assert result["per_level"][level]["total"] == 25  # 25 fairness groups
    assert result["challenge_robustness"] < 1.0


def test_v2_enforced_hardening_ladder_passes_all_levels(loaded_db):
    compile_fairness_abi(loaded_db)
    enforcement = resolve_fairness_enforcement(loaded_db)
    result = run_hardening_ladder(loaded_db, agent_version="v2", prohibited_fields=enforcement.prohibited_fields)
    assert result["challenge_robustness"] == 1.0
    for level in ["L1", "L2", "L3", "L4"]:
        assert result["per_level"][level]["pass_rate"] == 1.0


def test_regression_test_is_registered_from_a_fairness_failure_and_persists(loaded_db):
    failures = scan_fairness_groups(loaded_db, agent_version="v1")
    assert failures
    test = register_regression_test(loaded_db, failures[0], abi_version_introduced="fair_adjudication_v1")
    assert test.failure_type == "FAIRNESS"
    assert test.still_passing is False  # not yet verified against a fix

    same = register_regression_test(loaded_db, failures[0], abi_version_introduced="fair_adjudication_v1")
    assert same.id == test.id  # idempotent


def test_regression_suite_flips_to_passing_once_enforcement_is_applied(loaded_db):
    enforcement = resolve_fairness_enforcement(loaded_db)
    results = run_regression_suite(
        loaded_db,
        candidate_version="v2",
        prohibited_fields=enforcement.prohibited_fields,
        workflow_enforce=True,
    )
    fairness_tests = [t for t in results if t.failure_type == "FAIRNESS"]
    assert fairness_tests
    assert all(t.still_passing for t in fairness_tests)
    assert all(t.last_tested_version == "v2" for t in fairness_tests)

    persisted = loaded_db.query(RegressionTestModel).filter_by(failure_type="FAIRNESS").all()
    assert all(t.still_passing for t in persisted)


def test_regression_suite_marks_source_failure_resolved_and_unresolved(loaded_db):
    from app.models.failure import FailureModel

    failures = scan_fairness_groups(loaded_db, agent_version="v1")
    test = register_regression_test(loaded_db, failures[0], abi_version_introduced="fair_adjudication_v1")

    enforcement = resolve_fairness_enforcement(loaded_db)
    run_regression_suite(loaded_db, candidate_version="v2", prohibited_fields=enforcement.prohibited_fields, workflow_enforce=True)
    failure = loaded_db.query(FailureModel).filter_by(failure_id=test.input_data["source_failure_id"]).one()
    assert failure.resolved is True

    run_regression_suite(loaded_db, candidate_version="v1", prohibited_fields=None, workflow_enforce=False)
    loaded_db.refresh(failure)
    assert failure.resolved is False


def test_regression_suite_would_catch_a_reintroduced_failure(loaded_db):
    # Rerun with the old, unprotected v1 configuration -- the regression
    # must fail again, proving the suite actually detects recurrence.
    results = run_regression_suite(loaded_db, candidate_version="v1", prohibited_fields=None, workflow_enforce=False)
    fairness_tests = [t for t in results if t.failure_type == "FAIRNESS"]
    assert any(not t.still_passing for t in fairness_tests)
