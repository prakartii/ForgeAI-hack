import logging
from typing import Optional, Dict, Any, List
from app.config.settings import get_settings

logger = logging.getLogger("failurefoundry.neo4j")


class Neo4jClient:
    """
    Neo4j Graph Database Client for FailureFoundry.
    Implements the Causal Execution and Behavioral Lineage layer (CLAUDE.md §5 & §10).
    Polyglot Persistence: SQLite is the primary system of record;
    Neo4j serves as the relationship, causality, and failure-to-ABI graph projection.
    """

    def __init__(self):
        self.settings = get_settings()
        self._driver = None

    def _get_driver(self):
        """
        Lazily initializes the Neo4j driver with configured credentials.
        """
        if self._driver is not None:
            return self._driver

        if not self.settings.neo4j_password:
            # Standby mode: credentials not yet provided
            return None

        try:
            from neo4j import GraphDatabase
            auth = (self.settings.neo4j_user or "neo4j", self.settings.neo4j_password)
            self._driver = GraphDatabase.driver(
                self.settings.neo4j_uri or "bolt://localhost:7687",
                auth=auth,
            )
            return self._driver
        except Exception as e:
            logger.warning(f"Neo4j driver initialization failed: {e}")
            return None

    def check_connection(self) -> Dict[str, Any]:
        """
        Verifies active connectivity to the Neo4j graph cluster.
        Returns a structured status dictionary without throwing uncaught exceptions.
        """
        if not self.settings.neo4j_password:
            return {
                "status": "standby",
                "configured": False,
                "uri": self.settings.neo4j_uri,
                "database": self.settings.neo4j_database,
                "message": "Neo4j credentials not configured in .env; SQLite active as primary system of record.",
            }

        driver = self._get_driver()
        if not driver:
            return {
                "status": "unavailable",
                "configured": True,
                "uri": self.settings.neo4j_uri,
                "database": self.settings.neo4j_database,
                "message": "Failed to create Neo4j driver.",
            }

        try:
            driver.verify_connectivity()
            return {
                "status": "connected",
                "configured": True,
                "uri": self.settings.neo4j_uri,
                "database": self.settings.neo4j_database,
                "message": "Connected to Neo4j graph instance.",
            }
        except Exception as e:
            return {
                "status": "unreachable",
                "configured": True,
                "uri": self.settings.neo4j_uri,
                "database": self.settings.neo4j_database,
                "message": f"Neo4j connection error: {str(e)}",
            }

    def sync_execution_node(
        self,
        claim_id: str,
        agent_name: str,
        agent_version: str,
        event_id: str,
        event_type: str = "EXECUTION",
        parent_event_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Projects an execution event into the Neo4j causal graph.
        Creates (:Claim), (:Agent), and (:Event) nodes and causal relationships.
        """
        driver = self._get_driver()
        if not driver:
            return False

        query = """
        MERGE (c:Claim {claim_id: $claim_id})
        MERGE (a:Agent {name: $agent_name, version: $agent_version})
        CREATE (e:Event {
            event_id: $event_id,
            event_type: $event_type
        })
        CREATE (a)-[:EXECUTED]->(e)
        CREATE (e)-[:ON_CLAIM]->(c)
        """
        params = {
            "claim_id": claim_id,
            "agent_name": agent_name,
            "agent_version": agent_version,
            "event_id": event_id,
            "event_type": event_type,
        }

        try:
            with driver.session(database=self.settings.neo4j_database) as session:
                session.run(query, params)
                if parent_event_id:
                    link_query = """
                    MATCH (parent:Event {event_id: $parent_event_id})
                    MATCH (child:Event {event_id: $child_event_id})
                    MERGE (parent)-[:PRECEDED]->(child)
                    """
                    session.run(link_query, {
                        "parent_event_id": parent_event_id,
                        "child_event_id": event_id,
                    })
            return True
        except Exception as e:
            logger.warning(f"Failed to sync execution event to Neo4j: {e}")
            return False

    def sync_failure_lineage(
        self,
        failure_id: str,
        failure_type: str,
        affected_agent: str,
        scenario_id: Optional[str] = None,
        abi_version: Optional[str] = None,
    ) -> bool:
        """
        Projects a diagnosed failure and compiled Behavior ABI lineage into Neo4j.
        """
        driver = self._get_driver()
        if not driver:
            return False

        query = """
        MERGE (a:Agent {name: $affected_agent})
        CREATE (f:Failure {
            failure_id: $failure_id,
            failure_type: $failure_type,
            scenario_id: $scenario_id
        })
        CREATE (a)-[:TRIGGERED]->(f)
        """
        params = {
            "affected_agent": affected_agent,
            "failure_id": failure_id,
            "failure_type": failure_type,
            "scenario_id": scenario_id or "unspecified",
        }

        try:
            with driver.session(database=self.settings.neo4j_database) as session:
                session.run(query, params)
                if abi_version:
                    abi_query = """
                    MATCH (f:Failure {failure_id: $failure_id})
                    MERGE (abi:BehaviorABI {abi_version: $abi_version})
                    MERGE (f)-[:COMPILED_INTO]->(abi)
                    """
                    session.run(abi_query, {
                        "failure_id": failure_id,
                        "abi_version": abi_version,
                    })
            return True
        except Exception as e:
            logger.warning(f"Failed to sync failure lineage to Neo4j: {e}")
            return False

    def get_causal_graph(self, claim_id: str) -> Dict[str, Any]:
        """
        Retrieves graph nodes and edges for React Flow rendering.
        """
        driver = self._get_driver()
        if not driver:
            return {"nodes": [], "edges": [], "source": "empty_standby"}

        query = """
        MATCH (c:Claim {claim_id: $claim_id})<-[:ON_CLAIM]-(e:Event)<-[:EXECUTED]-(a:Agent)
        OPTIONAL MATCH (e)<-[:PRECEDED]-(prev:Event)
        RETURN e.event_id AS id, e.event_type AS type, a.name AS agent, prev.event_id AS parent
        """
        nodes = []
        edges = []
        try:
            with driver.session(database=self.settings.neo4j_database) as session:
                results = session.run(query, {"claim_id": claim_id})
                for record in results:
                    nodes.append({
                        "id": record["id"],
                        "data": {"label": f"{record['agent']}: {record['type']}"},
                    })
                    if record["parent"]:
                        edges.append({
                            "id": f"{record['parent']}->{record['id']}",
                            "source": record["parent"],
                            "target": record["id"],
                        })
            return {"nodes": nodes, "edges": edges, "source": "neo4j"}
        except Exception as e:
            logger.warning(f"Failed to query Neo4j causal graph: {e}")
            return {"nodes": [], "edges": [], "source": "error", "error": str(e)}

    def close(self):
        """
        Closes the Neo4j driver connection pool.
        """
        if self._driver:
            self._driver.close()
            self._driver = None


# Singleton instance
neo4j_client = Neo4jClient()


def get_neo4j_client() -> Neo4jClient:
    return neo4j_client
