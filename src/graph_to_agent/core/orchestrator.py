"""
GraphOrchestrator - Main entry point for the graph-to-agent framework.

This module provides a high-level API for converting visual graphs
into executable LLM agent workflows.
"""

import os
import json
import logging
from typing import Any, Optional
from dataclasses import dataclass, field

try:
    import requests
except ImportError:
    requests = None

try:
    import openai
except ImportError:
    openai = None


@dataclass
class GraphNode:
    """Represents a node in the agent graph."""

    id: str
    label: str
    node_type: str = "content"  # user, system, or content

    def __post_init__(self):
        """Auto-detect node type from label."""
        label_lower = self.label.lower().strip()
        if label_lower == "user":
            self.node_type = "user"
        elif label_lower == "system":
            self.node_type = "system"
        else:
            self.node_type = "content"


@dataclass
class GraphEdge:
    """Represents an edge (connection) between nodes."""

    from_node: str
    to_node: str
    id: Optional[str] = None


@dataclass
class AgentGraph:
    """Structured representation of an agent graph."""

    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "AgentGraph":
        """Create AgentGraph from dictionary format."""
        nodes = [GraphNode(id=n["id"], label=n["label"]) for n in data.get("nodes", [])]
        edges = [
            GraphEdge(
                from_node=e["from"],
                to_node=e["to"],
                id=e.get("id"),
            )
            for e in data.get("edges", [])
        ]
        return cls(nodes=nodes, edges=edges)

    def to_dict(self) -> dict:
        """Convert back to dictionary format."""
        return {
            "nodes": [{"id": n.id, "label": n.label} for n in self.nodes],
            "edges": [{"from": e.from_node, "to": e.to_node} for e in self.edges],
        }


class GraphOrchestrator:
    """
    Main orchestrator for graph-based agent workflows.

    Example:
        orchestrator = GraphOrchestrator()
        graph = {"nodes": [...], "edges": [...]}
        response = orchestrator.execute(graph)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-3.5-turbo",
        base_url: str = "https://api.openai.com/v1/chat/completions",
    ):
        """
        Initialize the orchestrator.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model to use for completions
            base_url: API endpoint URL
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)

    def graph_to_messages(self, graph_data: dict) -> list[dict]:
        """
        Convert a graph structure to GPT message format.

        Args:
            graph_data: Dictionary with 'nodes' and 'edges' keys

        Returns:
            List of message dictionaries with 'role' and 'content'
        """
        graph = AgentGraph.from_dict(graph_data)

        # Build tree structure
        tree = self._build_tree(graph)

        # Find root nodes (no incoming edges)
        target_ids = {e.to_node for e in graph.edges}
        root_ids = [n.id for n in graph.nodes if n.id not in target_ids]

        # Convert to messages
        messages = []
        for root_id in root_ids:
            self._traverse_tree(tree, root_id, messages)

        return messages

    def _build_tree(self, graph: AgentGraph) -> dict:
        """Build tree structure from graph."""
        tree = {}
        node_map = {n.id: n for n in graph.nodes}

        for node in graph.nodes:
            tree[node.id] = {
                "node": node,
                "children": [],
            }

        for edge in graph.edges:
            if edge.from_node in tree:
                tree[edge.from_node]["children"].append(edge.to_node)

        return tree

    def _traverse_tree(
        self,
        tree: dict,
        node_id: str,
        messages: list,
        current_role: Optional[str] = None,
    ):
        """Recursively traverse tree and build messages."""
        if node_id not in tree:
            return

        entry = tree[node_id]
        node = entry["node"]

        if node.node_type in ("user", "system"):
            # This is a role marker - process children as content
            for child_id in entry["children"]:
                if child_id in tree:
                    child_node = tree[child_id]["node"]
                    if child_node.node_type == "content":
                        messages.append(
                            {"role": node.node_type, "content": child_node.label}
                        )
                        # Continue traversing
                        for grandchild_id in tree[child_id]["children"]:
                            self._traverse_tree(tree, grandchild_id, messages)
                    else:
                        self._traverse_tree(tree, child_id, messages)
        elif current_role:
            # Content node with a known role
            messages.append({"role": current_role, "content": node.label})
            for child_id in entry["children"]:
                self._traverse_tree(tree, child_id, messages)

    def execute(
        self,
        graph_data: dict,
        variables: Optional[dict] = None,
    ) -> str:
        """
        Execute the graph and return the LLM response.

        Args:
            graph_data: Graph structure with nodes and edges
            variables: Optional dict of variable substitutions

        Returns:
            LLM response text
        """
        if not self.api_key:
            raise ValueError(
                "API key required. Set OPENAI_API_KEY env var or pass api_key parameter."
            )

        # Apply variable substitutions
        if variables:
            graph_data = self._substitute_variables(graph_data, variables)

        # Convert to messages
        messages = self.graph_to_messages(graph_data)

        if not messages:
            raise ValueError("Graph produced no messages. Check node/edge structure.")

        # Make API call
        payload = {
            "model": self.model,
            "messages": messages,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        if requests is None:
            raise ImportError("requests library required. Install with: pip install requests")

        response = requests.post(self.base_url, headers=headers, json=payload)
        response.raise_for_status()

        return response.json()["choices"][0]["message"]["content"]

    def _substitute_variables(self, graph_data: dict, variables: dict) -> dict:
        """Replace @variable placeholders in node labels."""
        import copy

        graph = copy.deepcopy(graph_data)
        for node in graph["nodes"]:
            for var_name, var_value in variables.items():
                placeholder = f"@variable_{var_name}"
                if placeholder in node["label"]:
                    node["label"] = node["label"].replace(placeholder, str(var_value))
                # Also support @variable without suffix
                if "@variable" in node["label"] and var_name == "default":
                    node["label"] = node["label"].replace("@variable", str(var_value))
        return graph

    def validate_graph(self, graph_data: dict) -> list[str]:
        """
        Validate graph structure and return list of warnings/errors.

        Returns:
            List of validation messages (empty if valid)
        """
        issues = []

        if "nodes" not in graph_data:
            issues.append("ERROR: Graph missing 'nodes' key")
            return issues

        if "edges" not in graph_data:
            issues.append("WARNING: Graph has no 'edges' - nodes are disconnected")

        node_ids = {n["id"] for n in graph_data.get("nodes", [])}

        # Check for orphan edges
        for edge in graph_data.get("edges", []):
            if edge["from"] not in node_ids:
                issues.append(f"ERROR: Edge references unknown node: {edge['from']}")
            if edge["to"] not in node_ids:
                issues.append(f"ERROR: Edge references unknown node: {edge['to']}")

        # Check for role markers
        has_user = any(
            n["label"].lower().strip() == "user" for n in graph_data.get("nodes", [])
        )
        has_system = any(
            n["label"].lower().strip() == "system" for n in graph_data.get("nodes", [])
        )

        if not has_user and not has_system:
            issues.append(
                "WARNING: No 'user' or 'system' role markers found. "
                "Messages may not be correctly attributed."
            )

        return issues
