"""
Neo4j persistence handler for Graph-to-Agent.

Replaces BigQuery with native graph database for better graph queries.
Uses Cypher query language for natural graph operations.

Install: pip install neo4j
"""

import os
import logging
from typing import Optional
from datetime import datetime

try:
    from neo4j import GraphDatabase
    HAS_NEO4J = True
except ImportError:
    HAS_NEO4J = False
    GraphDatabase = None


class Neo4jHandler:
    """
    Neo4j graph database handler for storing and querying agent graphs.

    Advantages over BigQuery:
    - Native graph queries (Cypher)
    - Better for traversals and pattern matching
    - Real-time reads/writes
    - Built-in graph algorithms

    Example:
        handler = Neo4jHandler()
        handler.save_graph_data(graph_data, "my_graph_001")
        result = handler.load_graph_data_by_id("my_graph_001")
    """

    def __init__(
        self,
        uri: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: str = "neo4j",
    ):
        """
        Initialize Neo4j connection.

        Args:
            uri: Neo4j connection URI (default: NEO4J_URI env var)
            username: Neo4j username (default: NEO4J_USERNAME env var)
            password: Neo4j password (default: NEO4J_PASSWORD env var)
            database: Database name (default: "neo4j")
        """
        if not HAS_NEO4J:
            raise ImportError("neo4j package required. Install with: pip install neo4j")

        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.username = username or os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD")
        self.database = database
        self.logger = logging.getLogger(__name__)

        if not self.password:
            raise ValueError("Neo4j password required. Set NEO4J_PASSWORD env var.")

        self._driver = None

    @property
    def driver(self):
        """Lazy-load Neo4j driver."""
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password)
            )
            self.logger.info(f"Connected to Neo4j at {self.uri}")
        return self._driver

    def close(self):
        """Close the Neo4j connection."""
        if self._driver:
            self._driver.close()
            self._driver = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # =========================================================================
    # Graph CRUD Operations
    # =========================================================================

    def save_graph_data(self, graph_data: dict, graph_id: str) -> dict:
        """
        Save graph data (nodes and edges) to Neo4j.

        Args:
            graph_data: Dict with 'nodes' and 'edges' keys
            graph_id: Unique identifier for this graph

        Returns:
            Status dict with saved graph info
        """
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])
        timestamp = datetime.utcnow().isoformat()

        with self.driver.session(database=self.database) as session:
            # Create nodes
            for node in nodes:
                session.execute_write(
                    self._create_node,
                    graph_id=graph_id,
                    node_id=node["id"],
                    label=node.get("label", ""),
                    timestamp=timestamp,
                )

            # Create edges
            for edge in edges:
                session.execute_write(
                    self._create_edge,
                    graph_id=graph_id,
                    from_id=edge["from"],
                    to_id=edge["to"],
                    timestamp=timestamp,
                )

        self.logger.info(f"Saved graph {graph_id}: {len(nodes)} nodes, {len(edges)} edges")

        return {
            "status": "success",
            "graph_id": graph_id,
            "nodes_count": len(nodes),
            "edges_count": len(edges),
        }

    @staticmethod
    def _create_node(tx, graph_id: str, node_id: str, label: str, timestamp: str):
        """Transaction function to create a node."""
        query = """
        MERGE (n:AgentNode {graph_id: $graph_id, node_id: $node_id})
        SET n.label = $label,
            n.updated_at = $timestamp
        RETURN n
        """
        tx.run(query, graph_id=graph_id, node_id=node_id, label=label, timestamp=timestamp)

    @staticmethod
    def _create_edge(tx, graph_id: str, from_id: str, to_id: str, timestamp: str):
        """Transaction function to create an edge."""
        query = """
        MATCH (a:AgentNode {graph_id: $graph_id, node_id: $from_id})
        MATCH (b:AgentNode {graph_id: $graph_id, node_id: $to_id})
        MERGE (a)-[r:CONNECTS_TO]->(b)
        SET r.graph_id = $graph_id,
            r.updated_at = $timestamp
        RETURN r
        """
        tx.run(query, graph_id=graph_id, from_id=from_id, to_id=to_id, timestamp=timestamp)

    def load_graph_data_by_id(self, graph_id: str) -> dict:
        """
        Load a graph by its ID.

        Args:
            graph_id: The graph identifier

        Returns:
            Dict with 'nodes' and 'edges' lists
        """
        with self.driver.session(database=self.database) as session:
            # Get nodes
            nodes_result = session.execute_read(self._get_nodes, graph_id=graph_id)

            # Get edges
            edges_result = session.execute_read(self._get_edges, graph_id=graph_id)

        return {
            "nodes": nodes_result,
            "edges": edges_result,
        }

    @staticmethod
    def _get_nodes(tx, graph_id: str) -> list:
        """Transaction function to get nodes."""
        query = """
        MATCH (n:AgentNode {graph_id: $graph_id})
        RETURN n.node_id AS id, n.label AS label
        """
        result = tx.run(query, graph_id=graph_id)
        return [{"id": record["id"], "label": record["label"]} for record in result]

    @staticmethod
    def _get_edges(tx, graph_id: str) -> list:
        """Transaction function to get edges."""
        query = """
        MATCH (a:AgentNode {graph_id: $graph_id})-[r:CONNECTS_TO]->(b:AgentNode {graph_id: $graph_id})
        RETURN a.node_id AS from, b.node_id AS to
        """
        result = tx.run(query, graph_id=graph_id)
        return [{"from": record["from"], "to": record["to"]} for record in result]

    def get_available_graphs(self) -> list:
        """Get all available graph IDs."""
        with self.driver.session(database=self.database) as session:
            result = session.execute_read(self._get_graph_ids)
        return result

    @staticmethod
    def _get_graph_ids(tx) -> list:
        """Transaction function to get distinct graph IDs."""
        query = """
        MATCH (n:AgentNode)
        RETURN DISTINCT n.graph_id AS graph_id
        ORDER BY graph_id
        """
        result = tx.run(query)
        return [{"graph_id": record["graph_id"]} for record in result]

    def delete_graph(self, graph_id: str) -> dict:
        """Delete a graph and all its nodes/edges."""
        with self.driver.session(database=self.database) as session:
            session.execute_write(self._delete_graph, graph_id=graph_id)

        self.logger.info(f"Deleted graph {graph_id}")
        return {"status": "success", "deleted": graph_id}

    @staticmethod
    def _delete_graph(tx, graph_id: str):
        """Transaction function to delete a graph."""
        query = """
        MATCH (n:AgentNode {graph_id: $graph_id})
        DETACH DELETE n
        """
        tx.run(query, graph_id=graph_id)

    # =========================================================================
    # Graph Algorithms (Neo4j native)
    # =========================================================================

    def find_root_nodes(self, graph_id: str) -> list:
        """
        Find root nodes (nodes with no incoming edges).

        This is a native graph query - much faster than SQL-based approach.
        """
        with self.driver.session(database=self.database) as session:
            result = session.execute_read(self._find_roots, graph_id=graph_id)
        return result

    @staticmethod
    def _find_roots(tx, graph_id: str) -> list:
        """Find nodes with no incoming edges."""
        query = """
        MATCH (n:AgentNode {graph_id: $graph_id})
        WHERE NOT ()-[:CONNECTS_TO]->(n)
        RETURN n.node_id AS id, n.label AS label
        """
        result = tx.run(query, graph_id=graph_id)
        return [{"id": record["id"], "label": record["label"]} for record in result]

    def find_path(self, graph_id: str, from_id: str, to_id: str) -> list:
        """
        Find shortest path between two nodes.

        Returns list of node IDs in the path.
        """
        with self.driver.session(database=self.database) as session:
            result = session.execute_read(
                self._find_shortest_path,
                graph_id=graph_id,
                from_id=from_id,
                to_id=to_id,
            )
        return result

    @staticmethod
    def _find_shortest_path(tx, graph_id: str, from_id: str, to_id: str) -> list:
        """Find shortest path using native graph algorithm."""
        query = """
        MATCH path = shortestPath(
            (a:AgentNode {graph_id: $graph_id, node_id: $from_id})-[:CONNECTS_TO*]->(b:AgentNode {graph_id: $graph_id, node_id: $to_id})
        )
        RETURN [n IN nodes(path) | n.node_id] AS path
        """
        result = tx.run(query, graph_id=graph_id, from_id=from_id, to_id=to_id)
        record = result.single()
        return record["path"] if record else []

    def get_descendants(self, graph_id: str, node_id: str) -> list:
        """Get all descendants of a node (full subtree)."""
        with self.driver.session(database=self.database) as session:
            result = session.execute_read(
                self._get_descendants,
                graph_id=graph_id,
                node_id=node_id,
            )
        return result

    @staticmethod
    def _get_descendants(tx, graph_id: str, node_id: str) -> list:
        """Get all nodes reachable from given node."""
        query = """
        MATCH (start:AgentNode {graph_id: $graph_id, node_id: $node_id})-[:CONNECTS_TO*]->(descendant)
        RETURN DISTINCT descendant.node_id AS id, descendant.label AS label
        """
        result = tx.run(query, graph_id=graph_id, node_id=node_id)
        return [{"id": record["id"], "label": record["label"]} for record in result]

    # =========================================================================
    # Schema & Indexes
    # =========================================================================

    def setup_indexes(self):
        """Create indexes for better query performance."""
        with self.driver.session(database=self.database) as session:
            # Index on graph_id for fast graph lookups
            session.run("""
                CREATE INDEX agent_node_graph_id IF NOT EXISTS
                FOR (n:AgentNode)
                ON (n.graph_id)
            """)

            # Composite index for node lookups within a graph
            session.run("""
                CREATE INDEX agent_node_composite IF NOT EXISTS
                FOR (n:AgentNode)
                ON (n.graph_id, n.node_id)
            """)

        self.logger.info("Neo4j indexes created")
