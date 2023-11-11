import json
import logging
import os
import inspect

from logger.CustomLogger import CustomLogger

# Initialize the custom logger
logger = CustomLogger(log_file='graph_processing.log').logger


class ContextManager:
    def __init__(self):
        self.responses = {}

    def add_response(self, label, response):
        self.responses[label] = response

    def get_response(self, label):
        return self.responses.get(label, '')


class GraphToGPTTranslator:
    def __init__(self, log_file='graph_processing.log'):
        self.logger = CustomLogger(log_file=log_file).logger

    def translate_graph_to_gpt(self, graph_data_json):
        graph_data = json.loads(graph_data_json)
        nodes = {node['id']: node for node in graph_data['nodes']}
        edges = graph_data['edges']

        self.log_edges_and_nodes(edges, nodes)
        sequences = self.identify_and_log_sequences(nodes, edges)

        messages = []
        for seq in sequences:
            if self.is_valid_sequence(seq, nodes):
                seq_messages = self.format_sequence_to_messages(seq, nodes)
                messages.extend(seq_messages)

        return json.dumps({"model": "gpt-3.5-turbo", "messages": messages}, indent=4)

    def log_edges_and_nodes(self, edges, nodes):
        for edge in edges:
            self.logger.debug(f"Edge from {edge['from']} to {edge['to']}")
            self.logger.debug(f"Node {edge['from']} content: {nodes[edge['from']]['label'].split()[:5]}")
            self.logger.debug(f"Node {edge['to']} content: {nodes[edge['to']]['label'].split()[:5]}")

    def identify_and_log_sequences(self, nodes, edges):
        sequences = []
        for edge in edges:
            sequence = [edge['from'], edge['to']]
            while sequence[-1] in [e['from'] for e in edges]:
                next_edge = next(e for e in edges if e['from'] == sequence[-1])
                sequence.append(next_edge['to'])
            sequences.append(sequence)
            self.logger.debug(f"Identified sequence: {sequence}")
        return sequences

    def is_valid_sequence(self, sequence, nodes):
        if len(sequence) < 6:
            return False

        expected_roles = ['user', 'content', 'system', 'content', 'user', 'content']
        actual_roles = [self.get_role(nodes[node_id]) for node_id in sequence]

        return all(role == expected_roles[i] for i, role in enumerate(actual_roles[:len(expected_roles)]))

    def format_sequence_to_json(self, sequence_ids, nodes):
        formatted_sequence = []
        for node_id in sequence_ids:
            node = nodes.get(node_id, {})
            node_content = node.get('label', '')
            role = self.get_role(node)

            # Filter out nodes where label directly matches the role
            if role != node_content.lower():
                formatted_sequence.append({'role': role, 'content': node_content})

        return json.dumps({'model': 'gpt-3.5-turbo-16k-0613', 'messages': formatted_sequence}, indent=4)

    def format_sequence_to_messages(self, sequence_ids, nodes):
        messages = []
        for node_id in sequence_ids:
            node = nodes.get(node_id, {})
            node_content = node.get('label', '')
            role = self.get_role(node)
            messages.append({"role": role, "content": node_content})

        return messages

    def get_role(self, node):
        label = node['label'].lower()
        if label == 'user' or label == 'system':
            return label

        raise ValueError(f"Invalid role label: {label}")

    def print_sequence_contents(self, sequence, nodes):
        for node_id in sequence:
            node = nodes[node_id]
            self.logger.info(f"Node ID: {node_id}, Role: {self.get_role(node)}, Content: {node['label']}")


translator = GraphToGPTTranslator()

