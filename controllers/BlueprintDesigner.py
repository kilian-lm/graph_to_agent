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

    def __init__(self, dataset_id):
        # First logging
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        print(timestamp)
        self.log_file = f'{timestamp}_engine_room.log'
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

    def provide_root_nodes(self, graph_data):
        root_nodes = [node['id'] for node in graph_data['nodes'] if
                      not any(edge['to'] == node['id'] for edge in graph_data['edges'])]

        return root_nodes

    def tree_counter(self, graph_data):
        """
        Counts the number of root nodes (trees) in the given graph data.

        Parameters:
        graph_data (dict): The graph data containing nodes and edges.

        Returns:
        int: The number of identified root nodes (trees) in the graph.
        """
        # Check if graph_data is valid
        if not isinstance(graph_data, dict) or 'nodes' not in graph_data or 'edges' not in graph_data:
            self.logger.error("Invalid graph data format.")
            return 0

        try:
            identified_root_nodes = self.provide_root_nodes(graph_data)
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
                variable_hierarchy[variable_number] = (node_id, depth)

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
        blueprint = {}
        # Sort variables by their order in the hierarchy
        for variable_number, (node_id, depth) in sorted(variable_hierarchy.items()):
            blueprint[variable_number] = {
                'node_id': node_id,
                'depth': depth
            }
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

    def update_and_return_graph(self, original_graph_data, populated_graph_data):
        """
        Updates the original graph data with the populated graph data and
        returns the entire graph in .vis.js format.

        Parameters:
        original_graph_data (dict): The original graph data.
        populated_graph_data (dict): The graph data with populated variables.

        Returns:
        dict: The updated graph data in .vis.js format.
        """

        # Extract original IDs and create a mapping to updated nodes
        updated_nodes = {}
        for node in populated_graph_data['nodes']:
            original_id = node['id'].split('_v')[0]  # Extract original ID before version suffix
            updated_nodes[original_id] = node

        # Update the original graph with the populated data
        for node in original_graph_data['nodes']:
            node_id = node['id']
            if node_id in updated_nodes:
                # Update label with populated data
                node['label'] = updated_nodes[node_id]['label']

        # Return the updated graph in .vis.js format
        return {
            'nodes': original_graph_data['nodes'],
            'edges': original_graph_data['edges']
        }

    def process_graph_with_gpt(self, graph_data):
        # Step 1: Count Trees
        tree_count = self.tree_counter(graph_data)
        self.logger.info(f"Tree count: {tree_count}")

        # Step 2: Analyze Hierarchy and Variables
        variable_hierarchy = self.analyze_hierarchy_and_variables(graph_data)
        self.logger.debug(f"Variable Hierarchy: {variable_hierarchy}")

        # Step 3: Design Blueprint
        blueprint = self.design_blueprint(variable_hierarchy)
        self.logger.debug(f"Blueprint: {blueprint}")

        # Step 4: Prepare GPT Format
        gpt_call = self.prepare_gpt_format(self.provide_root_nodes(graph_data), graph_data)

        # Step 5: Get GPT Response and Populate Nodes
        try:
            gpt_response = self.get_gpt_response(gpt_call)
            populated_graph = self.populate_variable_nodes(graph_data, gpt_response)

            # Step 6: Update and Return the Graph in .vis.js Format
            updated_graph_data = self.update_and_return_graph(graph_data, populated_graph)
            return updated_graph_data

        except Exception as e:
            self.logger.error(f"Error processing graph with GPT: {e}")
            return None
