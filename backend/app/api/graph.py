from typing import Dict, Any
from fastapi import APIRouter, Depends
from app.db.neo4j import get_neo4j_client, Neo4jClient

router = APIRouter(prefix="/graph", tags=["Graph & Causal Lineage"])


@router.get("/status", response_model=Dict[str, Any])
def graph_status(client: Neo4jClient = Depends(get_neo4j_client)) -> Dict[str, Any]:
    """
    Returns the operational status of the Neo4j graph and lineage projection layer.
    """
    return client.check_connection()


@router.get("/causal/{claim_id}", response_model=Dict[str, Any])
def get_causal_graph(
    claim_id: str,
    client: Neo4jClient = Depends(get_neo4j_client),
) -> Dict[str, Any]:
    """
    Returns the causal execution graph nodes and edges for React Flow visualization.
    """
    return client.get_causal_graph(claim_id)
