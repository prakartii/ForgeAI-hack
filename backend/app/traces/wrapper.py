"""
Common trace wrapper (CLAUDE.md §9).

Every agent and tool call passes through this wrapper. It is the single
place that writes the AgentRun + TraceEvent envelope to SQLite, so no
agent may call an LLM or tool without producing a traceable record.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.trace import AgentRunModel, TraceEventModel


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class TraceRecorder:
    """
    Records one AgentRun and its TraceEvents. Used as a context manager so
    the run's terminal status (completed/failed) is always recorded, even
    if the agent raises.
    """

    def __init__(
        self,
        db: Session,
        *,
        claim_id: str,
        agent_name: str,
        agent_version: str,
        scenario_id: Optional[str] = None,
        counterfactual_group: Optional[str] = None,
        abi_version: Optional[str] = None,
        mutation_id: Optional[str] = None,
        prism_session_id: Optional[str] = None,
    ):
        self.db = db
        self.run_id = new_id("run")
        self.claim_id = claim_id
        self.agent_name = agent_name
        self.agent_version = agent_version
        self.scenario_id = scenario_id
        self.counterfactual_group = counterfactual_group
        self.abi_version = abi_version
        self.mutation_id = mutation_id
        self.prism_session_id = prism_session_id
        self._run_row: Optional[AgentRunModel] = None

    def __enter__(self) -> "TraceRecorder":
        self._run_row = AgentRunModel(
            run_id=self.run_id,
            claim_id=self.claim_id,
            agent_name=self.agent_name,
            agent_version=self.agent_version,
            scenario_id=self.scenario_id,
            counterfactual_group=self.counterfactual_group,
            abi_version=self.abi_version,
            mutation_id=self.mutation_id,
            prism_session_id=self.prism_session_id,
            status="running",
        )
        self.db.add(self._run_row)
        self.db.commit()
        return self

    def record_event(
        self,
        *,
        input_payload: dict[str, Any],
        output_payload: dict[str, Any],
        tool_calls: Optional[list[dict[str, Any]]] = None,
        handoffs: Optional[list[dict[str, Any]]] = None,
        errors: Optional[list[str]] = None,
        state_changes: Optional[list[dict[str, Any]]] = None,
        model_metadata: Optional[dict[str, Any]] = None,
        prompt_metadata: Optional[dict[str, Any]] = None,
    ) -> TraceEventModel:
        event = TraceEventModel(
            event_id=new_id("evt"),
            run_id=self.run_id,
            claim_id=self.claim_id,
            agent_name=self.agent_name,
            agent_version=self.agent_version,
            input_payload=input_payload,
            output_payload=output_payload,
            model_metadata=model_metadata or {},
            prompt_metadata=prompt_metadata or {},
            tool_calls=tool_calls or [],
            handoffs=handoffs or [],
            errors=errors or [],
            retries=0,
            timestamps={"recorded_at": datetime.now(timezone.utc).isoformat()},
            state_changes=state_changes or [],
            scenario_id=self.scenario_id,
            counterfactual_group=self.counterfactual_group,
            abi_version=self.abi_version,
            mutation_id=self.mutation_id,
            prism_session_id=self.prism_session_id,
        )
        self.db.add(event)
        self.db.commit()
        return event

    def complete(self, status: str = "completed") -> None:
        assert self._run_row is not None
        self._run_row.status = status
        self.db.commit()

    def __exit__(self, exc_type, exc, tb) -> bool:
        self.complete("failed" if exc_type else "completed")
        return False
