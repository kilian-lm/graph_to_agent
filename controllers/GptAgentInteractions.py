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

load_dotenv()


class GptAgentInteractions():

    def __init__(self, dataset_id):
        # First logging
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        print(timestamp)
        self.log_file = f'{timestamp}_gpt_agent_interactions.log'
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
        self.dataset_id = dataset_id
        bq_client_secrets = os.getenv('BQ_CLIENT_SECRETS')

        try:
            bq_client_secrets_parsed = json.loads(bq_client_secrets)
            self.bq_client_secrets = Credentials.from_service_account_info(bq_client_secrets_parsed)
            self.bigquery_client = bigquery.Client(credentials=self.bq_client_secrets,
                                                   project=self.bq_client_secrets.project_id)
            self.logger.info("BigQuery client successfully initialized.")
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse BQ_CLIENT_SECRETS environment variable: {e}")
            raise
        except Exception as e:
            self.logger.error(f"An error occurred while initializing the BigQuery client: {e}")
            raise

    def create_dataset_if_not_exists(self):
        dataset_ref = self.bigquery_client.dataset(self.dataset_id)
        try:
            self.bigquery_client.get_dataset(dataset_ref)
            self.logger.info(f"Dataset {self.dataset_id} already exists.")
        except Exception as e:
            try:
                dataset = bigquery.Dataset(dataset_ref)
                self.bigquery_client.create_dataset(dataset)
                self.logger.info(f"Dataset {self.dataset_id} created.")
            except Exception as ex:
                self.logger.error(f"Failed to create dataset {self.dataset_id}: {ex}")
                raise

    def create_table_if_not_exists(self, table_id, schema):
        table_ref = self.bigquery_client.dataset(self.dataset_id).table(table_id)
        try:
            self.bigquery_client.get_table(table_ref)
            self.logger.info(f"Table {table_id} already exists.")
        except Exception as e:
            try:
                table = bigquery.Table(table_ref, schema=schema)
                self.bigquery_client.create_table(table)
                self.logger.info(f"Table {table_id} created.")
            except Exception as ex:
                self.logger.error(f"Failed to create table {table_id}: {ex}")
                raise

    def get_node_schema(self):
        return [
            bigquery.SchemaField("graph_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("label", "STRING", mode="REQUIRED")
        ]

    def get_edge_schema(self):
        return [
            bigquery.SchemaField("graph_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("from", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("to", "STRING", mode="REQUIRED")
        ]

    def get_available_graphs(self):
        # Query to get distinct graph_ids from the nodes_table
        query = f"SELECT DISTINCT graph_id FROM `{self.dataset_id}.nodes_table`"
        query_job = self.bigquery_client.query(query)
        results = query_job.result()

        return [{"graph_id": row["graph_id"], "graph_name": row["graph_id"]} for row in results]

    def load_graph_data_by_id(self, graph_id):
        nodes_table_ref = self.bigquery_client.dataset(self.dataset_id).table("nodes_table")
        edges_table_ref = self.bigquery_client.dataset(self.dataset_id).table("edges_table")

        # Fetch nodes for given graph_id
        nodes_query = f"SELECT * FROM `{self.dataset_id}.nodes_table` WHERE graph_id = '{graph_id}'"
        nodes_query_job = self.bigquery_client.query(nodes_query)
        nodes_results = nodes_query_job.result()
        nodes = [{"id": row['id'], "label": row['label']} for row in nodes_results]

        self.logger.info(f"nodes loaded by graph id {nodes} already exists.")

        # Fetch edges for given graph_id
        edges_query = f"SELECT * FROM `{self.dataset_id}.edges_table` WHERE graph_id = '{graph_id}'"
        edges_query_job = self.bigquery_client.query(edges_query)
        edges_results = edges_query_job.result()
        edges = [{"from": row['from'], "to": row['to']} for row in edges_results]

        return {"nodes": nodes, "edges": edges}

    def translate_graph_data_for_bigquery(self, graph_data, graph_id):
        # Extract nodes and edges from the graph data
        raw_nodes = graph_data.get('nodes', [])
        raw_edges = graph_data.get('edges', [])

        # Translate nodes
        nodes_for_bq = [
            {
                "graph_id": graph_id,
                "id": node.get('id'),
                "label": node.get('label')
            }
            for node in raw_nodes
        ]

        self.logger.info(f"nodes_for_bq: {nodes_for_bq}")

        # Translate edges
        edges_for_bq = [
            {
                "graph_id": graph_id,
                "from": edge.get('from'),
                "to": edge.get('to')
            }
            for edge in raw_edges
        ]

        self.logger.info(f"edges_for_bq: {edges_for_bq}")

        return nodes_for_bq, edges_for_bq

    def get_node_type(self, node):
        if 'user' in node['label'].lower():
            return 'user'
        elif 'system' in node['label'].lower():
            return 'system'
        else:
            return 'content'

    def translate_graph_to_gpt_sequence(self, graph_data):
        nodes = graph_data["nodes"]
        edges = graph_data["edges"]


        # Build a mapping of node IDs to nodes
        node_mapping = {node['id']: node for node in nodes}
        self.logger.info(f"node_map: {node_mapping}")

        # Initialize the data structure
        translated_data = {
            "model": os.getenv("MODEL"),
            "messages": []
        }

        self.logger.info(f"translated_data: {translated_data}")

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

            self.logger.info(f"from_node: {from_node}")
            self.logger.info(f"to_node: {to_node}")

            from_node_type = self.get_node_type(from_node)
            to_node_type = self.get_node_type(to_node)

            self.logger.info(f"from_node_type: {from_node_type}")
            self.logger.info(f"to_node_type: {to_node_type}")



        # Serialize data to json
        json_data = json.dumps(translated_data, indent=4)
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"temp_local/processed_graph_{timestamp}.json"

        # Check if the temp_local directory exists
        if not os.path.exists('temp_local'):
            os.makedirs('temp_local')

        # Save the JSON data to the file
        with open(filename, 'w') as json_file:
            json_file.write(json_data)

        breakpoint()  # todo ::


        return {
            'bigquery_errors': {'node_errors': [], 'edge_errors': []},
            'processed_data': translated_data
        }

    def extract_and_send_to_gpt(self, processed_data):

        actual_data = processed_data.get("processed_data", {})
        messages = actual_data.get("messages", [])

        post_data = {
            "model": os.getenv("MODEL"),
            "messages": messages
        }

        # Send POST request to GPT
        response = requests.post(self.openai_base_url, headers=self.headers, json=post_data)

        if response.status_code == 200:
            agent_content = response.json()["choices"][0]["message"]["content"]
            return agent_content
        else:
            raise Exception(f"Error in GPT request: {response.status_code}, {response.text}")

    def extract_gpt_interactions_before_save(self, graph_data, graph_id):

        nodes_for_bq, edges_for_bq = self.translate_graph_data_for_bigquery(graph_data, graph_id)
        # Log the transformed data for debugging
        self.logger.info(f"extract_gpt_interactions_before_save, Transformed Nodes: {nodes_for_bq}")
        self.logger.info(f"extract_gpt_interactions_before_save, Transformed Edges: {edges_for_bq}")

        graph_data_as_dicts = {
            "nodes": nodes_for_bq,
            "edges": edges_for_bq
        }

        self.logger.info(f"extract_gpt_interactions_before_save, graph_data_as_dicts: {graph_data_as_dicts}")

        # Pass the dictionaries to the workflow logic
        processed_data = self.translate_graph_to_gpt_sequence(graph_data_as_dicts)

        processed_data = processed_data["processed_data"]
        self.logger.info(f"processed_data: {processed_data}")
        agent_content = self.extract_and_send_to_gpt(processed_data)
        self.logger.info(f"agent_content: {agent_content}")

    def get_last_content_node(self, edges, nodes):
        # Assuming edges are ordered
        last_edge = edges[-1]
        last_node_id = last_edge['to']

        self.logger.info(f"get_last_content_node, last_node_id : {last_node_id}")

        for node in nodes:
            if node['id'] == last_node_id:
                return node
        return None

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

    def process_gpt_response_and_update_graph(self, gpt_response, graph_data):
        last_content_node = self.get_last_content_node(graph_data['edges'], graph_data['nodes'])

        self.logger.info(f"process_gpt_response_and_update_graph, last_content_node : {last_content_node}")

        # Generate a unique ID for the new node
        new_node_id = f"agent_response_based_on{last_content_node['id']}"
        new_node = {
            'id': new_node_id,
            'label': gpt_response,
        }

        self.logger.info(f"process_gpt_response_and_update_graph, new_node : {new_node}")

        # Check if a node with the new ID already exists
        existing_node_ids = {node['id'] for node in graph_data['nodes']}
        if new_node_id not in existing_node_ids:
            graph_data['nodes'].append(new_node)
            # Create a new edge from the last content node to the new node
            new_edge = {
                'from': last_content_node['id'],
                'to': new_node_id,
            }
            graph_data['edges'].append(new_edge)
            self.logger.info(f"process_gpt_response_and_update_graph, new_edge : {new_edge}")
        else:
            self.logger.info(f"Node with ID {new_node_id} already exists. Skipping node and edge addition.")

        self.logger.info(f"process_gpt_response_and_update_graph, graph_data : {graph_data}")

        # debugging:
        graph_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        self.save_graph_data(graph_data, graph_id)
        return graph_data

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

    # def populate_variable_nodes(self, graph_data, gpt_response, recursion_depth=0):
    #     import re
    #
    #     nodes = graph_data["nodes"]
    #     edges = graph_data["edges"]
    #
    #     # Regular expression to find @variable placeholders with optional suffix
    #     variable_pattern = re.compile(r'@variable(?:_(\d+))?')
    #
    #     # Track the versions of variables
    #     variable_versions = {}
    #
    #     for node in nodes:
    #         self.logger.info(f"Processing node with id {node['id']} and label {node['label']}")
    #
    #         content = node['label']
    #         matches = list(variable_pattern.finditer(content))
    #         matches.sort(key=lambda match: int(match.group(1)) if match.group(1) else 0)
    #
    #         for match in matches:
    #             suffix = match.group(1)
    #             variable_full = match.group(0)
    #
    #             if suffix:
    #                 self.logger.info(f"Found versioned variable with suffix {suffix} in node {node['id']}")
    #                 self.logger.info(f"Found base @variable in node {node['id']}")
    #
    #                 # This is a versioned variable
    #                 required_version = int(suffix)
    #                 versioned_node_id = f"{node['id']}_v{required_version}"
    #
    #                 if versioned_node_id in variable_versions:
    #                     # Use the versioned content
    #                     previous_content = variable_versions[versioned_node_id]
    #                     updated_content = content.replace(variable_full, previous_content)
    #                 else:
    #                     # Recursive call to resolve variable
    #                     updated_graph = self.populate_variable_nodes(graph_data, gpt_response, recursion_depth + 1)
    #                     updated_node = next(node for node in updated_graph['nodes'] if node['id'] == versioned_node_id)
    #                     previous_content = updated_node['label']
    #                     updated_content = content.replace(variable_full, previous_content)
    #
    #                 # Update node label with resolved content
    #                 node['label'] = updated_content
    #                 node['id'] = versioned_node_id  # Update node ID with version
    #                 variable_versions[node['id']] = updated_content
    #             else:
    #                 # It's the base @variable
    #                 updated_content = content.replace(variable_full, gpt_response)
    #                 node['label'] = updated_content
    #                 self.logger.info(f"Node {node['id']} updated to {node['label']}")
    #
    #                 versioned_node_id = f"{node['id']}_v{recursion_depth + 1}"
    #                 node['id'] = versioned_node_id
    #                 variable_versions[node['id']] = updated_content
    #
    #     # Update edges to point to the new versioned node IDs
    #     for edge in edges:
    #         if edge['from'] in variable_versions:
    #             edge['from'] += f"_v{recursion_depth + 1}"
    #         if edge['to'] in variable_versions:
    #             edge['to'] += f"_v{recursion_depth + 1}"
    #
    #     return graph_data

    # def populate_variable_nodes(self, graph_data, gpt_response, recursion_depth=0):
    #     import re
    #
    #     nodes = graph_data["nodes"]
    #     edges = graph_data["edges"]
    #
    #     # Regular expression to find @variable placeholders with optional suffix
    #     variable_pattern = re.compile(r'@variable(?:_(\d+))?')
    #
    #     # Track the versions of variables
    #     variable_versions = {}
    #
    #     for node in nodes:
    #         self.logger.info(f"Processing node with id {node['id']} and label {node['label']}")
    #
    #         content = node['label']
    #         matches = list(variable_pattern.finditer(content))
    #         matches.sort(key=lambda match: int(match.group(1)) if match.group(1) else 0)
    #
    #         for match in matches:
    #             suffix = match.group(1)
    #             variable_full = match.group(0)
    #
    #             if suffix:
    #                 self.logger.info(f"Found versioned variable with suffix {suffix} in node {node['id']}")
    #                 self.logger.info(f"Found base @variable in node {node['id']}")
    #
    #                 # This is a versioned variable
    #                 required_version = int(suffix)
    #                 versioned_node_id = f"{node['id']}_v{required_version}"
    #
    #                 if versioned_node_id in variable_versions:
    #                     # Use the versioned content
    #                     previous_content = variable_versions[versioned_node_id]
    #                     updated_content = content.replace(variable_full, previous_content)
    #                 else:
    #                     # Recursive call to resolve variable
    #                     processed_data = self.translate_graph_to_gpt_sequence(graph_data)
    #                     self.logger.info(f"populate_variable_nodes, processed_data {processed_data}")
    #
    #                     gpt_response = self.get_gpt_response(processed_data)
    #                     self.populate_variable_nodes(graph_data, gpt_response, recursion_depth + 1)
    #                     self.logger.info(f"Populating variable nodes at recursion depth {recursion_depth}")
    #
    #                 # Update node label with resolved content
    #                 node['label'] = updated_content
    #                 node['id'] = versioned_node_id  # Update node ID with version
    #                 variable_versions[node['id']] = updated_content
    #             else:
    #                 # It's the base @variable
    #                 updated_content = content.replace(variable_full, gpt_response)
    #                 node['label'] = updated_content
    #                 self.logger.info(f"Node {node['id']} updated to {node['label']}")
    #
    #                 versioned_node_id = f"{node['id']}_v{recursion_depth + 1}"
    #                 node['id'] = versioned_node_id
    #                 variable_versions[node['id']] = updated_content
    #
    #     # Update edges to point to the new versioned node IDs
    #     for edge in edges:
    #         if edge['from'] in variable_versions:
    #             edge['from'] += f"_v{recursion_depth + 1}"
    #         if edge['to'] in variable_versions:
    #             edge['to'] += f"_v{recursion_depth + 1}"
    #
    #     # Save the updated nodes and edges
    #     self.save_graph_data(nodes, edges)
    #
    #     self.logger.info(f"Saving updated graph data with nodes: {graph_data['nodes']} and edges: {graph_data['edges']}")
    #
    #     return graph_data

    def save_graph_data(self, graph_data, graph_id):
        try:
            # Check and create dataset if it doesn't exist
            self.create_dataset_if_not_exists()

            nodes_table_ref = self.bigquery_client.dataset(self.dataset_id).table("nodes_table")
            edges_table_ref = self.bigquery_client.dataset(self.dataset_id).table("edges_table")

            # Check and create nodes table if it doesn't exist
            self.create_table_if_not_exists("nodes_table", self.get_node_schema())

            # Check and create edges table if it doesn't exist
            self.create_table_if_not_exists("edges_table", self.get_edge_schema())

            # Retrieve the tables and their schemas
            nodes_table = self.bigquery_client.get_table(nodes_table_ref)
            edges_table = self.bigquery_client.get_table(edges_table_ref)

            # Use the translator function to transform the data
            nodes_for_bq, edges_for_bq = self.translate_graph_data_for_bigquery(graph_data, graph_id)

            # Log the transformed data for debugging
            self.logger.info(f"controller save_graph_data, Transformed Nodes: {nodes_for_bq}")
            self.logger.info(f"controller save_graph_data, Transformed Edges: {edges_for_bq}")

            # Insert nodes and pass in the schema explicitly
            errors_nodes = self.bigquery_client.insert_rows(nodes_table, nodes_for_bq,
                                                            selected_fields=nodes_table.schema)
            if errors_nodes:
                self.logger.info(f"Encountered errors while inserting nodes: {errors_nodes}")

            # Insert edges and pass in the schema explicitly
            errors_edges = self.bigquery_client.insert_rows(edges_table, edges_for_bq,
                                                            selected_fields=edges_table.schema)
            if errors_edges:
                self.logger.info(f"Encountered errors while inserting edges: {errors_edges}")

            # Compile all errors
            all_errors = {
                "node_errors": errors_nodes,
                "edge_errors": errors_edges
            }

            if errors_nodes or errors_edges:
                self.logger.error("Errors occurred during the saving of graph data.")

            # Save the transformed data as dictionaries for the workflow
            # This assumes that the data is already in a dictionary format suitable for the workflow
            graph_data_as_dicts = {
                "nodes": nodes_for_bq,
                "edges": edges_for_bq
            }

            self.logger.info(f"graph_data_as_dicts: {graph_data_as_dicts}")

            # Return both BigQuery errors and processed data
            return {
                "bigquery_errors": all_errors,
            }

        except Exception as e:
            self.logger.error("An unexpected error occurred during save_graph_data:")
        raise


# gpt_agent_interactions = GptAgentInteractions('graph_to_agent')

#
# help(GptAgentInteractions)
