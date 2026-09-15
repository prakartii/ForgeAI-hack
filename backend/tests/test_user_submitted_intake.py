from app.agents.intake import run_intake
from app.models.domain import ClaimModel


def _user_claim(**overrides) -> ClaimModel:
    details = {
        "source": "user_submitted",
        "claim_description": "Someone hit my bumper in a parking lot.",
        "damage_part": "BUMPER",
        "damage_severity": "MEDIUM",
        "repair_estimate_inr": 15000,
        "has_photo": True,
        "required_evidence_complete": True,
    }
    details.update(overrides)
    return ClaimModel(claim_id="USER_TEST", policy_id="POL_USER_TEST", peril="COLLISION",
                       damage_type="DENT", verified_damage=0, evidence_status="pending",
                       proxy_variants={}, details=details)


def test_user_submitted_claim_with_photo_structures_normally():
    result = run_intake(_user_claim())
    assert result["action"] == "STRUCTURE_CLAIM"
    assert result["damage"] == "BUMPER"
    assert result["evidence_completeness"] == "complete"


def test_user_submitted_claim_without_photo_requests_one():
    result = run_intake(_user_claim(has_photo=False))
    assert result["action"] == "REQUEST_IMAGE_OR_ESCALATE"
    assert result["damage"] == "UNRESOLVED"


def test_user_submitted_claim_with_incomplete_evidence_escalates():
    result = run_intake(_user_claim(required_evidence_complete=False))
    assert result["action"] == "REQUEST_MISSING_EVIDENCE_OR_ESCALATE"
