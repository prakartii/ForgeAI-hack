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
from app.prism import get_prism_client
from app.scenarios.csv_loader import load_dataset


def _force_prism_unconfigured(monkeypatch):
    """
    Forces the shared PRISM client to report not_configured regardless of
    whatever real PRISM_API_KEY/PRISM_PROJECT_ID happen to be set in this
    environment's .env -- these tests assert behavior for the unconfigured
    case specifically, not the ambient dev environment's credentials.
    """
    client = get_prism_client()
    monkeypatch.setattr(client.settings, "prism_api_key", None)
    monkeypatch.setattr(client.settings, "prism_project_id", None)


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


def test_v1_metrics_show_real_fairness_and_workflow_gaps(loaded_db, monkeypatch):
    _force_prism_unconfigured(monkeypatch)
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


def test_release_gate_blocks_v2_only_on_missing_prism_evidence(loaded_db, monkeypatch):
    """
    Without PRISM credentials, the gate must legitimately block on that
    single clause rather than pretend evidence exists (CLAUDE.md
    sec23/sec31) -- every other clause should pass once enforcement is
    active. Forced unconfigured here since this environment may have real
    PRISM credentials in .env for manual end-to-end testing.
    """
    _force_prism_unconfigured(monkeypatch)
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


def test_release_gate_prism_clause_passes_when_credentials_are_real(loaded_db):
    """
    When real PRISM credentials are configured (e.g. during manual
    end-to-end testing against a live PRISM account), the prism_evidence
    clause must actually reflect that -- not just always report
    unconfigured. Skipped when no real credentials are present.
    """
    client = get_prism_client()
    if not client.is_configured:
        return

    enforcement = resolve_enforcement(loaded_db)
    metrics = compute_metrics(
        loaded_db,
        candidate_version="v2",
        prohibited_fields=enforcement["prohibited_fields"],
        workflow_enforce=enforcement["workflow_enforce"],
        claim_ids=_sample_claim_ids(loaded_db, n=5),
    )
    assert metrics["prism_evidence"]["status"] == "configured"
    result = evaluate_release_gate(loaded_db, candidate_version="v2", metrics=metrics)
    assert "prism_evidence" not in result.violated_clauses


def test_evidence_completeness_counts_a_blocked_bad_citation_as_complete(loaded_db):
    """
    ~50 claims in the demo dataset seed a deliberately invalid citation
    (NONEXISTENT_CITATION / UNSUPPORTED_POLICY_CLAUSE /
    RATIONALE_DECISION_CONTRADICTION) specifically so the explanation-
    verification checkpoint has something real to catch. Under v2 those
    are correctly BLOCKED_CUSTOMER_COMMUNICATION -- evidence_completeness
    must count that as the requirement being met (no bad explanation
    reached a customer), not as a violation, otherwise a full-dataset
    release-gate run can never reach 1.0 no matter how well v2 enforces
    the checkpoint (regression guard for a real bug hit live).
    """
    import json

    seeded_ids = [
        row[0]
        for row in loaded_db.query(ClaimModel.claim_id, ClaimModel.details).all()
        if row[1].get("failure_injected")
        in ("NONEXISTENT_CITATION", "UNSUPPORTED_POLICY_CLAUSE", "RATIONALE_DECISION_CONTRADICTION")
    ]
    assert seeded_ids  # the fixture dataset actually contains these

    enforcement = resolve_enforcement(loaded_db)
    metrics = compute_metrics(
        loaded_db,
        candidate_version="v2",
        prohibited_fields=enforcement["prohibited_fields"],
        workflow_enforce=enforcement["workflow_enforce"],
        claim_ids=seeded_ids,
    )
    assert metrics["evidence_completeness"] == 1.0


def test_release_gate_ignores_other_versions_unresolved_critical_failures(loaded_db, monkeypatch):
    """
    v1's own intentionally-injected weaknesses (CLAUDE.md sec29) leave
    unresolved CRITICAL failures in the table forever -- a v1 failure must
    never veto v2's gate just by sharing the table (regression guard for a
    real bug: the gate's critical-failure count wasn't scoped by
    candidate_version, so any accumulated v1 failure permanently blocked
    every later v2 evaluation).
    """
    from app.models.failure import FailureModel
    from app.traces.wrapper import new_id

    loaded_db.add(
        FailureModel(
            failure_id=new_id("fail"),
            failure_type="FAIRNESS",
            severity="CRITICAL",
            description="v1 fairness failure, never resolved",
            affected_agent="adjudication",
            diagnosis={"agent_version": "v1"},
            resolved=False,
        )
    )
    loaded_db.commit()

    from app.config import settings as settings_module

    monkeypatch.setattr(settings_module.get_settings(), "prism_evidence_required", False)
    enforcement = resolve_enforcement(loaded_db)
    metrics = compute_metrics(
        loaded_db,
        candidate_version="v2",
        prohibited_fields=enforcement["prohibited_fields"],
        workflow_enforce=enforcement["workflow_enforce"],
        claim_ids=_sample_claim_ids(loaded_db),
    )
    result = evaluate_release_gate(loaded_db, candidate_version="v2", metrics=metrics)
    assert "critical_abi_violations" not in result.violated_clauses


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
