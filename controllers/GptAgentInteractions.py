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
from controllers.BigQueryHandler import BigQueryHandler

load_dotenv()

logging.basicConfig(level=logging.DEBUG)  # You can change the level as needed.
logger = logging.getLogger(__name__)



class GptAgentInteractions(BigQueryHandler):

    def __init__(self, dataset_id):
        super().__init__(dataset_id)

    def get_node_type(self, node):
        if 'user' in node['label'].lower():
            return 'user'
        elif 'system' in node['label'].lower():
            return 'system'
        else:
            return 'content'

    def extract_and_send_to_gpt(self, processed_data):

        actual_data = processed_data.get("processed_data", {})
        messages = actual_data.get("messages", [])

        post_data = {
            "model": os.getenv("MODEL"),
            "messages": messages
        }

        # post_data = {
        #     "model": os.getenv("MODEL"),
        #     "messages": processed_data["messages"]
        # }

        # Send POST request to GPT
        response = requests.post(self.openai_base_url, headers=self.headers, json=post_data)

        # Check if the request was successful and extract PUML content
        if response.status_code == 200:
            agent_content = response.json()["choices"][0]["message"]["content"]
            return agent_content
        else:
            raise Exception(f"Error in GPT request: {response.status_code}, {response.text}")

    def translate_graph_to_gpt_sequence(self, graph_data):
        nodes = graph_data["nodes"]
        edges = graph_data["edges"]

        # Build a mapping of node IDs to nodes
        node_mapping = {node['id']: node for node in nodes}

        # Initialize the data structure
        translated_data = {
            "model": os.getenv("MODEL"),
            "messages": []
        }

        # Define valid transitions
        valid_transitions = {
            'user': 'content',
            'content': 'system',
            'system': 'content'
        }

        # Start from 'user' nodes and follow the valid transitions
        current_expected = 'user'

        for edge in edges:
            from_node = node_mapping[edge['from']]
            to_node = node_mapping[edge['to']]

            from_node_type = self.get_node_type(from_node)
            to_node_type = self.get_node_type(to_node)

            # Validate the transition
            if from_node_type == current_expected and valid_transitions.get(from_node_type) == to_node_type:
                # Append the content of the 'to' node if it's a 'content' node
                if to_node_type == 'content':
                    translated_data['messages'].append({
                        "role": from_node_type,
                        "content": to_node['label']
                    })
                # Update the expected type for the next node
                current_expected = to_node_type

            # Reset to 'user' after a 'system' to 'content' transition
            if from_node_type == 'system' and to_node_type == 'content':
                current_expected = 'user'

        # Serialize data to json
        json_data = json.dumps(translated_data, indent=4)
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        json_filename = f"processed_graph_{timestamp}.json"

        with open(json_filename, "w") as json_file:
            json_file.write(json_data)

        return {
            'bigquery_errors': {'node_errors': [], 'edge_errors': []},
            'processed_data': translated_data
        }

    def extract_gpt_interactions_before_save(self, graph_data, graph_id):

        nodes_for_bq, edges_for_bq = self.translate_graph_data_for_bigquery(graph_data, graph_id)
        # Log the transformed data for debugging
        logger.debug(f"Transformed Nodes: {nodes_for_bq}")
        logger.debug(f"Transformed Edges: {edges_for_bq}")

        graph_data_as_dicts = {
            "nodes": nodes_for_bq,
            "edges": edges_for_bq
        }

        logger.debug(f"graph_data_as_dicts: {graph_data_as_dicts}")

        # Pass the dictionaries to the workflow logic
        processed_data = self.translate_graph_to_gpt_sequence(graph_data_as_dicts)

        processed_data = processed_data["processed_data"]
        logger.debug(f"processed_data: {processed_data}")
        agent_content = self.extract_and_send_to_gpt(processed_data)
        logger.debug(f"agent_content: {agent_content}")

    def get_last_content_node(self, edges, nodes):
        # Assuming edges are ordered
        last_edge = edges[-1]
        last_node_id = last_edge['to']

        logger.debug(f"get_last_content_node, last_node_id : {last_node_id}")

        for node in nodes:
            if node['id'] == last_node_id:
                return node
        return None

    def process_gpt_response_and_update_graph(self, gpt_response, graph_data):
        last_content_node = self.get_last_content_node(graph_data['edges'], graph_data['nodes'])

        logger.debug(f"process_gpt_response_and_update_graph, last_content_node : {last_content_node}")

        # Create a new node with GPT response
        # Create a new node with GPT response
        new_node_id = f"agent_response_based_on{last_content_node['id']}"  # generate a unique ID for the new node
        new_node = {
            'id': new_node_id,
            'label': gpt_response,
        }

        # Create a new edge from the last content node to the new node
        new_edge = {
            'from': last_content_node['id'],
            'to': new_node_id,
        }

        graph_data['nodes'].append(new_node)
        graph_data['edges'].append(new_edge)

        return graph_data
    # Add the process_recursive_graph method
    def process_recursive_graph(self, graph_data):
        # Update valid transitions to include 'variable' nodes
        valid_transitions = {
            'user': 'content',
            'content': ['system', 'variable'],
            'system': 'content',
            'variable': 'content'
        }

        # Process the graph in a sequence
        processed_data = {"messages": []}
        variable_content = None

        for edge in graph_data["edges"]:
            from_node = graph_data["nodes"][edge['from']]
            to_node = graph_data["nodes"][edge['to']]

            from_node_type = self.get_node_type(from_node)
            to_node_type = self.get_node_type(to_node)

            # Check for valid transitions
            if valid_transitions[from_node_type] == to_node_type or to_node_type in valid_transitions[from_node_type]:
                if from_node_type == 'variable':
                    # Replace 'variable' node content with the previous GPT API response
                    from_node['label'] = variable_content

                # Add the interaction to the processed data
                processed_data['messages'].append({
                    "role": from_node_type,
                    "content": from_node['label']
                })

                # If the 'to' node is a 'variable', get response from GPT API
                if to_node_type == 'variable':
                    gpt_response = self.get_gpt_response(processed_data)
                    variable_content = gpt_response

        return processed_data

    # New method to interact with the GPT API
    def get_gpt_response(self, processed_data):
        post_data = {
            "model": os.getenv("MODEL"),
            "messages": processed_data["messages"]
        }
        response = requests.post(self.openai_base_url, headers=self.headers, json=post_data)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            raise Exception(f"Error in GPT request: {response.status_code}, {response.text}")

# GptAgentInteractions
#
# help(GptAgentInteractions)
