def test_load_demo_dataset_endpoint(client):
    response = client.post("/api/scenarios/load")
    assert response.status_code == 200
    data = response.json()
    assert data["oracle_check"]["mismatches"] == 0


def test_scenarios_list_after_load(client):
    client.post("/api/scenarios/load")
    response = client.get("/api/scenarios?limit=5")
    assert response.status_code == 200
    assert len(response.json()) == 5


def test_failures_scan_endpoint(client):
    client.post("/api/scenarios/load")
    response = client.post("/api/failures/scan?agent_version=v1&claim_sample_size=20")
    assert response.status_code == 200
    data = response.json()
    assert data["fairness_failures"] > 0


def test_abis_list_endpoint_compiles_on_demand(client):
    response = client.get("/api/abis")
    assert response.status_code == 200
    versions = [a["abi_version"] for a in response.json()]
    assert "fair_adjudication_v1" in versions
    assert "fair_workflow_v1" in versions


def test_hardening_results_endpoint(client):
    client.post("/api/scenarios/load")
    response = client.get("/api/hardening/results?agent_version=v1&enforced=false")
    assert response.status_code == 200
    data = response.json()
    assert "challenge_robustness" in data


def test_metrics_compute_endpoint(client):
    client.post("/api/scenarios/load")
    response = client.post("/api/metrics/compute?candidate_version=v2&enforced=true&sample_size=25")
    assert response.status_code == 200
    data = response.json()
    assert data["sample_size"] == 25


def test_gates_run_endpoint(client):
    client.post("/api/scenarios/load")
    response = client.post("/api/gates/run?candidate_version=v2")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("PASS", "BLOCKED")


def test_regressions_run_endpoint(client):
    client.post("/api/scenarios/load")
    response = client.post("/api/regressions/run?candidate_version=v2")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_graph_causal_endpoint_falls_back_to_sqlite(client):
    client.post("/api/scenarios/load")
    from app.db.session import SessionLocal
    from app.models.domain import ClaimModel, PolicyModel
    from app.agents.orchestrator import run_claim_pipeline

    db = SessionLocal()
    claim = db.query(ClaimModel).first()
    claim_id = claim.claim_id
    policy = db.query(PolicyModel).filter_by(policy_id=claim.policy_id).one()
    run_claim_pipeline(db, claim, policy, agent_version="v2", scenario_id=claim_id)
    db.close()

    response = client.get(f"/api/graph/causal/{claim_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "sqlite_fallback"
    assert len(data["nodes"]) >= 3


def test_execute_claim_pipeline_endpoint(client):
    client.post("/api/scenarios/load")
    response = client.post("/api/runs/execute?claim_id=IMG_0002&agent_version=v2&enforced=true")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["workflow_state"]["explanation_verified"] is True
