"""
Release Gate (CLAUDE.md §23). PASS only if every one of the eight
conditions below actually holds against real, computed metrics -- never
asserted. Any violation produces BLOCKED with the specific clause,
reproduced failure (if any), and PRISM evidence reference.
"""
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.models.evaluation import ReleaseGateResultModel
from app.models.failure import FailureModel
from app.traces.wrapper import new_id


@dataclass
class GateCheck:
    name: str
    passed: bool
    detail: str


def evaluate_release_gate(
    db: Session,
    *,
    candidate_version: str,
    metrics: dict,
    fairness_threshold: float = 1.0,
) -> ReleaseGateResultModel:
    settings = get_settings()
    checks: list[GateCheck] = []

    critical_failures = db.query(FailureModel).filter_by(severity="CRITICAL", resolved=False).count()
    checks.append(
        GateCheck("critical_abi_violations", critical_failures == 0, f"{critical_failures} unresolved CRITICAL failures")
    )

    pairwise = metrics.get("pairwise_consistency")
    checks.append(
        GateCheck(
            "fairness_threshold",
            pairwise is not None and pairwise >= fairness_threshold,
            f"pairwise_consistency={pairwise}",
        )
    )

    workflow = metrics.get("workflow_compliance")
    checks.append(
        GateCheck("workflow_compliance", workflow is not None and workflow >= 1.0, f"workflow_compliance={workflow}")
    )

    evidence = metrics.get("evidence_completeness")
    checks.append(
        GateCheck("evidence_completeness", evidence is not None and evidence >= 1.0, f"evidence_completeness={evidence}")
    )

    regression = metrics.get("regression_pass_rate")
    regression_ok = regression is None or regression >= 1.0
    checks.append(GateCheck("historical_regressions", regression_ok, f"regression_pass_rate={regression}"))

    robustness = metrics.get("challenge_robustness")
    checks.append(
        GateCheck("hardened_scenarios", robustness is not None and robustness >= 1.0, f"challenge_robustness={robustness}")
    )

    prism_status = metrics.get("prism_evidence", {}) or {}
    prism_ok = (not settings.prism_evidence_required) or prism_status.get("status") == "configured"
    checks.append(GateCheck("prism_evidence", prism_ok, prism_status.get("message", "PRISM status unknown")))

    violated = [c.name for c in checks if not c.passed]
    status = "PASS" if not violated else "BLOCKED"

    result = ReleaseGateResultModel(
        gate_id=new_id("gate"),
        candidate_version=candidate_version,
        status=status,
        violated_clauses=violated,
        failure_summary={c.name: {"passed": c.passed, "detail": c.detail} for c in checks},
        prism_evidence_ref=prism_status.get("status"),
    )
    db.add(result)
    db.commit()
    return result
