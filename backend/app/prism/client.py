"""
PRISM adapter (CLAUDE.md §21).

Wraps the real, installed `prismtrace` SDK (package `blockconvey-monitor`,
version 0.3.1). The class name and method signatures below were read
directly from the installed package
(`prismtrace.client.PRISMtrace.submit_trajectory` /
`.get_trajectory_evaluation`), not guessed from documentation -- CLAUDE.md
§21 forbids inventing undocumented PRISM APIs.

One claim maps to one PRISM conversation (`conversation_id=claim_id`); one
FailureFoundry AgentRun maps to one PRISM trajectory built from that run's
TraceEvents. The trajectory id returned by PRISM is stored back onto the
AgentRun as `prism_session_id` so every run can be correlated with its
PRISM evidence.

No credentials are configured in this environment (PRISM_API_KEY /
PRISM_PROJECT_ID are unset in .env). Every method below degrades to a
clearly-labeled "not_configured" / None result rather than fabricating a
trajectory id, an evaluation score, or any other PRISM evidence --
CLAUDE.md §31: PRISM results must never be faked.
"""
import logging
from typing import Any, Optional

from app.config.settings import get_settings
from app.models.trace import AgentRunModel, TraceEventModel

logger = logging.getLogger("failurefoundry.prism")


class PrismClient:
    def __init__(self):
        self.settings = get_settings()
        self._client = None

    @property
    def is_configured(self) -> bool:
        return bool(self.settings.prism_api_key and self.settings.prism_project_id)

    def _get_client(self):
        if not self.is_configured:
            return None
        if self._client is not None:
            return self._client
        try:
            from prismtrace import PRISMtrace

            self._client = PRISMtrace(
                api_key=self.settings.prism_api_key,
                host=self.settings.prism_base_url,
                project_id=self.settings.prism_project_id,
            )
            return self._client
        except Exception as e:  # pragma: no cover - defensive, SDK not reachable
            logger.warning(f"PRISM client initialization failed: {e}")
            return None

    def status(self) -> dict[str, Any]:
        return {
            "status": "configured" if self.is_configured else "not_configured",
            "project_id": self.settings.prism_project_id if self.is_configured else None,
            "base_url": self.settings.prism_base_url,
            "message": (
                "PRISM client configured and reachable via prismtrace SDK v0.3.1"
                if self.is_configured
                else "PRISM_API_KEY / PRISM_PROJECT_ID not set: PRISM evidence is unavailable, "
                "not simulated. See CLAUDE.md sec21/sec31."
            ),
        }

    @staticmethod
    def _events_to_steps(events: list[TraceEventModel]) -> list[dict]:
        steps = []
        for event in events:
            steps.append(
                {
                    "step_type": "tool_call" if event.tool_calls else "reasoning",
                    "label": f"{event.agent_name} ({event.agent_version})",
                    "tool_name": event.agent_name,
                    "input_summary": str(event.input_payload)[:500],
                    "output_summary": str(event.output_payload)[:500],
                    "status": "error" if event.errors else "success",
                }
            )
        return steps

    def submit_agent_run(self, run: AgentRunModel, events: list[TraceEventModel]) -> Optional[str]:
        """
        Submits one AgentRun's trace events as a PRISM trajectory. Returns
        the trajectory id on success, or None if PRISM is not configured
        or the submission failed -- callers must treat None as "no PRISM
        evidence available," never assume success.
        """
        client = self._get_client()
        if client is None:
            return None

        response = client.submit_trajectory(
            steps=self._events_to_steps(events),
            agent_name=run.agent_name,
            conversation_id=run.claim_id,
            request_id=run.run_id,
            final_status="success" if run.status == "completed" else "error",
        )
        if not response:
            logger.warning(f"PRISM trajectory submission returned no result for run {run.run_id}")
            return None
        return response.get("id") or response.get("trajectory_id")

    def fetch_evaluation(self, trajectory_id: str) -> Optional[dict]:
        """Fetches PRISM's own evaluator result for a submitted trajectory."""
        client = self._get_client()
        if client is None:
            return None
        return client.get_trajectory_evaluation(trajectory_id)


_prism_client: Optional[PrismClient] = None


def get_prism_client() -> PrismClient:
    global _prism_client
    if _prism_client is None:
        _prism_client = PrismClient()
    return _prism_client
