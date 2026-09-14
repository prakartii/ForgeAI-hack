def test_health_endpoint(client):
    """
    Test GET /health returns 200 with real status, app name, and connected database.
    """
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app"] == "FailureFoundry"
    assert data["version"] == "0.1.0"
    assert data["database"] == "connected"
    assert "timestamp" in data


def test_api_health_endpoint(client):
    """
    Test GET /api/health also returns 200.
    """
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_root_endpoint(client):
    """
    Test GET / returns root discovery metadata including locked lifecycle stages.
    """
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["app"] == "FailureFoundry"
    assert "lifecycle" in data
    assert "BUILD" in data["lifecycle"]
    assert "RELEASE GATE" in data["lifecycle"]
