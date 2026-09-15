"""
Customer-facing demo API (CLAUDE.md §30's "submit a synthetic insurance
claim" step). This is the only API surface a non-technical viewer of the
customer portal talks to -- it wraps the same real agent pipeline the
engineering console uses, but returns claimant-friendly shapes (plain
decision/payout/explanation, no internal IDs or ABI plumbing).
"""
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.enforcement.engine import resolve_enforcement
from app.models.domain import ClaimModel, DocumentModel, PolicyModel
from app.models.scenario import CounterfactualPairModel, ScenarioModel
from app.agents.orchestrator import run_claim_pipeline

router = APIRouter(prefix="/demo", tags=["Customer Portal"])

# A hand-picked, diverse set of claims for the general "file a claim"
# picker: a mix of vehicle types and outcomes (clean approval, denial,
# escalation for missing evidence) so a first-time visitor sees the range
# of what the system handles, not just the happy path.
_CURATED_CLAIM_IDS = [
    "IMG_0002", "IMG_0010", "IMG_0025", "IMG_0031", "IMG_0044",
    "IMG_0057", "IMG_0063", "IMG_0078",
]


def _image_url(db: Session, claim_id: str) -> Optional[str]:
    doc = db.query(DocumentModel).filter_by(claim_id=claim_id, doc_type="damage_photo").one_or_none()
    if doc and doc.file_path:
        return f"/media/images/{Path(doc.file_path).name}"
    return None


def _claim_summary(db: Session, claim: ClaimModel) -> Dict[str, Any]:
    d = claim.details
    return {
        "claim_id": claim.claim_id,
        "vehicle_make": d.get("vehicle_make"),
        "vehicle_model": d.get("vehicle_model"),
        "peril": claim.peril,
        "damage_part": d.get("damage_part"),
        "damage_type": claim.damage_type,
        "description": d.get("claim_description"),
        "image_url": _image_url(db, claim.claim_id),
    }


@router.get("/claims", response_model=List[Dict[str, Any]])
def list_sample_claims(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """A curated, diverse picker list for the general claim-filing flow."""
    claims = db.query(ClaimModel).filter(ClaimModel.claim_id.in_(_CURATED_CLAIM_IDS)).all()
    by_id = {c.claim_id: c for c in claims}
    ordered = [by_id[cid] for cid in _CURATED_CLAIM_IDS if cid in by_id]
    return [_claim_summary(db, c) for c in ordered]


@router.get("/fairness-groups", response_model=List[Dict[str, Any]])
def list_fairness_groups(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """
    Lists every matched counterfactual group -- the same accident, told by
    different customers -- for the "compare as a different customer" demo.
    """
    group_ids = sorted({row[0] for row in db.query(CounterfactualPairModel.group_id).distinct().all()})
    results = []
    for group_id in group_ids:
        pair = db.query(CounterfactualPairModel).filter_by(group_id=group_id).first()
        claim = db.query(ClaimModel).filter_by(claim_id=pair.baseline_claim_id).one()
        d = claim.details
        results.append({
            "group_id": group_id,
            "label": (
                f"{d.get('vehicle_make')} {d.get('vehicle_model')} — "
                f"{(d.get('damage_part') or '').replace('_', ' ').lower()} ({claim.peril.lower()})"
            ),
            "image_url": _image_url(db, claim.claim_id),
        })
    return results


@router.get("/fairness-groups/{group_id}/variants", response_model=List[Dict[str, Any]])
def get_fairness_group_variants(group_id: str, db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Every customer variant in one matched group, with the proxy fields that differ."""
    pairs = db.query(CounterfactualPairModel).filter_by(group_id=group_id).all()
    if not pairs:
        raise HTTPException(status_code=404, detail=f"fairness group {group_id} not found")
    claim_ids = sorted({pairs[0].baseline_claim_id} | {p.counterfactual_claim_id for p in pairs})

    variants = []
    for claim_id in claim_ids:
        claim = db.query(ClaimModel).filter_by(claim_id=claim_id).one()
        pv = claim.proxy_variants
        variants.append({
            **_claim_summary(db, claim),
            "claimant_name": pv.get("claimant_name_synthetic"),
            "city": pv.get("city"),
            "state": pv.get("state"),
            "narrative_style": pv.get("narrative_style"),
        })
    return variants


_REASON_COPY = {
    "ELIGIBLE_CLAIM": "your policy was active and this type of damage is covered",
    "POLICY_INACTIVE": "your policy wasn't active on the date of the incident",
    "PERIL_EXCLUDED": "this type of incident isn't covered under your policy",
    "EVIDENCE_MISSING": "we're still waiting on some required evidence",
}


def _humanize_explanation(decision: str, reason: str, adjudication: Dict[str, Any]) -> str:
    """
    Builds a plain-English explanation for the claimant from the exact
    same facts the Adjudication agent used -- never inventing evidence,
    just writing it the way a person (not an audit log) reads it.
    """
    context = adjudication.get("context_used", {})
    why = _REASON_COPY.get(reason, reason.replace("_", " ").lower())

    if decision == "APPROVE":
        damage = context.get("verified_damage_inr")
        deductible = context.get("deductible_inr")
        parts = [f"We approved your claim because {why}."]
        if damage is not None and deductible is not None:
            parts.append(f"Your payout reflects the verified damage of ₹{damage:,.0f} minus your ₹{deductible:,.0f} deductible.")
        return " ".join(parts)
    if decision == "DENY":
        return f"We weren't able to approve this claim because {why}."
    return f"We've escalated this claim for a closer look because {why}."


@router.post("/submit", response_model=Dict[str, Any])
def submit_claim(
    claim_id: str,
    protected: bool = True,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Runs one claim through the real pipeline and returns a claimant-facing
    result. `protected=true` resolves whichever Behavior ABI is currently
    compiled and active (the "fixed" experience); `protected=false` runs
    the raw, unenforced v1 agent (the "before" experience) so the same
    portal can demonstrate both sides of the fix.
    """
    claim = db.query(ClaimModel).filter_by(claim_id=claim_id).one_or_none()
    if claim is None:
        raise HTTPException(status_code=404, detail=f"claim {claim_id} not found")
    policy = db.query(PolicyModel).filter_by(policy_id=claim.policy_id).one()

    if protected:
        enforcement = resolve_enforcement(db)
        prohibited_fields = enforcement["prohibited_fields"]
        workflow_enforce = enforcement["workflow_enforce"]
        agent_version = "v2"
    else:
        prohibited_fields = None
        workflow_enforce = False
        agent_version = "v1"

    result = run_claim_pipeline(
        db, claim, policy, agent_version=agent_version,
        prohibited_fields=prohibited_fields, workflow_enforce=workflow_enforce,
        scenario_id=claim_id,
    )

    steps = ["submitted", "reviewed"]
    if result["status"] == "COMMUNICATED_WITHOUT_VERIFICATION":
        steps += ["decided", "communicated"]
        explanation = None
    elif result["status"] == "BLOCKED_CUSTOMER_COMMUNICATION":
        steps += ["decided"]
        explanation = None
    else:
        steps += ["decided", "explained", "communicated"]
        explanation = _humanize_explanation(
            result["adjudication"]["decision"], result["adjudication"]["reason"], result["adjudication"]
        )

    adjudication = result["adjudication"]
    return {
        "claim_id": claim_id,
        "protected": protected,
        "status": result["status"],
        "steps_completed": steps,
        "decision": adjudication["decision"],
        "payout_inr": adjudication["payout"],
        "explanation": explanation,
        "explanation_verified": result.get("workflow_state").explanation_verified if result.get("workflow_state") else False,
    }
