import os
import json
from google.cloud import bigquery
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
from google.api_core.exceptions import NotFound
import logging
from google.oauth2.service_account import Credentials
from google.oauth2 import service_account
from google.cloud import bigquery
import json
import datetime
import requests
from logger.CustomLogger import CustomLogger
import inspect
import re

load_dotenv()


# assumption: new methods allows chaining of agents but != recursive calls because @var isnt integrated yet

class BlueprintDesigner():

    def __init__(self):
        # First logging
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        print(timestamp)
        self.log_file = f'{timestamp}_blueprint_designer.log'
        print(self.log_file)
        self.log_dir = './temp_log'
        print(self.log_dir)
        self.log_level = logging.DEBUG
        print(self.log_level)
        self.logger = CustomLogger(self.log_file, self.log_level, self.log_dir)

        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.openai_base_url = "https://api.openai.com/v1/chat/completions"
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.openai_api_key}'
        }

    def load_json_graph(self, json_graph_data):
        graph_data = json.loads(json_graph_data)
        return graph_data


    def provide_root_nodes(self, tree):
        all_children = set(child for node in tree.values() for child in node['children'])
        root_nodes = [node_id for node_id, node in tree.items() if node_id not in all_children]
        return root_nodes


    def tree_counter(self, tree):
        """
        Counts the number of root nodes (trees) in the given tree structure.

        Parameters:
        tree (dict): The tree structure containing nodes and their children.

        Returns:
        int: The number of root nodes (trees) in the tree structure.
        """
        if not isinstance(tree, dict):
            self.logger.error("Invalid tree data format.")
            return 0

        try:
            identified_root_nodes = self.provide_root_nodes(tree)
            counter = len(identified_root_nodes)
            self.logger.info(f"Identified root nodes: {counter}")
            return counter
        except Exception as e:
            self.logger.error(f"Error in counting trees: {e}")
            return 0

    def analyze_hierarchy_and_variables(self, tree):
        variable_hierarchy = {}

        def traverse(node_id, depth=0):
            node = tree[node_id]
            if '@variable' in node['label']:
                variable_number = self.extract_variable_number(node['label'])
                variable_hierarchy[node_id] = {'variable_number': variable_number, 'depth': depth}

            for child_id in node['children']:
                traverse(child_id, depth + 1)

        for root_id in self.provide_root_nodes(tree):
            traverse(root_id)

        return variable_hierarchy

    def extract_variable_number(self, label):
        # Extract and return the number after '@variable_' from the label
        # Assuming the label format is '@variable_X' where X is the number
        match = re.search(r'@variable_(\d+)', label)
        return int(match.group(1)) if match else None

    def design_blueprint(self, variable_hierarchy):
        # Sorting variables first by depth then by variable number
        sorted_variables = sorted(variable_hierarchy.items(), key=lambda x: (x[1]['depth'], x[1]['variable_number']))
        blueprint = [{'node_id': node_id, 'variable_number': details['variable_number']} for node_id, details in
                     sorted_variables]
        return blueprint

    def tree_to_gpt_call(self, tree, node_id, is_user=True):
        messages = []
        node = tree[node_id]

        # If the current node is a 'user' or 'system', process its first child as the content.
        if node['label'] in ['user', 'system']:
            role = 'user' if is_user else 'system'
            if node['children']:
                content_node_id = node['children'][0]  # First child is the content.
                content = tree[content_node_id]['label']
                messages.append({"role": role, "content": content})

                # Process the response (next child of the content node).
                if len(tree[content_node_id]['children']) > 0:
                    response_node_id = tree[content_node_id]['children'][0]
                    messages.extend(self.tree_to_gpt_call(tree, response_node_id, not is_user))

        return messages

    def prepare_gpt_format(self, root_nodes, tree):
        all_messages = []

        for root_id in root_nodes:
            messages = self.tree_to_gpt_call(tree, root_id)
            all_messages.extend(messages)

        gpt_call = {
            "model": "gpt-3.5-turbo",
            "messages": all_messages
        }

        return gpt_call

    def populate_variable_nodes(self, graph_data, gpt_response):
        # Iterate through the nodes in the graph_data
        for node in graph_data['nodes']:
            # Check if the node contains '@variable'
            if '@variable' in node['label']:
                # Replace '@variable' with the GPT response
                node['label'] = node['label'].replace('@variable', gpt_response)

                # Assign a versioned node ID
                node['id'] = f"{node['id']}_v1"  # Assuming recursion_depth is always 1 for simplicity

        return graph_data

    def get_gpt_response(self, processed_data):
        self.logger.debug(processed_data)
        response = requests.post(self.openai_base_url, headers=self.headers, json=processed_data)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            raise Exception(f"Error in GPT request: {response.status_code}, {response.text}")

    # def update_and_return_graph(self, original_graph_data, populated_graph_data):
    #     """
    #     Updates the original graph data with the populated graph data and
    #     returns the entire graph in .vis.js format.
    #
    #     Parameters:
    #     original_graph_data (dict): The original graph data.
    #     populated_graph_data (dict): The graph data with populated variables.
    #
    #     Returns:
    #     dict: The updated graph data in .vis.js format.
    #     """
    #
    #     # Extract original IDs and create a mapping to updated nodes
    #     updated_nodes = {}
    #     for node in populated_graph_data['nodes']:
    #         original_id = node['id'].split('_v')[0]  # Extract original ID before version suffix
    #         updated_nodes[original_id] = node
    #
    #     # Update the original graph with the populated data
    #     for node in original_graph_data['nodes']:
    #         node_id = node['id']
    #         if node_id in updated_nodes:
    #             # Update label with populated data
    #             node['label'] = updated_nodes[node_id]['label']
    #
    #     # Return the updated graph in .vis.js format
    #     return {
    #         'nodes': original_graph_data['nodes'],
    #         'edges': original_graph_data['edges']
    #     }

    def build_tree_structure(self, nodes, edges):
        tree = {}
        for node in nodes:
            tree[node['id']] = {
                'label': node['label'],
                'children': []
            }
        for edge in edges:
            tree[edge['from']]['children'].append(edge['to'])
        return tree

    # def update_cross_agent_variables(self, tree, variable_suffix, response):
    #     for node_id, node in tree.items():
    #         if f"@variable_{variable_suffix}" in node['label']:
    #             node['label'] = node['label'].replace(f"@variable_{variable_suffix}", response)

    def process_graph_with_gpt(self, graph_data):
        # Step 1: Count Trees
        tree_count = self.tree_counter(graph_data)
        self.logger.info(f"Tree count: {tree_count}")

        tree = b_des.build_tree_structure(graph_data["nodes"], graph_data["edges"])
        self.logger.info(f"tree: {tree}")

        # Step 2: Analyze Hierarchy and Variables
        variable_hierarchy = self.analyze_hierarchy_and_variables(tree)
        self.logger.info(f"Variable Hierarchy: {variable_hierarchy}")

        # Step 3: Design Blueprint
        blueprint = self.design_blueprint(variable_hierarchy)
        self.logger.info(f"Blueprint: {blueprint}")

        # Checkpoint: Dump hierarchy to JSON before API requests
        with open('blueprint_checkpoint.json', 'w') as file:
            json.dump(blueprint, file)

        # Step 4: Prepare GPT Format
        gpt_call = self.prepare_gpt_format(self.provide_root_nodes(graph_data), graph_data)
        self.logger.info(f"gpt_call: {gpt_call}")

        # Step 5: Get GPT Response and Populate Nodes
        try:
            gpt_response = self.get_gpt_response(gpt_call)
            self.logger.info(f"gpt_response: {gpt_response}")

            populated_graph = self.populate_variable_nodes(graph_data, gpt_response)
            self.logger.info(f"populated_graph: {populated_graph}")

            # Step 6: Update and Return the Graph in .vis.js Format
            updated_graph_data = self.update_and_return_graph(graph_data, populated_graph)
            self.logger.info(f"updated_graph_data: {updated_graph_data}")

            return updated_graph_data

        except Exception as e:
            self.logger.error(f"Error processing graph with GPT: {e}")
            return None


