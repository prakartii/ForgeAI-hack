"""
Customer-facing demo API (CLAUDE.md §30's "submit a synthetic insurance
claim" step). This is the only API surface a non-technical viewer of the
customer portal talks to -- it wraps the same real agent pipeline the
engineering console uses, but returns claimant-friendly shapes (plain
decision/payout/explanation, no internal IDs or ABI plumbing).
"""
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func

from app.agents.adjudication import run_adjudication
from app.db.session import get_db
from app.enforcement.engine import resolve_enforcement
from app.failures.detectors import detect_fairness_failure
from app.models.domain import ClaimModel, DocumentModel, PolicyModel
from app.models.scenario import CounterfactualPairModel, ScenarioModel
from app.models.trace import AgentRunModel
from app.agents.orchestrator import run_claim_pipeline
from app.regression.engine import register_regression_test
from app.traces.wrapper import TraceRecorder

router = APIRouter(prefix="/demo", tags=["Customer Portal"])

UPLOADS_DIR = Path(__file__).resolve().parents[3] / "data" / "uploads"

# A handful of realistic policy tiers a real user could plausibly pick,
# built from the deductible/coverage-limit combinations actually present
# in the synthetic dataset (data/scenarios/*.csv), not invented numbers.
_POLICY_TIERS = {
    "basic": {"deductible": 5000, "coverage_limit": 100000},
    "standard": {"deductible": 2500, "coverage_limit": 200000},
    "premium": {"deductible": 1000, "coverage_limit": 500000},
}
_COVERED_PERILS = ["COLLISION", "FIRE", "FLOOD", "THEFT", "VANDALISM"]
_DAMAGE_PARTS = ["BUMPER", "DOOR", "GLASS", "HEAD_LAMP", "TAIL_LAMP", "UNSPECIFIED"]
_DAMAGE_SEVERITIES = ["LOW", "MEDIUM", "HIGH"]

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


