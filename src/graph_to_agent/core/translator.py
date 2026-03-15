"""
GraphTranslator - Bidirectional translation between graph formats.

Supports conversion between:
- Visual graph format (vis.js compatible)
- GPT message format
- Mermaid diagram format
- PlantUML format
"""

import json
from typing import Any


class GraphTranslator:
    """
    Bidirectional translator for agent graph formats.

    Supports:
    - vis.js JSON <-> GPT messages
    - vis.js JSON <-> Mermaid
    - vis.js JSON <-> PlantUML
    """

    def __init__(self):
        """Initialize translator."""
        self.valid_transitions = {
            "user": "content",
            "content": "system",
            "system": "agent_response",
            "agent_response": "user",
        }

    def to_gpt_messages(self, graph_data: dict) -> list[dict]:
        """
        Convert graph to GPT message format.

        Args:
            graph_data: Dict with 'nodes' and 'edges'

        Returns:
            List of message dicts
        """
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])

        # Build node mapping
        node_map = {n["id"]: n["label"] for n in nodes}

        # Build adjacency list
        children = {n["id"]: [] for n in nodes}
        for edge in edges:
            children[edge["from"]].append(edge["to"])

        # Find root nodes
        targets = {e["to"] for e in edges}
        roots = [n["id"] for n in nodes if n["id"] not in targets]

        # Traverse and build messages
        messages = []
        for root_id in roots:
            self._collect_messages(node_map, children, root_id, messages)

        return messages

    def _collect_messages(
        self,
        node_map: dict,
        children: dict,
        node_id: str,
        messages: list,
    ):
        """Recursively collect messages from tree."""
        if node_id not in node_map:
            return

        label = node_map[node_id]
        label_lower = label.lower().strip()

        if label_lower in ("user", "system"):
            role = label_lower
            # Get content from children
            for child_id in children.get(node_id, []):
                child_label = node_map.get(child_id, "")
                child_lower = child_label.lower().strip()

                if child_lower not in ("user", "system"):
                    # This is content
                    messages.append({"role": role, "content": child_label})
                    # Continue traversal
                    for grandchild_id in children.get(child_id, []):
                        self._collect_messages(
                            node_map, children, grandchild_id, messages
                        )
                else:
                    # Another role marker
                    self._collect_messages(node_map, children, child_id, messages)

    def to_mermaid(self, graph_data: dict) -> str:
        """
        Convert graph to Mermaid diagram format.

        Args:
            graph_data: Dict with 'nodes' and 'edges'

        Returns:
            Mermaid diagram string
        """
        lines = ["graph TD"]

        # Add nodes with sanitized labels
        for node in graph_data.get("nodes", []):
            safe_label = node["label"][:50].replace('"', "'").replace("\n", " ")
            safe_id = node["id"].replace("-", "_")
            lines.append(f'    {safe_id}["{safe_label}"]')

        # Add edges
        for edge in graph_data.get("edges", []):
            from_id = edge["from"].replace("-", "_")
            to_id = edge["to"].replace("-", "_")
            lines.append(f"    {from_id} --> {to_id}")

        return "\n".join(lines)

    def to_plantuml(self, graph_data: dict) -> str:
        """
        Convert graph to PlantUML sequence diagram.

        Args:
            graph_data: Dict with 'nodes' and 'edges'

        Returns:
            PlantUML diagram string
        """
        lines = ["@startuml"]

        # Define participants
        participants = set()
        for node in graph_data.get("nodes", []):
            label_lower = node["label"].lower().strip()
            if label_lower in ("user", "system"):
                participants.add(label_lower.capitalize())

        for p in sorted(participants):
            lines.append(f"participant {p}")

        lines.append("")

        # Create sequence from messages
        messages = self.to_gpt_messages(graph_data)
        prev_role = None

        for msg in messages:
            role = msg["role"].capitalize()
            content = msg["content"][:40].replace("\n", " ")

            if prev_role:
                lines.append(f'{prev_role} -> {role}: "{content}"')
            else:
                lines.append(f'note over {role}: "{content}"')

            prev_role = role

        lines.append("@enduml")
        return "\n".join(lines)

    def from_gpt_messages(
        self,
        messages: list[dict],
        prefix: str = "node",
    ) -> dict:
        """
        Convert GPT messages back to graph format.

        Args:
            messages: List of message dicts
            prefix: ID prefix for generated nodes

        Returns:
            Graph dict with 'nodes' and 'edges'
        """
        nodes = []
        edges = []
        prev_node_id = None

        for i, msg in enumerate(messages):
            role = msg["role"]
            content = msg["content"]

            # Create role marker node
            role_node_id = f"{prefix}_{i}_role"
            nodes.append({"id": role_node_id, "label": role})

            # Create content node
            content_node_id = f"{prefix}_{i}_content"
            nodes.append({"id": content_node_id, "label": content})

            # Edge from role to content
            edges.append({"from": role_node_id, "to": content_node_id})

            # Edge from previous content to this role
            if prev_node_id:
                edges.append({"from": prev_node_id, "to": role_node_id})

            prev_node_id = content_node_id

        return {"nodes": nodes, "edges": edges}
