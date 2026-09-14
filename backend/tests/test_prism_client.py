from app.models.trace import TraceEventModel
from app.prism.client import PrismClient


def test_prism_client_reports_not_configured_without_credentials():
    client = PrismClient()
    assert client.is_configured is False
    status = client.status()
    assert status["status"] == "not_configured"
    assert "PRISM_API_KEY" in status["message"]


def test_submit_agent_run_returns_none_when_not_configured():
    from app.models.trace import AgentRunModel

    client = PrismClient()
    run = AgentRunModel(run_id="run_1", claim_id="CLAIM_1", agent_name="intake", status="completed")
    assert client.submit_agent_run(run, []) is None


def test_fetch_evaluation_returns_none_when_not_configured():
    client = PrismClient()
    assert client.fetch_evaluation("some_trajectory_id") is None


def test_events_to_steps_marks_errors_as_failed_steps():
    event = TraceEventModel(
        event_id="evt_1",
        run_id="run_1",
        claim_id="CLAIM_1",
        agent_name="adjudication",
        agent_version="v1",
        input_payload={"a": 1},
        output_payload={"b": 2},
        errors=["something went wrong"],
    )
    steps = PrismClient._events_to_steps([event])
    assert steps[0]["status"] == "error"
    assert steps[0]["tool_name"] == "adjudication"
