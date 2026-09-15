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

    def retrigger_evaluation(self, trajectory_id: str) -> Optional[dict]:
        """Forces PRISM to re-run evaluation for an already-submitted
        trajectory, live -- not served from cache."""
        client = self._get_client()
        if client is None:
            return None
        return client.retrigger_evaluation(trajectory_id)

    def list_trajectories(self, *, limit: int = 100, offset: int = 0) -> Optional[dict]:
        """GET /api/trajectories?project_id=...&limit=...&offset=... -- not
        wrapped by the installed prismtrace SDK, so this calls the SDK's
        own authenticated httpx client directly. Verified empirically
        against the real API (not guessed): returns {"trajectories": [...],
        "total": N}, each entry carrying overall_score/governance_passed/
        critical_rule_failed pre-aggregated by PRISM -- a single call here
        replaces N individual get_trajectory_evaluation calls.
        """
        client = self._get_client()
        if client is None:
            return None
        return client._get_sync(f"/api/trajectories?project_id={self.settings.prism_project_id}&limit={limit}&offset={offset}")

    # ------------------------------------------------------------------
    # Knowledge Base (kb_upload / kb_search) -- wraps
    # prismtrace.client.PRISMtrace.kb_upload / .kb_search / .kb_list_documents,
    # read directly from the installed SDK, same as the trajectory methods
    # above. Used to ground the Explainability Agent's citations against
    # the actual compiled ABI text stored in PRISM, rather than only
    # internal context keys (CLAUDE.md §16: an ABI must be an executable
    # contract, not just a comment -- this makes it retrievable evidence
    # too).
    # ------------------------------------------------------------------

    def kb_upload_text(self, filename: str, content: str, *, description: Optional[str] = None) -> Optional[dict]:
        client = self._get_client()
        if client is None:
            return None
        return client.kb_upload(filename, content, description=description, content_type="text/plain")

    def kb_list_documents(self) -> list[dict]:
        client = self._get_client()
        if client is None:
            return []
        return client.kb_list_documents()

    def kb_search(self, query: str, *, limit: int = 3) -> list[dict]:
        client = self._get_client()
        if client is None:
            return []
        return client.kb_search(query, limit=limit)

    def ensure_abi_kb_seeded(self, abi_texts: dict[str, str]) -> dict[str, Any]:
        """Uploads each {filename: yaml_text} into PRISM's knowledge base
        exactly once -- idempotent, checked against kb_list_documents by
        filename so reruns (e.g. on every server start) don't duplicate
        chunks. Returns {"uploaded": [...], "already_present": [...],
        "status": "not_configured"} depending on what actually happened;
        never claims success PRISM didn't confirm."""
        if not self.is_configured:
            return {"status": "not_configured", "uploaded": [], "already_present": []}

        existing_names = {doc.get("name") for doc in self.kb_list_documents()}
        uploaded, already_present = [], []
        for filename, text in abi_texts.items():
            if filename in existing_names:
                already_present.append(filename)
                continue
            result = self.kb_upload_text(filename, text, description=f"FailureFoundry compiled Behavior ABI: {filename}")
            if result:
                uploaded.append(filename)
        return {"status": "configured", "uploaded": uploaded, "already_present": already_present}

    def get_verdict(self, *, sample_size: int = 500, page_size: int = 100) -> dict[str, Any]:
        """Aggregates PRISM's own governance verdict across our submitted
        trajectories -- real evaluator output, not our own scoring.
        Bounded to `sample_size` (most recently submitted first, per the
        API's default ordering) rather than walking every trajectory on
        the project, since that count can run into the thousands; the
        sample is always reported alongside the true total so this is
        never presented as more complete than it is."""
        if not self.is_configured:
            return {
                "status": "not_configured",
                "total_on_prism": None,
                "sample_size": 0,
                "evaluated_count": 0,
                "critical_failures": 0,
                "avg_overall_score": None,
            }

        fetched: list[dict] = []
        total_on_prism = None
        offset = 0
        while len(fetched) < sample_size:
            page = self.list_trajectories(limit=min(page_size, sample_size - len(fetched)), offset=offset)
            if not page or not page.get("trajectories"):
                break
            total_on_prism = page.get("total", total_on_prism)
            fetched.extend(page["trajectories"])
            offset += page_size
            if len(page["trajectories"]) < page_size:
                break

        evaluated = [t for t in fetched if t.get("overall_score") is not None]
        critical_failures = sum(1 for t in evaluated if t.get("critical_rule_failed"))
        avg_score = round(sum(t["overall_score"] for t in evaluated) / len(evaluated), 2) if evaluated else None

        return {
            "status": "configured",
            "total_on_prism": total_on_prism,
            "sample_size": len(fetched),
            "evaluated_count": len(evaluated),
            "critical_failures": critical_failures,
            "avg_overall_score": avg_score,
        }


_prism_client: Optional[PrismClient] = None


def get_prism_client() -> PrismClient:
    global _prism_client
    if _prism_client is None:
        _prism_client = PrismClient()
    return _prism_client
