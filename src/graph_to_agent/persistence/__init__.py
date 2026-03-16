"""Persistence backends for storing and retrieving graphs."""

from graph_to_agent.persistence.memory import InMemoryStore
from graph_to_agent.persistence.file import FileStore

# Optional: Neo4j (requires: pip install neo4j)
try:
    from graph_to_agent.persistence.neo4j_handler import Neo4jHandler
except ImportError:
    Neo4jHandler = None

__all__ = ["InMemoryStore", "FileStore", "Neo4jHandler"]
