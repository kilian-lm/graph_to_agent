#!/usr/bin/env python3
"""
Basic Agent Chain Example

This example demonstrates how to create a simple agent chain
using the graph-to-agent framework.

The graph structure:
    user -> "Translate to French" -> system -> "Understood" -> user -> "Hello world"

Results in GPT messages:
    [{"role": "user", "content": "Translate to French"},
     {"role": "system", "content": "Understood"},
     {"role": "user", "content": "Hello world"}]
"""

import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def create_translation_graph():
    """Create a simple translation agent graph."""
    return {
        "nodes": [
            {"id": "user1", "label": "user"},
            {"id": "instruction", "label": "You are a French translator. Translate the following text to French."},
            {"id": "system1", "label": "system"},
            {"id": "ack", "label": "Understood! I will translate the text to French."},
            {"id": "user2", "label": "user"},
            {"id": "input", "label": "Hello, how are you today?"},
        ],
        "edges": [
            {"from": "user1", "to": "instruction"},
            {"from": "instruction", "to": "system1"},
            {"from": "system1", "to": "ack"},
            {"from": "ack", "to": "user2"},
            {"from": "user2", "to": "input"},
        ],
    }


def build_tree_structure(nodes, edges):
    """Build a tree structure from nodes and edges."""
    tree = {}
    for node in nodes:
        tree[node["id"]] = {"label": node["label"], "children": []}
    for edge in edges:
        if edge["from"] in tree:
            tree[edge["from"]]["children"].append(edge["to"])
    return tree


def find_root_nodes(nodes, edges):
    """Find nodes that have no incoming edges (root nodes)."""
    target_ids = {edge["to"] for edge in edges}
    return [node["id"] for node in nodes if node["id"] not in target_ids]


def get_node_type(label):
    """Determine if a node is user, system, or content."""
    label_lower = label.lower()
    if label_lower == "user":
        return "user"
    elif label_lower == "system":
        return "system"
    else:
        return "content"


def tree_to_messages(tree, node_id, messages=None, current_role="user"):
    """Convert tree structure to GPT message format."""
    if messages is None:
        messages = []

    node = tree[node_id]
    node_type = get_node_type(node["label"])

    if node_type in ["user", "system"]:
        # This is a role marker, process its children as content
        for child_id in node["children"]:
            child = tree[child_id]
            child_type = get_node_type(child["label"])

            if child_type == "content":
                # Add this content with the current role
                messages.append({"role": node_type, "content": child["label"]})

                # Process children of the content node
                for grandchild_id in child["children"]:
                    tree_to_messages(tree, grandchild_id, messages, node_type)
            else:
                # It's another role marker
                tree_to_messages(tree, child_id, messages, node_type)

    return messages


def main():
    """Main execution."""
    print("Graph-to-Agent: Basic Agent Chain Example")
    print("=" * 50)

    # Create the graph
    graph = create_translation_graph()
    print("\n1. Created graph with nodes:")
    for node in graph["nodes"]:
        print(f"   - {node['id']}: {node['label'][:50]}...")

    # Build tree structure
    tree = build_tree_structure(graph["nodes"], graph["edges"])
    print("\n2. Built tree structure")

    # Find root nodes
    roots = find_root_nodes(graph["nodes"], graph["edges"])
    print(f"\n3. Found root nodes: {roots}")

    # Convert to messages
    all_messages = []
    for root_id in roots:
        messages = tree_to_messages(tree, root_id)
        all_messages.extend(messages)

    print("\n4. Generated GPT message format:")
    print(json.dumps(all_messages, indent=2))

    # Create full GPT request payload
    gpt_payload = {"model": "gpt-3.5-turbo", "messages": all_messages}

    print("\n5. Full GPT API payload:")
    print(json.dumps(gpt_payload, indent=2))

    # Note: To actually call the API, uncomment below:
    # import requests
    # api_key = os.getenv('OPENAI_API_KEY')
    # response = requests.post(
    #     'https://api.openai.com/v1/chat/completions',
    #     headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
    #     json=gpt_payload
    # )
    # print(response.json()['choices'][0]['message']['content'])


if __name__ == "__main__":
    main()