json_graph_data = """
{
  "nodes": [
    {
      "id": "07537a68-1c7e-4edb-a72f-2d82015c490f",
      "label": "Understood! As I'm an expert in the .puml syntax i will correct it"
    },
    {
      "id": "1cc45118-72ee-4efe-95d8-06e8c02fb4c0",
      "label": "The following is a .puml content generated by an agent. Please critically review it and correct any mistakes, especially ensuring it strictly adheres to .puml syntax and does not contain any elements from other diagramming languages like Mermaid"
    },
    {
      "id": "2e419e7e-a540-4c9a-af4e-5110e54fad96",
      "label": "system"
    },
    {
      "id": "757e7439-08f8-4cea-afac-c25b01167d32",
      "label": "user"
    },
    {
      "id": "c7d1c0a4-6365-44d6-be0c-bd3fc5436b85",
      "label": "user"
    },
    {
      "id": "eac6de73-9726-43b7-9441-f8e319a972e6",
      "label": "@variable_1"
    },
    {
      "id": "copied-1699797991293-eac6de73-9726-43b7-9441-f8e319a972e6",
      "label": "@startumlparticipant Meta-Agent as MAparticipant Agent1 as A1participant Agent2 as A2MA -> A1: Dispatch taskactivate A1A1 -> MA: Send responsedeactivate A1note over MA: Critically digest and evaluate responseMA -> A1: Dispatch task for refined reviewMA -> A2: Dispatch task with new perspectiveactivate A1activate A2A1 -> MA: Send refined responsedeactivate A1A2 -> MA: Send feedback responsedeactivate A2note over MA: Review responses and steps takennote over MA: Benchmark responsesnote over MA: Make final decision@enduml"
    },
    {
      "id": "copied-1699797991293-07537a68-1c7e-4edb-a72f-2d82015c490f",
      "label": "Understood! As I'm an expert in the .puml syntax i will correct it"
    },
    {
      "id": "copied-1699797991293-1cc45118-72ee-4efe-95d8-06e8c02fb4c0",
      "label": "The following is a .puml content generated by an agent. Please critically review it and correct any mistakes, especially ensuring it strictly adheres to .puml syntax and does not contain any elements from other diagramming languages like Mermaid"
    },
    {
      "id": "copied-1699797991293-2e419e7e-a540-4c9a-af4e-5110e54fad96",
      "label": "system"
    },
    {
      "id": "copied-1699797991293-757e7439-08f8-4cea-afac-c25b01167d32",
      "label": "user"
    },
    {
      "id": "copied-1699797991293-c7d1c0a4-6365-44d6-be0c-bd3fc5436b85",
      "label": "user"
    }
  ],
  "edges": [
    {
      "from": "07537a68-1c7e-4edb-a72f-2d82015c490f",
      "id": "67194bdc-f1f3-417f-9778-4d163c8b82d1",
      "to": "757e7439-08f8-4cea-afac-c25b01167d32"
    },
    {
      "from": "1cc45118-72ee-4efe-95d8-06e8c02fb4c0",
      "id": "1329a8be-e4e2-42fd-bdb6-2057f9c320d3",
      "to": "2e419e7e-a540-4c9a-af4e-5110e54fad96"
    },
    {
      "from": "2e419e7e-a540-4c9a-af4e-5110e54fad96",
      "id": "33312b2e-b683-4489-b471-e2d1ca03d21a",
      "to": "07537a68-1c7e-4edb-a72f-2d82015c490f"
    },
    {
      "from": "757e7439-08f8-4cea-afac-c25b01167d32",
      "id": "f5b47e5e-4121-44a3-8b29-97bfe2069148",
      "to": "eac6de73-9726-43b7-9441-f8e319a972e6"
    },
    {
      "from": "c7d1c0a4-6365-44d6-be0c-bd3fc5436b85",
      "id": "f4e2015e-e7f1-4e03-b3c6-ee82986533ca",
      "to": "1cc45118-72ee-4efe-95d8-06e8c02fb4c0"
    },
    {
      "from": "copied-1699797991293-757e7439-08f8-4cea-afac-c25b01167d32",
      "id": "copied-1699797991293-f5b47e5e-4121-44a3-8b29-97bfe2069148",
      "to": "copied-1699797991293-eac6de73-9726-43b7-9441-f8e319a972e6"
    },
    {
      "from": "copied-1699797991293-07537a68-1c7e-4edb-a72f-2d82015c490f",
      "id": "copied-1699797991293-67194bdc-f1f3-417f-9778-4d163c8b82d1",
      "to": "copied-1699797991293-757e7439-08f8-4cea-afac-c25b01167d32"
    },
    {
      "from": "copied-1699797991293-2e419e7e-a540-4c9a-af4e-5110e54fad96",
      "id": "copied-1699797991293-33312b2e-b683-4489-b471-e2d1ca03d21a",
      "to": "copied-1699797991293-07537a68-1c7e-4edb-a72f-2d82015c490f"
    },
    {
      "from": "copied-1699797991293-1cc45118-72ee-4efe-95d8-06e8c02fb4c0",
      "id": "copied-1699797991293-1329a8be-e4e2-42fd-bdb6-2057f9c320d3",
      "to": "copied-1699797991293-2e419e7e-a540-4c9a-af4e-5110e54fad96"
    },
    {
      "from": "copied-1699797991293-c7d1c0a4-6365-44d6-be0c-bd3fc5436b85",
      "id": "copied-1699797991293-f4e2015e-e7f1-4e03-b3c6-ee82986533ca",
      "to": "copied-1699797991293-1cc45118-72ee-4efe-95d8-06e8c02fb4c0"
    }
  ]
}
"""

b_des = BlueprintDesigner()

graph_data = b_des.load_json_graph(json_graph_data)

# b_des.process_graph_with_gpt(graph_data)
# Step 1: Count Trees

tree = b_des.build_tree_structure(graph_data["nodes"], graph_data["edges"])
tree

tree_count = b_des.tree_counter(tree)

b_des.logger.info(f"Tree count: {tree_count}")

root_nodes = b_des.provide_root_nodes(tree)
# todo : retry new apporach

b_des.identify_agents(root_nodes,tree)

# Step 2: Analyze Hierarchy and Variables
variable_hierarchy = b_des.analyze_hierarchy_and_variables(tree)
variable_hierarchy


# variable_hierarchy = b_des.analyze_hierarchy_and_variables(graph_data)
b_des.logger.debug(f"Variable Hierarchy: {variable_hierarchy}")

# Step 3: Design Blueprint
blueprint = b_des.design_blueprint(variable_hierarchy)
blueprint
b_des.logger.debug(f"Blueprint: {blueprint}")

# Step 4: Prepare GPT Format
gpt_call = b_des.prepare_gpt_format(b_des.provide_root_nodes(graph_data), graph_data)

