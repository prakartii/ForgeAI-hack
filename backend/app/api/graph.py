from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.neo4j import Neo4jClient, get_neo4j_client
from app.db.session import get_db
from app.models.trace import TraceEventModel

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
    db: Session = Depends(get_db),
    client: Neo4jClient = Depends(get_neo4j_client),
) -> Dict[str, Any]:
    """
    Returns the causal execution graph for React Flow. Prefers the Neo4j
    projection; when Neo4j is not configured/reachable in this environment
    it falls back to building the same shape directly from SQLite's
    TraceEvent rows (CLAUDE.md §10/§5: SQLite is the authoritative system
    of record, Neo4j only a relationship projection over it), rather than
    showing an empty graph for a claim that actually ran.

    Each agent call gets its own AgentRun (CLAUDE.md §9: "one agent
    execution = one run"), so a claim run through the pipeline multiple
    times (e.g. once as v1, once as v2) has several separate causal
    chains. Edges only connect an event to the very next event recorded
    for the same agent_version, so re-running a claim never draws a
    nonsensical edge from one execution attempt into a different one.
    """
    neo4j_result = client.get_causal_graph(claim_id)
    if neo4j_result.get("nodes"):
        return neo4j_result

    events = (
        db.query(TraceEventModel)
        .filter_by(claim_id=claim_id)
        .order_by(TraceEventModel.id.asc())
        .all()
    )
    nodes = [
        {
            "id": e.event_id,
            "data": {
                "label": f"{e.agent_name} ({e.agent_version})",
                "handoffs": e.handoffs,
                "errors": e.errors,
            },
        }
        for e in events
    ]
    edges = []
    last_event_by_version: dict[str, TraceEventModel] = {}
    for event in events:
        previous = last_event_by_version.get(event.agent_version)
        if previous is not None:
            edges.append({"id": f"{previous.event_id}->{event.event_id}", "source": previous.event_id, "target": event.event_id})
        last_event_by_version[event.agent_version] = event

    return {"nodes": nodes, "edges": edges, "source": "sqlite_fallback" if events else "empty"}