graph_data_json = """
{
  "nodes": [
    {
      "id": "c7d1c0a4-6365-44d6-be0c-bd3fc5436b85",
      "label": "user"
    },
    {
      "id": "757e7439-08f8-4cea-afac-c25b01167d32",
      "label": "user"
    },
    {
      "id": "2e419e7e-a540-4c9a-af4e-5110e54fad96",
      "label": "system"
    },
    {
      "id": "07537a68-1c7e-4edb-a72f-2d82015c490f",
      "label": "Understood! As I'm an expert in the .puml syntax i will correct it"
    },
    {
      "id": "1cc45118-72ee-4efe-95d8-06e8c02fb4c0",
      "label": "The following is a .puml content generated by an agent. Please critically review it and correct any mistakes, especially ensuring it strictly adheres to .puml syntax and does not contain any elements from other diagramming languages like Mermaid"
    },
    {
      "id": "2d545024-3765-4b01-b1df-04da99ea4e80",
      "x": -575.9889498552049,
      "y": -331.9214349905721,
      "label": "sequenceDiagramAlice->>John: Hello John, how are you?John-->>Alice: Great!Alice-)John: See you later!"
    }
  ],
  "edges": [
    {
      "from": "07537a68-1c7e-4edb-a72f-2d82015c490f",
      "to": "757e7439-08f8-4cea-afac-c25b01167d32",
      "id": "84f178f5-9dba-4f5c-b525-e16ea173be2f"
    },
    {
      "from": "1cc45118-72ee-4efe-95d8-06e8c02fb4c0",
      "to": "2e419e7e-a540-4c9a-af4e-5110e54fad96",
      "id": "d535cac8-7bec-452e-b3ef-4c0184610ba3"
    },
    {
      "from": "2e419e7e-a540-4c9a-af4e-5110e54fad96",
      "to": "07537a68-1c7e-4edb-a72f-2d82015c490f",
      "id": "1764a3dc-3198-4e08-819e-51ccf56f4a07"
    },
    {
      "from": "c7d1c0a4-6365-44d6-be0c-bd3fc5436b85",
      "to": "1cc45118-72ee-4efe-95d8-06e8c02fb4c0",
      "id": "10bad7e6-bf61-42f2-95aa-47ba7abe6b30"
    },
    {
      "from": "757e7439-08f8-4cea-afac-c25b01167d32",
      "to": "2d545024-3765-4b01-b1df-04da99ea4e80",
      "id": "eb438078-7275-414e-9eed-cf77d931e0c3"
    }
  ]
}
"""


graph_data = json.loads(graph_data_json)
graph_data
nodes = {node['id']: node for node in graph_data['nodes']}
nodes
edges = graph_data['edges']
edges



def build_tree_structure(nodes, edges):
    tree = {}
    for node in nodes:
        tree[node['id']] = {
            'label': node['label'],
            'children': []
        }
    for edge in edges:
        tree[edge['from']]['children'].append(edge['to'])
    return tree

def print_tree(tree, node_id, depth=0):
    # This function recursively prints the tree.
    indent = ' ' * depth * 2
    print(f"{indent}- {tree[node_id]['label']}")
    for child_id in tree[node_id]['children']:
        print_tree(tree, child_id, depth + 1)


tree = build_tree_structure(graph_data['nodes'], graph_data['edges'])

# Print the tree starting from the root node. Assuming the root has no incoming edges.
root_nodes = [node['id'] for node in graph_data['nodes'] if not any(edge['to'] == node['id'] for edge in graph_data['edges'])]

# Now let's print the trees. There may be multiple roots if the graph is not a single tree.
for root_id in root_nodes:
    print_tree(tree, root_id)
    print("\n")  # Add spacing between different trees (if any)










translator.log_edges_and_nodes(edges, nodes)
sequences = translator.identify_and_log_sequences(nodes, edges)

messages = []
for seq in sequences:
    if translator.is_valid_sequence(seq, nodes):
        seq_messages = translator.format_sequence_to_messages(seq, nodes)
        messages.extend(seq_messages)

translated_data = translator.translate_graph_to_gpt(graph_data_json)
translated_data
json.dumps(translated_data)
nodes = {
    'c7d1c0a4-6365-44d6-be0c-bd3fc5436b85': {'label': 'user'},
    '1cc45118-72ee-4efe-95d8-06e8c02fb4c0': {'label': 'The following is a .puml content generated by an agent...'},
    '2e419e7e-a540-4c9a-af4e-5110e54fad96': {'label': 'system'},
    '07537a68-1c7e-4edb-a72f-2d82015c490f': {'label': 'Understood! As I\'m an expert in the .puml syntax...'},
    '757e7439-08f8-4cea-afac-c25b01167d32': {'label': 'user'},
    '2d545024-3765-4b01-b1df-04da99ea4e80': {'label': 'sequenceDiagram\nAlice->>John: Hello John, how are you?...'}
}

# Identified Sequence
sequence_ids = ['c7d1c0a4-6365-44d6-be0c-bd3fc5436b85', '1cc45118-72ee-4efe-95d8-06e8c02fb4c0',
                '2e419e7e-a540-4c9a-af4e-5110e54fad96', '07537a68-1c7e-4edb-a72f-2d82015c490f',
                '757e7439-08f8-4cea-afac-c25b01167d32', '2d545024-3765-4b01-b1df-04da99ea4e80']


# Function to format sequence into JSON
def format_sequence_to_json(sequence_ids, nodes):
    formatted_sequence = []
    for node_id in sequence_ids:
        node_content = nodes.get(node_id, {}).get('label', '')
        role = 'system' if 'system' in node_content.lower() else 'user'
        formatted_sequence.append({'role': role, 'content': node_content})

    return json.dumps({'model': 'gpt-3.5-turbo-16k-0613', 'messages': formatted_sequence}, indent=4)


# Generate JSON
json_output = format_sequence_to_json(sequence_ids, nodes)
print(json_output)
