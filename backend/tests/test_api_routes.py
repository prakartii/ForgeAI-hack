def test_api_agents_route(client):
    response = client.get("/api/agents")
    assert response.status_code == 200
    agents = response.json()
    assert len(agents) == 4
    agent_names = [a["name"] for a in agents]
    assert "IntakeAgent" in agent_names
    assert "AdjudicationAgent" in agent_names
    assert "ExplainabilityAgent" in agent_names
    assert "AppealsAgent" in agent_names


def test_api_scenarios_route(client):
    response = client.get("/api/scenarios")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_api_runs_route(client):
    response = client.get("/api/runs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_api_traces_route(client):
    response = client.get("/api/traces")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_api_failures_route(client):
    response = client.get("/api/failures")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_api_prism_status_route(client):
    response = client.get("/api/prism/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "base_url" in data


def test_api_abis_route(client):
    response = client.get("/api/abis")
    assert response.status_code == 200
    abis = response.json()
    assert isinstance(abis, list)
    # Should find fairness.yaml and workflow.yaml from abis directory
    abi_versions = [a.get("abi_version") for a in abis]
    assert "fair_adjudication_v1" in abi_versions
    assert "fair_workflow_v1" in abi_versions


def test_api_mutations_route(client):
    response = client.get("/api/mutations")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_api_hardening_route(client):
    response = client.get("/api/hardening/ladders")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


def test_api_regressions_route(client):
    response = client.get("/api/regressions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_api_metrics_route(client):
    response = client.get("/api/metrics")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_api_gates_route(client):
    response = client.get("/api/gates")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
