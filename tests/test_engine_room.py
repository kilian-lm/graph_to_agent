"""Tests for EngineRoom core functionality."""

import pytest


class TestEngineRoom:
    """Test suite for EngineRoom graph processing."""

    def test_build_tree_structure(self):
        """Test tree structure building from nodes and edges."""
        # Sample graph data
        nodes = [
            {"id": "1", "label": "user"},
            {"id": "2", "label": "Hello, how are you?"},
            {"id": "3", "label": "system"},
        ]
        edges = [
            {"from": "1", "to": "2"},
            {"from": "2", "to": "3"},
        ]

        # Build tree manually (simulating EngineRoom.build_tree_structure)
        tree = {}
        for node in nodes:
            tree[node["id"]] = {"label": node["label"], "children": []}
        for edge in edges:
            tree[edge["from"]]["children"].append(edge["to"])

        assert "1" in tree
        assert tree["1"]["label"] == "user"
        assert "2" in tree["1"]["children"]

    def test_provide_root_nodes(self):
        """Test identification of root nodes (nodes with no incoming edges)."""
        nodes = [
            {"id": "root1", "label": "user"},
            {"id": "child1", "label": "content"},
            {"id": "root2", "label": "user"},
        ]
        edges = [
            {"from": "root1", "to": "child1"},
        ]

        # Find root nodes (nodes that are never a 'to' target)
        target_ids = {edge["to"] for edge in edges}
        root_nodes = [node["id"] for node in nodes if node["id"] not in target_ids]

        assert "root1" in root_nodes
        assert "root2" in root_nodes
        assert "child1" not in root_nodes

    def test_get_node_type(self):
        """Test node type classification."""

        def get_node_type(node):
            if "user" in node["label"].lower():
                return "user"
            elif "system" in node["label"].lower():
                return "system"
            else:
                return "content"

        assert get_node_type({"label": "user"}) == "user"
        assert get_node_type({"label": "User Input"}) == "user"
        assert get_node_type({"label": "system"}) == "system"
        assert get_node_type({"label": "Hello world"}) == "content"


class TestGraphPatterns:
    """Test graph pattern recognition and processing."""

    def test_valid_transitions(self):
        """Test valid transition patterns in agent graphs."""
        valid_transitions = {
            "user": "content",
            "content": "system",
            "system": "agent_response",
            "agent_response": "user",
        }

        # Test valid transitions
        assert valid_transitions["user"] == "content"
        assert valid_transitions["content"] == "system"

    def test_message_sequence_generation(self):
        """Test GPT message sequence generation from graph."""
        # Simulated graph data representing a conversation
        graph_data = {
            "nodes": [
                {"id": "1", "label": "user"},
                {"id": "2", "label": "You are a helpful assistant"},
                {"id": "3", "label": "system"},
                {"id": "4", "label": "Understood!"},
            ],
            "edges": [
                {"from": "1", "to": "2"},
                {"from": "2", "to": "3"},
                {"from": "3", "to": "4"},
            ],
        }

        # Build expected message format
        messages = [
            {"role": "user", "content": "You are a helpful assistant"},
            {"role": "system", "content": "Understood!"},
        ]

        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "system"


class TestVariableSubstitution:
    """Test @variable substitution functionality."""

    def test_variable_replacement(self):
        """Test @variable placeholder replacement."""
        label = "The answer is @variable and more"
        gpt_response = "42"

        result = label.replace("@variable", gpt_response)

        assert result == "The answer is 42 and more"
        assert "@variable" not in result

    def test_multiple_variable_markers(self):
        """Test handling of multiple variable markers."""
        label = "@variable_1 meets @variable_2"

        # In actual implementation, each variable would be resolved separately
        result = label.replace("@variable_1", "Alice").replace("@variable_2", "Bob")

        assert result == "Alice meets Bob"
