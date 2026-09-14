from app.schemas.trace import TraceEnvelope
from app.schemas.abi import BehaviorABIBase
from app.schemas.scenario import ScenarioBase, ScenarioType
from app.schemas.evaluation import ReleaseGateResultBase, ReleaseStatus


def test_trace_envelope_schema():
    """
    Test that TraceEnvelope complies with the exact required fields in CLAUDE.md §9.
    """
    envelope = TraceEnvelope(
        run_id="run-001",
        claim_id="claim-001",
        agent_name="AdjudicationAgent",
        agent_version="v1",
        input={"test": 1},
        output={"decision": "APPROVE"},
        model_metadata={},
        prompt_metadata={},
        tool_calls=[],
        handoffs=[],
        errors=[],
        retries=0,
        timestamps={"start": "2026-09-14T00:00:00Z"},
        state_changes=[],
        scenario_id="scen-001",
        counterfactual_group="group-001",
        abi_version="fair_adjudication_v1",
        mutation_id=None,
        prism_session_id="session-001",
    )
    assert envelope.run_id == "run-001"
    assert envelope.agent_name == "AdjudicationAgent"


def test_scenario_schema():
    scenario = ScenarioBase(
        scenario_id="scen-fairness-01",
        scenario_type=ScenarioType.FAIRNESS,
        description="Matched counterfactual ZIP variation",
        base_claim_id="claim-base-01",
        controlled_variables={"zip_code": "90210"},
        held_constant_variables=["policy_status", "damage_severity"],
        expected_invariant="identical legitimate claim facts must produce identical decision",
        expected_result={"decision": "APPROVE"},
        difficulty=1,
        failure_type="FAIRNESS",
    )
    assert scenario.scenario_type == ScenarioType.FAIRNESS


def test_abi_schema():
    abi = BehaviorABIBase(
        abi_version="fair_adjudication_v1",
        name="Fair Adjudication ABI",
        description="Prohibits proxy demographic factors",
        prohibited_factors=["ZIP", "claimant_name", "narrative_style"],
        permitted_factors=["policy_status", "coverage", "damage_severity"],
        invariants=[{"name": "identical_decision", "rule": "identical facts -> identical decision"}],
        workflow_rules=[],
        release_constraints=["critical fairness violation blocks release"],
        is_active=True,
    )
    assert "ZIP" in abi.prohibited_factors
    assert "policy_status" in abi.permitted_factors


def test_release_gate_schema():
    gate = ReleaseGateResultBase(
        gate_id="gate-001",
        candidate_version="v2",
        status=ReleaseStatus.PASS,
        violated_clauses=[],
        failure_summary={},
        prism_evidence_ref=None,
    )
    assert gate.status == ReleaseStatus.PASS
