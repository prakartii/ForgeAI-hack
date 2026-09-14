"""
Hardening Engine (CLAUDE.md §11, §18).

Proves a fix generalizes rather than only patching one reproduced example.
The demo dataset already tags each fairness counterfactual variant with an
adversarial difficulty level (L1-L4, CLAUDE.md §18's ZIP -> +name ->
+narrative -> +multi-proxy ladder), so hardening here means: run every
group's variants under a given enforcement configuration and report the
pairwise-consistency pass rate at each level. A fix that only works for
one example shows up immediately as a level with a pass rate below 1.0.
"""
from collections import defaultdict
from typing import Optional

from sqlalchemy.orm import Session

from app.agents.adjudication import run_adjudication
from app.models.domain import ClaimModel, PolicyModel
from app.models.scenario import CounterfactualPairModel

LEVELS = ["L1", "L2", "L3", "L4"]


def run_hardening_ladder(
    db: Session,
    *,
    agent_version: str = "v1",
    prohibited_fields: Optional[list[str]] = None,
) -> dict:
    """
    For every fairness counterfactual group, checks whether its variants
    (each tagged with a hardening level) still agree with each other under
    the given adjudication configuration. Returns a per-level pass rate
    plus the overall challenge robustness score (CLAUDE.md §22).
    """
    group_ids = {row[0] for row in db.query(CounterfactualPairModel.group_id).distinct().all()}

    level_totals: dict[str, int] = defaultdict(int)
    level_passes: dict[str, int] = defaultdict(int)
    group_details = []

    for group_id in group_ids:
        pairs = db.query(CounterfactualPairModel).filter_by(group_id=group_id).all()
        claim_ids = {pairs[0].baseline_claim_id} | {p.counterfactual_claim_id for p in pairs}

        outcomes = {}
        levels_in_group = {}
        for claim_id in claim_ids:
            claim = db.query(ClaimModel).filter_by(claim_id=claim_id).one()
            policy = db.query(PolicyModel).filter_by(policy_id=claim.policy_id).one()
            result = run_adjudication(claim, policy, prohibited_fields=prohibited_fields)
            outcomes[claim_id] = (result["decision"], result["payout"])
            levels_in_group[claim_id] = claim.details.get("hardening_level") or "L1"

        consistent = len(set(outcomes.values())) == 1
        for claim_id, level in levels_in_group.items():
            level_totals[level] += 1
            if consistent:
                level_passes[level] += 1

        group_details.append({"group_id": group_id, "consistent": consistent, "outcomes": outcomes})

    per_level = {
        level: {
            "total": level_totals.get(level, 0),
            "passed": level_passes.get(level, 0),
            "pass_rate": (level_passes.get(level, 0) / level_totals[level]) if level_totals.get(level) else None,
        }
        for level in LEVELS
    }

    total = sum(level_totals.values())
    passed = sum(level_passes.values())
    return {
        "agent_version": agent_version,
        "per_level": per_level,
        "challenge_robustness": (passed / total) if total else None,
        "groups": group_details,
    }
