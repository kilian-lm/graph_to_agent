"""In-memory graph storage."""

from datetime import datetime
from typing import Optional
import json


class InMemoryStore:
    """
    Simple in-memory storage for graphs.

    Good for development and testing.
    For production, use BigQueryStore or FileStore.
    """

    def __init__(self):
        """Initialize empty store."""
        self._graphs: dict[str, dict] = {}
        self._metadata: dict[str, dict] = {}

    def save(self, graph_id: str, graph_data: dict, name: Optional[str] = None) -> str:
        """
        Save a graph.

        Args:
            graph_id: Unique identifier
            graph_data: Graph with nodes and edges
            name: Optional human-readable name

        Returns:
            The graph_id
        """
        self._graphs[graph_id] = graph_data
        self._metadata[graph_id] = {
            "name": name or graph_id,
            "created_at": datetime.now().isoformat(),
            "node_count": len(graph_data.get("nodes", [])),
            "edge_count": len(graph_data.get("edges", [])),
        }
        return graph_id

    def load(self, graph_id: str) -> Optional[dict]:
        """
        Load a graph by ID.

        Args:
            graph_id: Graph identifier

        Returns:
            Graph data or None if not found
        """
        return self._graphs.get(graph_id)

    def delete(self, graph_id: str) -> bool:
        """
        Delete a graph.

        Args:
            graph_id: Graph identifier

        Returns:
            True if deleted, False if not found
        """
        if graph_id in self._graphs:
            del self._graphs[graph_id]
            del self._metadata[graph_id]
            return True
        return False

    def list_graphs(self) -> list[dict]:
        """
        List all stored graphs.

        Returns:
            List of metadata dicts
        """
        return [
            {"id": gid, **meta}
            for gid, meta in self._metadata.items()
        ]

    def exists(self, graph_id: str) -> bool:
        """Check if a graph exists."""
        return graph_id in self._graphs

    def clear(self):
        """Clear all stored graphs."""
        self._graphs.clear()
        self._metadata.clear()
