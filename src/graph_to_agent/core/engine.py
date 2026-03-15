"""
EngineRoom - Low-level graph processing engine.

This module handles tree construction, traversal, and GPT format conversion.
For most use cases, use GraphOrchestrator instead.
"""

import logging
from typing import Any, Optional


class EngineRoom:
    """
    Low-level graph processing engine.

    Handles:
    - Tree structure building from nodes/edges
    - Root node identification
    - GPT message format conversion
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the engine."""
        self.logger = logger or logging.getLogger(__name__)

    def build_tree_structure(self, nodes: list[dict], edges: list[dict]) -> dict:
        """
        Build a tree structure from nodes and edges.

        Args:
            nodes: List of node dicts with 'id' and 'label'
            edges: List of edge dicts with 'from' and 'to'

        Returns:
            Dictionary mapping node_id to {label, children}
        """
        tree = {}
        for node in nodes:
            tree[node["id"]] = {
                "label": node["label"],
                "children": [],
            }

        for edge in edges:
            from_id = edge["from"]
            to_id = edge["to"]
            if from_id in tree:
                tree[from_id]["children"].append(to_id)

        return tree

    def find_root_nodes(self, nodes: list[dict], edges: list[dict]) -> list[str]:
        """
        Find root nodes (nodes with no incoming edges).

        Args:
            nodes: List of node dicts
            edges: List of edge dicts

        Returns:
            List of root node IDs
        """
        target_ids = {edge["to"] for edge in edges}
        return [node["id"] for node in nodes if node["id"] not in target_ids]

    def count_trees(self, nodes: list[dict], edges: list[dict]) -> int:
        """Count the number of disconnected trees (root nodes)."""
        return len(self.find_root_nodes(nodes, edges))

    def get_node_type(self, label: str) -> str:
        """
        Determine node type from label.

        Returns:
            'user', 'system', or 'content'
        """
        label_lower = label.lower().strip()
        if label_lower == "user":
            return "user"
        elif label_lower == "system":
            return "system"
        else:
            return "content"

    def tree_to_gpt_messages(
        self,
        tree: dict,
        node_id: str,
        messages: Optional[list] = None,
        is_user: bool = True,
    ) -> list[dict]:
        """
        Convert tree structure to GPT message format.

        Args:
            tree: Tree structure from build_tree_structure
            node_id: Starting node ID
            messages: Accumulated messages (internal use)
            is_user: Whether current role is user

        Returns:
            List of message dicts with 'role' and 'content'
        """
        if messages is None:
            messages = []

        if node_id not in tree:
            return messages

        node = tree[node_id]
        node_type = self.get_node_type(node["label"])

        if node_type in ("user", "system"):
            role = node_type
            # Process first child as content
            if node["children"]:
                content_node_id = node["children"][0]
                if content_node_id in tree:
                    content = tree[content_node_id]["label"]
                    messages.append({"role": role, "content": content})

                    # Process children of content node
                    for child_id in tree[content_node_id].get("children", []):
                        self.tree_to_gpt_messages(
                            tree, child_id, messages, role == "user"
                        )

        return messages

    def prepare_gpt_payload(
        self,
        nodes: list[dict],
        edges: list[dict],
        model: str = "gpt-3.5-turbo",
    ) -> dict:
        """
        Prepare a complete GPT API payload from graph data.

        Args:
            nodes: List of node dicts
            edges: List of edge dicts
            model: Model ID to use

        Returns:
            Complete API payload dict
        """
        tree = self.build_tree_structure(nodes, edges)
        root_nodes = self.find_root_nodes(nodes, edges)

        all_messages = []
        for root_id in root_nodes:
            messages = self.tree_to_gpt_messages(tree, root_id)
            all_messages.extend(messages)

        return {
            "model": model,
            "messages": all_messages,
        }

    def populate_variables(
        self,
        nodes: list[dict],
        variable_values: dict[str, str],
    ) -> list[dict]:
        """
        Replace @variable placeholders in node labels.

        Args:
            nodes: List of node dicts
            variable_values: Dict mapping variable names to values

        Returns:
            New list of nodes with substituted values
        """
        import copy

        new_nodes = copy.deepcopy(nodes)
        for node in new_nodes:
            for var_name, var_value in variable_values.items():
                placeholder = f"@variable_{var_name}"
                if placeholder in node["label"]:
                    node["label"] = node["label"].replace(placeholder, var_value)
                # Generic @variable
                if "@variable" in node["label"] and var_name == "default":
                    node["label"] = node["label"].replace("@variable", var_value)

        return new_nodes
