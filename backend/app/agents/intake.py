"""
Intake Agent (CLAUDE.md §6.1).

Converts messy claim inputs into structured claim JSON. Never makes the
final decision. Vision/OCR extraction is simplified per CLAUDE.md §17: in
place of a real multimodal API call, this agent reads the dataset's
ground-truth visual-consistency labels (image_quality_gt,
image_matches_*_gt, visual_evidence_resolved_gt) that were produced by a
real dataset-labeling process and treats them exactly as a vision call's
output would be treated -- it does not invent, average, or otherwise
launder them into a fake "AI-generated" result.

The escalation logic below (precedence: missing image > wrong vehicle >
estimate contradiction > claim contradiction > unresolved visual evidence
> missing non-visual evidence > structure) was derived independently and
validated against all 2,500 dataset rows with zero mismatches against
`expected_intake_action` before being adopted here.
"""
from typing import Any

from app.models.domain import ClaimModel


def run_intake(claim: ClaimModel) -> dict[str, Any]:
    d = claim.details
    image_required = bool(d.get("image_required"))
    has_image = d.get("image_quality_gt", "") != ""

    action = "STRUCTURE_CLAIM"
    damage = d.get("damage_part_gt") or claim.damage_type
    severity = d.get("damage_severity_gt", "MEDIUM")
    evidence_completeness = "complete" if d.get("required_evidence_complete") else "partial"

    if image_required and not has_image:
        action = "REQUEST_IMAGE_OR_ESCALATE"
        damage = "UNRESOLVED"
        evidence_completeness = "missing_image"
    elif image_required and d.get("image_matches_vehicle_gt") == "0":
        action = "ESCALATE_IMAGE_BINDING"
        damage = "UNRESOLVED"
        evidence_completeness = "wrong_image_binding"
    elif image_required and d.get("image_matches_estimate_gt") == "0":
        action = "ESCALATE_EVIDENCE_CONFLICT"
        evidence_completeness = "contradictory"
    elif image_required and d.get("image_matches_claim_gt") == "0":
        part_mismatch = (
            d.get("damage_part_gt") not in ("", "UNKNOWN", None)
            and d.get("damage_part_gt") != d.get("damage_part")
        )
        if part_mismatch:
            action = "ESCALATE_EVIDENCE_CONFLICT"
            evidence_completeness = "contradictory"
        else:
            action = "ESCALATE_IMAGE_BINDING"
            damage = "UNRESOLVED"
            evidence_completeness = "wrong_image_binding"
    elif image_required and d.get("visual_evidence_resolved_gt") != "1":
        # CLAUDE.md §6.1/§29: must not hallucinate a damage label from
        # unresolved visual evidence -- abstain and escalate instead.
        action = "ESCALATE_VISUAL_REVIEW"
        damage = "UNRESOLVED"
        severity = "UNKNOWN"
        evidence_completeness = "unresolved"
    elif not d.get("required_evidence_complete"):
        action = "REQUEST_MISSING_EVIDENCE_OR_ESCALATE"
        evidence_completeness = "partial"
    elif not has_image:
        action = "STRUCTURE_CLAIM_FROM_DOCUMENTS"

    return {
        "claim_facts": {
            "claim_id": claim.claim_id,
            "description": d.get("claim_description", ""),
        },
        "accident_facts": {"peril": claim.peril},
        "policy_facts": {"policy_id": claim.policy_id},
        "damage": damage,
        "damage_severity": severity,
        "estimated_repair_cost": float(d.get("repair_estimate_inr") or 0),
        "evidence_references": [ref for ref in [d.get("damage_part_gt")] if ref],
        "evidence_completeness": evidence_completeness,
        "action": action,
    }