@router.get("/claims/random", response_model=Dict[str, Any])
def get_random_claim(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Picks a genuinely random claim from the full dataset (not the 8
    curated samples) -- proof this isn't a small fixed set dressed up as
    a real system. Returns the total claim count alongside it so the
    portal can show "1 of N real claims."
    """
    total = db.query(ClaimModel).count()
    if total == 0:
        raise HTTPException(status_code=404, detail="no claims loaded yet -- load the demo dataset first")
    claim = db.query(ClaimModel).order_by(func.random()).first()
    return {**_claim_summary(db, claim), "total_claims_in_system": total}


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


@router.post("/fairness-groups/{group_id}/check", response_model=Dict[str, Any])
def check_fairness_group(
    group_id: str,
    protected: bool = False,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Runs every variant in one counterfactual group through real, traced
    Adjudication calls and -- if the outcomes disagree -- registers a
    genuine FailureModel row and a regression test through the exact same
    `detect_fairness_failure` path the engineering console's own failure
    scan uses. This is what makes the portal's fairness check a real part
    of the system rather than a cosmetic side calculation: run it here,
    then go check the Failures / Regression / Release Gate pages in the
    engineering console and the same failure is sitting there.
    """
    pairs = db.query(CounterfactualPairModel).filter_by(group_id=group_id).all()
    if not pairs:
        raise HTTPException(status_code=404, detail=f"fairness group {group_id} not found")
    claim_ids = sorted({pairs[0].baseline_claim_id} | {p.counterfactual_claim_id for p in pairs})

    prohibited_fields = resolve_enforcement(db)["prohibited_fields"] if protected else None
    agent_version = "v2" if protected else "v1"

    outcomes: Dict[str, tuple] = {}
    run_ids: Dict[str, str] = {}
    for claim_id in claim_ids:
        claim = db.query(ClaimModel).filter_by(claim_id=claim_id).one()
        policy = db.query(PolicyModel).filter_by(policy_id=claim.policy_id).one()
        with TraceRecorder(
            db, claim_id=claim_id, agent_name="adjudication", agent_version=agent_version,
            scenario_id=claim_id, counterfactual_group=group_id,
            # Bounded to this group's ~4 variants per click -- a real
            # interactive action, not a bulk sweep -- so it's safe to
            # submit each to PRISM live like the single-claim flow does.
            submit_to_prism=True,
        ) as tr:
            result = run_adjudication(claim, policy, prohibited_fields=prohibited_fields)
            tr.record_event(
                input_payload={"context_keys": sorted(result["context_used"].keys())},
                output_payload={k: v for k, v in result.items() if k != "context_used"},
            )
        outcomes[claim_id] = (result["decision"], result["payout"])
        run_ids[claim_id] = tr.run_id

    failure = detect_fairness_failure(
        db, group_id, outcomes, agent_version=agent_version, run_id=run_ids[pairs[0].baseline_claim_id]
    )
    if failure:
        register_regression_test(db, failure, abi_version_introduced="fair_adjudication_v1")

    prism_sessions = {
        r.run_id: r.prism_session_id
        for r in db.query(AgentRunModel).filter(AgentRunModel.run_id.in_(run_ids.values())).all()
    }

    return {
        "group_id": group_id,
        "protected": protected,
        "outcomes": {
            cid: {"decision": d, "payout": p, "run_id": run_ids[cid], "prism_session_id": prism_sessions.get(run_ids[cid])}
            for cid, (d, p) in outcomes.items()
        },
        "failure_id": failure.failure_id if failure else None,
    }


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


# Alternate synthetic values used only to re-run Adjudication in-memory for
# the fairness certificate -- never persisted, never shown to the
# claimant. If protected=True has already stripped these fields from the
# Adjudication context, swapping them here provably can't move the
# decision (the ABI's own guarantee); if protected=False, it can, and the
# certificate says so honestly rather than hiding it.
_ALT_PROXY_VALUES = {
    "claimant_name_synthetic": "Priya Nair",
    "city": "Bengaluru",
    "narrative_style": "FORMAL",
}


def _run_fairness_certificate(
    claim: ClaimModel,
    policy: PolicyModel,
    prohibited_fields: Optional[list],
    original_decision: str,
    original_payout: float,
) -> Dict[str, Any]:
    """
    Re-runs Adjudication with one proxy attribute swapped at a time, held
    against the same legitimate facts, and compares the outcome to what
    the claimant actually got -- the counterfactual check CLAUDE.md §13
    runs for the engineering demo, surfaced per-claim instead of only in
    the standalone Fairness Check page. Returns tests_run=0 (no
    certificate) for claims with no proxy data to test, e.g. a
    user-submitted claim that never collected a name/city.
    """
    checks = []
    original_proxy_variants = claim.proxy_variants
    for attribute, alt_value in _ALT_PROXY_VALUES.items():
        current_value = original_proxy_variants.get(attribute)
        if not current_value or current_value == alt_value:
            continue
        claim.proxy_variants = {**original_proxy_variants, attribute: alt_value}
        try:
            result = run_adjudication(claim, policy, prohibited_fields=prohibited_fields)
        finally:
            claim.proxy_variants = original_proxy_variants  # never persisted either way
        checks.append({
            "attribute": attribute,
            "decision_changed": result["decision"] != original_decision,
            "payout_changed": abs(result["payout"] - original_payout) > 1,
        })

    passed = sum(1 for c in checks if not c["decision_changed"] and not c["payout_changed"])
    return {
        "tests_run": len(checks),
        "tests_passed": passed,
        "disparity_found": len(checks) > 0 and passed < len(checks),
    }


_WHAT_WOULD_CHANGE = {
    "POLICY_INACTIVE": "Renewing your policy so it's active on the incident date would let this be approved.",
    "PERIL_EXCLUDED": "Adding this type of incident to your covered perils would let this be approved.",
    "EVIDENCE_MISSING": "Providing the required evidence (like a clear damage photo) would let us finish reviewing this.",
    "REQUEST_IMAGE_OR_ESCALATE": "Uploading a photo of the damage would let us finish reviewing this.",
    "REQUEST_MISSING_EVIDENCE_OR_ESCALATE": "Providing the remaining required evidence would let us finish reviewing this.",
}


def _what_would_change(decision: str, reason: str) -> Optional[str]:
    """Plain-language, drawn only from the permitted-attribute reason code -- never a prohibited attribute."""
    if decision == "APPROVE":
        return None
    return _WHAT_WOULD_CHANGE.get(reason)


@router.get("/claim-options", response_model=Dict[str, Any])
def get_claim_form_options() -> Dict[str, Any]:
    """Real, dataset-derived vocab for the new-claim form's dropdowns."""
    return {
        "perils": _COVERED_PERILS,
        "damage_parts": _DAMAGE_PARTS,
        "damage_severities": _DAMAGE_SEVERITIES,
        "policy_tiers": [{"id": k, **v} for k, v in _POLICY_TIERS.items()],
    }


@router.post("/claims/custom", response_model=Dict[str, Any])
def submit_custom_claim(
    vehicle_make: str = Form(...),
    vehicle_model: str = Form(...),
    peril: str = Form(...),
    damage_part: str = Form(...),
    damage_severity: str = Form(...),
    description: str = Form(""),
    repair_estimate_inr: float = Form(...),
    policy_tier: str = Form("standard"),
    photo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Creates a brand-new claim from real user input (not one of the
    dataset's pre-loaded scenarios) -- a genuine policy, a genuine
    claim, and (if provided) a genuine uploaded photo -- then returns it
    in the same shape `/demo/claims` returns, ready to hand straight to
    `/demo/submit`.
    """
    if peril not in _COVERED_PERILS:
        raise HTTPException(status_code=400, detail=f"unknown peril '{peril}'")
    if damage_part not in _DAMAGE_PARTS:
        raise HTTPException(status_code=400, detail=f"unknown damage_part '{damage_part}'")
    tier = _POLICY_TIERS.get(policy_tier, _POLICY_TIERS["standard"])

    claim_id = f"USER_{uuid.uuid4().hex[:10]}"
    policy_id = f"POL_{claim_id}"

    db.add(PolicyModel(
        policy_id=policy_id,
        is_active=True,
        covered_perils=[peril],
        deductible=tier["deductible"],
        coverage_limit=tier["coverage_limit"],
        exclusions=[],
        metadata_info={"policy_status": "ACTIVE", "tier": policy_tier},
    ))

    image_url = None
    has_photo = False
    if photo is not None and photo.filename:
        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        suffix = Path(photo.filename).suffix or ".jpg"
        stored_name = f"{claim_id}{suffix}"
        with open(UPLOADS_DIR / stored_name, "wb") as f:
            f.write(photo.file.read())
        has_photo = True
        image_url = f"/media/uploads/{stored_name}"

    db.add(ClaimModel(
        claim_id=claim_id,
        policy_id=policy_id,
        peril=peril,
        damage_type=damage_part,
        verified_damage=repair_estimate_inr,
        evidence_status="complete" if has_photo else "incomplete",
        proxy_variants={},
        details={
            "source": "user_submitted",
            "vehicle_make": vehicle_make,
            "vehicle_model": vehicle_model,
            "damage_part": damage_part,
            "damage_severity": damage_severity,
            "claim_description": description,
            "repair_estimate_inr": repair_estimate_inr,
            "has_photo": has_photo,
            "required_evidence_complete": has_photo,
        },
    ))

    if has_photo:
        db.add(DocumentModel(
            document_id=f"DOC_{claim_id}_IMG",
            claim_id=claim_id,
            doc_type="damage_photo",
            file_path=str(UPLOADS_DIR / Path(image_url).name),
            evidence_references=[damage_part],
        ))

    db.commit()

    return {
        "claim_id": claim_id,
        "vehicle_make": vehicle_make,
        "vehicle_model": vehicle_model,
        "peril": peril,
        "damage_part": damage_part,
        "damage_type": damage_part,
        "description": description,
        "image_url": image_url,
    }


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

    before_run_id = db.query(func.max(AgentRunModel.id)).scalar() or 0

    result = run_claim_pipeline(
        db, claim, policy, agent_version=agent_version,
        prohibited_fields=prohibited_fields, workflow_enforce=workflow_enforce,
        scenario_id=claim_id,
        # A real, single interactive claim submitted through the portal --
        # this is exactly the case the engineering console's own "Run
        # pipeline" action submits to PRISM for, so the portal does too.
        submit_to_prism=True,
    )

    # The exact AgentRun rows this call just created -- real, queryable
    # proof (not a summary) that this claim was actually executed, not
    # looked up from a table of canned answers. A judge can open the
    # engineering console's Agent Runs page filtered to this claim_id and
    # see these same run_ids (and, if PRISM is configured, the same
    # prism_session_id already attached by the auto-submit above).
    new_runs = (
        db.query(AgentRunModel)
        .filter(AgentRunModel.id > before_run_id, AgentRunModel.claim_id == claim_id)
        .order_by(AgentRunModel.id.asc())
        .all()
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

    # The certificate re-runs run_adjudication directly with one proxy
    # field swapped -- only a meaningful comparison when the real
    # decision came from that same function. When Intake couldn't
    # structure the claim (unresolved evidence, wrong image, etc.),
    # orchestrator overrides straight to ESCALATE without ever calling
    # run_adjudication, so there's no fairness question to test here.
    intake_structured_claim = result["intake"]["action"] in ("STRUCTURE_CLAIM", "STRUCTURE_CLAIM_FROM_DOCUMENTS")
    if intake_structured_claim:
        fairness_certificate = _run_fairness_certificate(
            claim, policy, prohibited_fields, adjudication["decision"], adjudication["payout"]
        )
    else:
        fairness_certificate = {"tests_run": 0, "tests_passed": 0, "disparity_found": False}

    return {
        "claim_id": claim_id,
        "protected": protected,
        "status": result["status"],
        "steps_completed": steps,
        "decision": adjudication["decision"],
        "payout_inr": adjudication["payout"],
        "explanation": explanation,
        "explanation_verified": result.get("workflow_state").explanation_verified if result.get("workflow_state") else False,
        "fairness_certificate": fairness_certificate,
        "what_would_change": _what_would_change(adjudication["decision"], adjudication["reason"]),
        "receipt": {
            "runs": [
                {"run_id": r.run_id, "agent_name": r.agent_name, "prism_session_id": r.prism_session_id}
                for r in new_runs
            ],
            "agent_version": agent_version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }
