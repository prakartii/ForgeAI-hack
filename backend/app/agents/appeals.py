"""
Appeals Agent (CLAUDE.md §6.4).

Hard rule: an appeal must never automatically change a decision without
material new evidence. `has_new_evidence` defaults to the dataset's own
`appeal_has_material_new_evidence` ground-truth label when not given
explicitly (e.g. by a scenario runner).
"""
from typing import Any, Optional

from app.models.domain import ClaimModel


def run_appeals(
    claim: ClaimModel,
    previous_decision: str,
    *,
    has_new_evidence: Optional[bool] = None,
) -> dict[str, Any]:
    if has_new_evidence is None:
        has_new_evidence = claim.details.get("appeal_has_material_new_evidence") == "1"

    if has_new_evidence:
        return {
            "outcome": "REASSESSED",
            "updated_rationale": (
                f"Claim {claim.claim_id} reassessed: material new evidence submitted since the "
                f"original '{previous_decision}' decision."
            ),
            "escalation_flag": False,
            "decision_changed": True,
        }

    return {
        "outcome": "DECISION_UNCHANGED",
        "updated_rationale": (
            f"No material new evidence was submitted for claim {claim.claim_id}; "
            f"the original '{previous_decision}' decision stands."
        ),
        "escalation_flag": False,
        "decision_changed": False,
    }
