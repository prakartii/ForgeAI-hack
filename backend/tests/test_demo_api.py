def test_list_sample_claims(client):
    client.post("/api/scenarios/load")
    response = client.get("/api/demo/claims")
    assert response.status_code == 200
    claims = response.json()
    assert len(claims) > 0
    assert "vehicle_make" in claims[0]
    assert "description" in claims[0]


def test_random_claim_is_not_limited_to_the_curated_list(client):
    client.post("/api/scenarios/load")
    curated = {c["claim_id"] for c in client.get("/api/demo/claims").json()}
    seen = set()
    for _ in range(15):
        claim = client.get("/api/demo/claims/random").json()
        # The shared test database may already hold extra user-submitted
        # claims from other tests/manual runs -- just confirm the real
        # dataset's 2,500 rows are present, not a suspiciously small number.
        assert claim["total_claims_in_system"] >= 2500
        seen.add(claim["claim_id"])
    assert seen - curated  # at least one random pick fell outside the curated 8


def test_list_fairness_groups(client):
    client.post("/api/scenarios/load")
    response = client.get("/api/demo/fairness-groups")
    assert response.status_code == 200
    groups = response.json()
    assert len(groups) == 25
    assert "label" in groups[0]


def test_get_fairness_group_variants(client):
    client.post("/api/scenarios/load")
    groups = client.get("/api/demo/fairness-groups").json()
    group_id = groups[0]["group_id"]
    response = client.get(f"/api/demo/fairness-groups/{group_id}/variants")
    assert response.status_code == 200
    variants = response.json()
    assert len(variants) == 4
    names = {v["claimant_name"] for v in variants}
    assert len(names) == 4  # each variant has a distinct claimant name


def test_fairness_check_registers_a_real_failure_when_unprotected(client):
    client.post("/api/scenarios/load")
    groups = client.get("/api/demo/fairness-groups").json()
    group_id = groups[0]["group_id"]

    unprotected = client.post(f"/api/demo/fairness-groups/{group_id}/check?protected=false").json()
    payouts = {v["payout"] for v in unprotected["outcomes"].values()}
    if len(payouts) > 1:
        assert unprotected["failure_id"] is not None
        failures = client.get("/api/failures").json()
        assert any(f["failure_id"] == unprotected["failure_id"] for f in failures)
        regressions = client.get("/api/regressions").json()
        assert any(r["input_data"].get("scenario_id") == group_id for r in regressions)


def test_fairness_check_finds_no_failure_when_protected(client):
    client.post("/api/scenarios/load")
    groups = client.get("/api/demo/fairness-groups").json()
    group_id = groups[0]["group_id"]

    protected = client.post(f"/api/demo/fairness-groups/{group_id}/check?protected=true").json()
    assert protected["failure_id"] is None
    payouts = {v["payout"] for v in protected["outcomes"].values()}
    assert len(payouts) == 1


def test_submit_claim_unprotected_vs_protected(client):
    client.post("/api/scenarios/load")
    groups = client.get("/api/demo/fairness-groups").json()
    variants = client.get(f"/api/demo/fairness-groups/{groups[0]['group_id']}/variants").json()
    claim_id = variants[0]["claim_id"]

    unprotected = client.post(f"/api/demo/submit?claim_id={claim_id}&protected=false").json()
    assert unprotected["decision"] in ("APPROVE", "DENY", "ESCALATE")
    assert unprotected["explanation"] is None  # v1 bypasses explanation

    protected = client.post(f"/api/demo/submit?claim_id={claim_id}&protected=true").json()
    assert protected["explanation_verified"] is True
    assert protected["explanation"] is not None
    assert claim_id not in protected["explanation"]  # no internal ids leaking into customer copy
    assert "APPROVE" not in protected["explanation"]  # plain English, not the raw enum value


def test_submit_unknown_claim_returns_404(client):
    response = client.post("/api/demo/submit?claim_id=NOT_A_REAL_CLAIM")
    assert response.status_code == 404


def test_claim_options_reflect_real_dataset_vocab(client):
    response = client.get("/api/demo/claim-options")
    assert response.status_code == 200
    options = response.json()
    assert "COLLISION" in options["perils"]
    assert len(options["policy_tiers"]) == 3


def test_submit_custom_claim_without_photo_escalates_for_missing_image(client):
    response = client.post(
        "/api/demo/claims/custom",
        data={
            "vehicle_make": "Tata",
            "vehicle_model": "Punch",
            "peril": "COLLISION",
            "damage_part": "BUMPER",
            "damage_severity": "MEDIUM",
            "description": "Someone hit my bumper in a parking lot.",
            "repair_estimate_inr": "15000",
            "policy_tier": "standard",
        },
    )
    assert response.status_code == 200
    claim = response.json()
    assert claim["claim_id"].startswith("USER_")
    assert claim["image_url"] is None

    result = client.post(f"/api/demo/submit?claim_id={claim['claim_id']}&protected=true").json()
    assert result["status"] == "COMPLETED"
    assert result["decision"] == "ESCALATE"  # no photo -> can't verify damage yet


def test_submit_custom_claim_with_photo_gets_approved(client, tmp_path):
    photo_path = tmp_path / "damage.jpg"
    photo_path.write_bytes(b"fake-jpeg-bytes")

    with open(photo_path, "rb") as photo_file:
        response = client.post(
            "/api/demo/claims/custom",
            data={
                "vehicle_make": "Hyundai",
                "vehicle_model": "Creta",
                "peril": "COLLISION",
                "damage_part": "DOOR",
                "damage_severity": "LOW",
                "description": "Scraped the door against a pillar.",
                "repair_estimate_inr": "8000",
                "policy_tier": "premium",
            },
            files={"photo": ("damage.jpg", photo_file, "image/jpeg")},
        )
    assert response.status_code == 200
    claim = response.json()
    assert claim["image_url"] == f"/media/uploads/{claim['claim_id']}.jpg"

    result = client.post(f"/api/demo/submit?claim_id={claim['claim_id']}&protected=true").json()
    assert result["status"] == "COMPLETED"
    assert result["decision"] == "APPROVE"
    assert result["payout_inr"] == 7000  # repair estimate (8000) minus the premium tier's 1000 deductible
    assert result["explanation"] is not None
