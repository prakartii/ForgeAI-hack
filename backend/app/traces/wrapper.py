"""
Common trace wrapper (CLAUDE.md §9).

Every agent and tool call passes through this wrapper. It is the single
place that writes the AgentRun + TraceEvent envelope to SQLite, so no
agent may call an LLM or tool without producing a traceable record.
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.trace import AgentRunModel, TraceEventModel

logger = logging.getLogger("failurefoundry.traces")


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
        submit_to_prism: bool = False,
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
        # Opt-in only (CLAUDE.md §21: budget trace volume) -- bulk callers
        # (metrics/hardening/regression, which run this across thousands of
        # claims) never pass this; only a single interactive claim run does.
        self.submit_to_prism = submit_to_prism
        self._run_row: Optional[AgentRunModel] = None
        self._events: list[TraceEventModel] = []

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
        self._events.append(event)
        return event

    def complete(self, status: str = "completed") -> None:
        assert self._run_row is not None
        self._run_row.status = status
        self.db.commit()

    def _try_submit_to_prism(self) -> None:
        """Best-effort, never raises: a PRISM outage must not break a claim
        run. Honest either way -- prism_session_id stays None on failure,
        never a fabricated id (CLAUDE.md §31)."""
        from app.prism import get_prism_client

        try:
            client = get_prism_client()
            if not client.is_configured or self._run_row is None:
                return
            trajectory_id = client.submit_agent_run(self._run_row, self._events)
            if trajectory_id:
                self._run_row.prism_session_id = trajectory_id
                self.db.commit()
        except Exception as e:  # pragma: no cover - defensive
            logger.warning(f"PRISM auto-submit failed for run {self.run_id}: {e}")

    def __exit__(self, exc_type, exc, tb) -> bool:
        self.complete("failed" if exc_type else "completed")
        if self.submit_to_prism:
            self._try_submit_to_prism()
        return False
