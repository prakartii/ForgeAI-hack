import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
import app.models  # noqa: F401  (registers all tables on Base.metadata)
from app.models.domain import ClaimModel, PolicyModel
from app.models.scenario import CounterfactualPairModel, ScenarioModel
from app.scenarios.csv_loader import DEFAULT_CSV_PATH, DEFAULT_IMAGES_DIR, load_dataset, verify_oracle_consistency


@pytest.fixture()
def db_session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path}/test_scenarios.db")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


def test_dataset_files_exist():
    assert DEFAULT_CSV_PATH.exists(), f"missing dataset CSV at {DEFAULT_CSV_PATH}"
    assert DEFAULT_IMAGES_DIR.exists(), f"missing images dir at {DEFAULT_IMAGES_DIR}"


def test_load_dataset_populates_all_object_types(db_session):
    summary = load_dataset(db_session)

    assert summary["policies"] == 2500
    assert summary["claims"] == 2500
    assert summary["scenarios"] == 2500
    assert summary["ground_truth"] == 2500
    assert summary["documents"] > 0
    # 25 fairness groups of 4 variants each -> 3 pairs per group
    assert summary["counterfactual_pairs"] == 75


def test_load_dataset_is_idempotent(db_session):
    load_dataset(db_session)
    second_summary = load_dataset(db_session)

    assert all(count == 0 for count in second_summary.values())
    assert db_session.query(ClaimModel).count() == 2500


def test_fairness_counterfactual_pairs_hold_legitimate_facts_constant(db_session):
    load_dataset(db_session)
    pair = db_session.query(CounterfactualPairModel).first()
    assert pair is not None

    baseline = db_session.query(ClaimModel).filter_by(claim_id=pair.baseline_claim_id).one()
    variant = db_session.query(ClaimModel).filter_by(claim_id=pair.counterfactual_claim_id).one()

    assert baseline.verified_damage == variant.verified_damage
    assert baseline.peril == variant.peril
    assert baseline.policy_id != variant.policy_id  # each row has its own synthetic policy record

    baseline_policy = db_session.query(PolicyModel).filter_by(policy_id=baseline.policy_id).one()
    variant_policy = db_session.query(PolicyModel).filter_by(policy_id=variant.policy_id).one()
    assert baseline_policy.deductible == variant_policy.deductible
    assert baseline_policy.coverage_limit == variant_policy.coverage_limit

    # proxy fields are exactly what changed between variants
    assert baseline.proxy_variants["synthetic_pin_code"] != variant.proxy_variants["synthetic_pin_code"]


def test_deterministic_oracle_matches_dataset_ground_truth(db_session):
    load_dataset(db_session)
    result = verify_oracle_consistency(db_session)

    assert result["checked"] > 0
    assert result["mismatches"] == []


def test_scenario_types_are_canonical(db_session):
    load_dataset(db_session)
    valid_types = {"FAIRNESS", "WORKFLOW", "EVIDENCE", "DECISION_CORRECTNESS", "HARDENING", "REGRESSION"}
    scenario_types = {s.scenario_type for s in db_session.query(ScenarioModel).all()}
    assert scenario_types <= valid_types
