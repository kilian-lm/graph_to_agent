
import json

# Load the provided JSON file
with open("agent_interactions_20231031_185854.json", "r") as file:
    data = json.load(file)

# Display the first few entries to understand the structure
data[:5] if isinstance(data, list) else data


type(data), data.keys() if isinstance(data, dict) else None

agent_interactions = data['agent_interactions']

type(agent_interactions), agent_interactions[0] if isinstance(agent_interactions, list) else agent_interactions

def translate_to_visjs(agent_interactions):
    nodes = []
    edges = []
    node_id = 0

    prev_content_node_id = None

    for interaction_group in agent_interactions:
        messages = interaction_group['messages']
        for interaction in messages:
            # Extract role and content
            role = interaction['role']
            # content = interaction['content'][:100] + "..."  # Truncate content for brevity
            content = interaction['content']
            # Create nodes
            role_node = {"id": node_id, "label": role}
            nodes.append(role_node)
            role_node_id = node_id
            node_id += 1

            content_node = {"id": node_id, "label": content}
            nodes.append(content_node)
            content_node_id = node_id
            node_id += 1

            # Create edges
            edges.append({"from": role_node_id, "to": content_node_id})  # Role to content
            if prev_content_node_id is not None:
                edges.append({"from": prev_content_node_id, "to": role_node_id})  # Previous content to current role

            prev_content_node_id = content_node_id

    return {"nodes": nodes, "edges": edges}

visjs_data = translate_to_visjs(agent_interactions)

visjs_data
