def test_list_sample_claims(client):
    client.post("/api/scenarios/load")
    response = client.get("/api/demo/claims")
    assert response.status_code == 200
    claims = response.json()
    assert len(claims) > 0
    assert "vehicle_make" in claims[0]
    assert "description" in claims[0]


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
