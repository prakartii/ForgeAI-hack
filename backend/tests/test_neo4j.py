from app.config.settings import get_settings
from app.db.neo4j import get_neo4j_client


def test_neo4j_settings():
    """
    Test that Neo4j configuration variables are present in Settings.
    """
    settings = get_settings()
    assert hasattr(settings, "neo4j_uri")
    assert hasattr(settings, "neo4j_user")
    assert hasattr(settings, "neo4j_password")
    assert hasattr(settings, "neo4j_database")


def test_neo4j_client_fallback_mode():
    """
    Test that Neo4j client operates safely in standby mode without throwing exceptions
    when credentials are not yet configured.
    """
    client = get_neo4j_client()
    status = client.check_connection()
    assert isinstance(status, dict)
    assert "status" in status
    assert status["status"] in ["standby", "connected", "unreachable", "unavailable"]


def test_api_graph_status_route(client):
    """
    Test GET /api/graph/status returns valid connection metadata.
    """
    response = client.get("/api/graph/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "uri" in data


def test_api_graph_causal_route(client):
    """
    Test GET /api/graph/causal/{claim_id} returns graph structure.
    """
    response = client.get("/api/graph/causal/claim-test-01")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
