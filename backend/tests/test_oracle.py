from app.scenarios.oracle import evaluate_claim_oracle


def test_inactive_policy_denies():
    result = evaluate_claim_oracle(
        policy_active=False, peril="COLLISION", covered_perils=["COLLISION"],
        required_evidence_complete=True, verified_damage=10000, deductible=1000, coverage_limit=50000,
    )
    assert result.decision == "DENY"
    assert result.payout == 0.0
    assert result.reason == "POLICY_INACTIVE"


def test_excluded_peril_denies():
    result = evaluate_claim_oracle(
        policy_active=True, peril="FLOOD", covered_perils=["COLLISION", "FIRE"],
        required_evidence_complete=True, verified_damage=10000, deductible=1000, coverage_limit=50000,
    )
    assert result.decision == "DENY"
    assert result.reason == "PERIL_EXCLUDED"


def test_missing_evidence_escalates():
    result = evaluate_claim_oracle(
        policy_active=True, peril="COLLISION", covered_perils=["COLLISION"],
        required_evidence_complete=False, verified_damage=10000, deductible=1000, coverage_limit=50000,
    )
    assert result.decision == "ESCALATE"
    assert result.payout == 0.0


def test_approve_payout_is_capped_by_coverage_limit():
    result = evaluate_claim_oracle(
        policy_active=True, peril="COLLISION", covered_perils=["COLLISION"],
        required_evidence_complete=True, verified_damage=100000, deductible=5000, coverage_limit=50000,
    )
    assert result.decision == "APPROVE"
    assert result.payout == 50000.0


def test_approve_payout_matches_dataset_example():
    # CF_001_V1 from the demo dataset: verified_damage=21000, deductible=7500 -> payout=13500
    result = evaluate_claim_oracle(
        policy_active=True, peril="COLLISION", covered_perils=["COLLISION", "FIRE", "FLOOD"],
        required_evidence_complete=True, verified_damage=21000, deductible=7500, coverage_limit=150000,
    )
    assert result.decision == "APPROVE"
    assert result.payout == 13500.0
