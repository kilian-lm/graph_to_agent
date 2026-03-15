"""File-based graph storage."""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional


class FileStore:
    """
    File-based storage for graphs.

    Stores graphs as JSON files in a directory.
    Good for local development and small-scale deployments.
    """

    def __init__(self, storage_dir: str = "./graphs"):
        """
        Initialize file store.

        Args:
            storage_dir: Directory to store graph files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _graph_path(self, graph_id: str) -> Path:
        """Get path for a graph file."""
        safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in graph_id)
        return self.storage_dir / f"{safe_id}.json"

    def save(self, graph_id: str, graph_data: dict, name: Optional[str] = None) -> str:
        """
        Save a graph to file.

        Args:
            graph_id: Unique identifier
            graph_data: Graph with nodes and edges
            name: Optional human-readable name

        Returns:
            The graph_id
        """
        data = {
            "id": graph_id,
            "name": name or graph_id,
            "created_at": datetime.now().isoformat(),
            "graph": graph_data,
        }

        path = self._graph_path(graph_id)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

        return graph_id

    def load(self, graph_id: str) -> Optional[dict]:
        """
        Load a graph from file.

        Args:
            graph_id: Graph identifier

        Returns:
            Graph data or None if not found
        """
        path = self._graph_path(graph_id)
        if not path.exists():
            return None

        with open(path) as f:
            data = json.load(f)

        return data.get("graph")

    def delete(self, graph_id: str) -> bool:
        """
        Delete a graph file.

        Args:
            graph_id: Graph identifier

        Returns:
            True if deleted, False if not found
        """
        path = self._graph_path(graph_id)
        if path.exists():
            path.unlink()
            return True
        return False

    def list_graphs(self) -> list[dict]:
        """
        List all stored graphs.

        Returns:
            List of metadata dicts
        """
        graphs = []
        for path in self.storage_dir.glob("*.json"):
            try:
                with open(path) as f:
                    data = json.load(f)
                    graphs.append({
                        "id": data.get("id", path.stem),
                        "name": data.get("name", path.stem),
                        "created_at": data.get("created_at"),
                        "node_count": len(data.get("graph", {}).get("nodes", [])),
                        "edge_count": len(data.get("graph", {}).get("edges", [])),
                    })
            except (json.JSONDecodeError, KeyError):
                continue
        return graphs

    def exists(self, graph_id: str) -> bool:
        """Check if a graph exists."""
        return self._graph_path(graph_id).exists()
