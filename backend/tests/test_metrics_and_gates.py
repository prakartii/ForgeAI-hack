import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.abi.compiler import compile_fairness_abi, compile_workflow_abi
from app.db.base import Base
import app.models  # noqa: F401
from app.enforcement.engine import resolve_enforcement
from app.gates.engine import evaluate_release_gate
from app.metrics.engine import compute_metrics
from app.models.domain import ClaimModel
from app.scenarios.csv_loader import load_dataset


@pytest.fixture(scope="module")
def loaded_db(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("metrics_db")
    engine = create_engine(f"sqlite:///{tmp_path}/test.db")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    load_dataset(session)
    compile_fairness_abi(session)
    compile_workflow_abi(session)
    yield session
    session.close()


def _sample_claim_ids(db, n=150):
    return [row[0] for row in db.query(ClaimModel.claim_id).limit(n).all()]


def test_v1_metrics_show_real_fairness_and_workflow_gaps(loaded_db):
    metrics = compute_metrics(
        loaded_db,
        candidate_version="v1",
        prohibited_fields=None,
        workflow_enforce=False,
        claim_ids=_sample_claim_ids(loaded_db),
    )
    assert metrics["pairwise_consistency"] < 1.0
    assert metrics["workflow_compliance"] < 1.0
    assert metrics["prism_evidence"]["status"] == "not_configured"


def test_v2_enforced_metrics_show_full_fairness_and_workflow_compliance(loaded_db):
    enforcement = resolve_enforcement(loaded_db)
    metrics = compute_metrics(
        loaded_db,
        candidate_version="v2",
        prohibited_fields=enforcement["prohibited_fields"],
        workflow_enforce=enforcement["workflow_enforce"],
        claim_ids=_sample_claim_ids(loaded_db),
    )
    assert metrics["pairwise_consistency"] == 1.0
    assert metrics["workflow_compliance"] == 1.0
    assert metrics["challenge_robustness"] == 1.0


def test_release_gate_blocks_v1_for_fairness_and_workflow_violations(loaded_db):
    metrics = compute_metrics(
        loaded_db, candidate_version="v1", prohibited_fields=None, workflow_enforce=False,
        claim_ids=_sample_claim_ids(loaded_db),
    )
    result = evaluate_release_gate(loaded_db, candidate_version="v1", metrics=metrics)
    assert result.status == "BLOCKED"
    assert "fairness_threshold" in result.violated_clauses
    assert "workflow_compliance" in result.violated_clauses


def test_release_gate_blocks_v2_only_on_missing_prism_evidence(loaded_db):
    """
    With no PRISM credentials configured in this environment, the gate
    must legitimately block on that single clause rather than pretend
    evidence exists (CLAUDE.md §23/§31) -- every other clause should pass
    once enforcement is active.
    """
    enforcement = resolve_enforcement(loaded_db)
    metrics = compute_metrics(
        loaded_db,
        candidate_version="v2",
        prohibited_fields=enforcement["prohibited_fields"],
        workflow_enforce=enforcement["workflow_enforce"],
        claim_ids=_sample_claim_ids(loaded_db),
    )
    result = evaluate_release_gate(loaded_db, candidate_version="v2", metrics=metrics)
    assert result.violated_clauses == ["prism_evidence"]
    assert result.status == "BLOCKED"


def test_release_gate_passes_v2_when_prism_evidence_not_required(loaded_db, monkeypatch):
    from app.config import settings as settings_module

    settings = settings_module.get_settings()
    monkeypatch.setattr(settings, "prism_evidence_required", False)

    enforcement = resolve_enforcement(loaded_db)
    metrics = compute_metrics(
        loaded_db,
        candidate_version="v2",
        prohibited_fields=enforcement["prohibited_fields"],
        workflow_enforce=enforcement["workflow_enforce"],
        claim_ids=_sample_claim_ids(loaded_db),
    )
    result = evaluate_release_gate(loaded_db, candidate_version="v2", metrics=metrics)
    assert result.status == "PASS"
    assert result.violated_clauses == []
