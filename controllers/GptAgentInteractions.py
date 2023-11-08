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

# from controllers.BigQueryHandler import BigQueryHandler

load_dotenv()

logging.basicConfig(level=logging.DEBUG)  # You can change the level as needed.
logger = logging.getLogger(__name__)


class GptAgentInteractions:

    def __init__(self, dataset_id):
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
            logger.info("BigQuery client successfully initialized.")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse BQ_CLIENT_SECRETS environment variable: {e}")
            raise
        except Exception as e:
            logger.error(f"An error occurred while initializing the BigQuery client: {e}")
            raise

    def create_dataset_if_not_exists(self):
        dataset_ref = self.bigquery_client.dataset(self.dataset_id)
        try:
            self.bigquery_client.get_dataset(dataset_ref)
            logger.info(f"Dataset {self.dataset_id} already exists.")
        except Exception as e:
            try:
                dataset = bigquery.Dataset(dataset_ref)
                self.bigquery_client.create_dataset(dataset)
                logger.info(f"Dataset {self.dataset_id} created.")
            except Exception as ex:
                logger.error(f"Failed to create dataset {self.dataset_id}: {ex}")
                raise

    def create_table_if_not_exists(self, table_id, schema):
        table_ref = self.bigquery_client.dataset(self.dataset_id).table(table_id)
        try:
            self.bigquery_client.get_table(table_ref)
            logger.info(f"Table {table_id} already exists.")
        except Exception as e:
            try:
                table = bigquery.Table(table_ref, schema=schema)
                self.bigquery_client.create_table(table)
                logger.info(f"Table {table_id} created.")
            except Exception as ex:
                logger.error(f"Failed to create table {table_id}: {ex}")
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

        logger.debug(f"nodes_for_bq: {nodes_for_bq}")

        # Translate edges
        edges_for_bq = [
            {
                "graph_id": graph_id,
                "from": edge.get('from'),
                "to": edge.get('to')
            }
            for edge in raw_edges
        ]

        logger.debug(f"edges_for_bq: {edges_for_bq}")

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
        filename = f"temp_local/processed_graph_{timestamp}.json"

        # Check if the temp_local directory exists
        if not os.path.exists('temp_local'):
            os.makedirs('temp_local')

        # Save the JSON data to the file
        with open(filename, 'w') as json_file:
            json_file.write(json_data)

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
        logger.debug(f"extract_gpt_interactions_before_save, Transformed Nodes: {nodes_for_bq}")
        logger.debug(f"extract_gpt_interactions_before_save, Transformed Edges: {edges_for_bq}")

        graph_data_as_dicts = {
            "nodes": nodes_for_bq,
            "edges": edges_for_bq
        }

        logger.debug(f"extract_gpt_interactions_before_save, graph_data_as_dicts: {graph_data_as_dicts}")

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

        # Generate a unique ID for the new node
        new_node_id = f"agent_response_based_on{last_content_node['id']}"
        new_node = {
            'id': new_node_id,
            'label': gpt_response,
        }

        logger.debug(f"process_gpt_response_and_update_graph, new_node : {new_node}")

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
            logger.debug(f"process_gpt_response_and_update_graph, new_edge : {new_edge}")
        else:
            logger.warning(f"Node with ID {new_node_id} already exists. Skipping node and edge addition.")

        logger.debug(f"process_gpt_response_and_update_graph, graph_data : {graph_data}")

        # debugging:
        graph_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        self.save_graph_data(graph_data, graph_id)
        return graph_data

    # def process_gpt_response_and_update_graph(self, gpt_response, graph_data):
    #     last_content_node = self.get_last_content_node(graph_data['edges'], graph_data['nodes'])
    #
    #     logger.debug(f"process_gpt_response_and_update_graph, last_content_node : {last_content_node}")
    #
    #     # Create a new node with GPT response
    #     new_node_id = f"agent_response_based_on{last_content_node['id']}"  # generate a unique ID for the new node
    #     new_node = {
    #         'id': new_node_id,
    #         'label': gpt_response,
    #     }
    #
    #     logger.debug(f"process_gpt_response_and_update_graph, new_node : {new_node}")
    #
    #     # Create a new edge from the last content node to the new node
    #     new_edge = {
    #         'from': last_content_node['id'],
    #         'to': new_node_id,
    #     }
    #
    #     logger.debug(f"process_gpt_response_and_update_graph, new_edge : {new_edge}")
    #
    #     graph_data['nodes'].append(new_node)
    #     graph_data['edges'].append(new_edge)
    #
    #     logger.debug(f"process_gpt_response_and_update_graph, graph_data : {graph_data}")
    #
    #     # debugging:
    #     graph_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    #
    #     self.save_graph_data(graph_data, graph_id)
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
            logger.debug(f"controller save_graph_data, Transformed Nodes: {nodes_for_bq}")
            logger.debug(f"controller save_graph_data, Transformed Edges: {edges_for_bq}")

            # Insert nodes and pass in the schema explicitly
            errors_nodes = self.bigquery_client.insert_rows(nodes_table, nodes_for_bq,
                                                            selected_fields=nodes_table.schema)
            if errors_nodes:
                logger.warning(f"Encountered errors while inserting nodes: {errors_nodes}")

            # Insert edges and pass in the schema explicitly
            errors_edges = self.bigquery_client.insert_rows(edges_table, edges_for_bq,
                                                            selected_fields=edges_table.schema)
            if errors_edges:
                logger.warning(f"Encountered errors while inserting edges: {errors_edges}")

            # Compile all errors
            all_errors = {
                "node_errors": errors_nodes,
                "edge_errors": errors_edges
            }

            if errors_nodes or errors_edges:
                logger.error("Errors occurred during the saving of graph data.")

            # Save the transformed data as dictionaries for the workflow
            # This assumes that the data is already in a dictionary format suitable for the workflow
            graph_data_as_dicts = {
                "nodes": nodes_for_bq,
                "edges": edges_for_bq
            }

            logger.debug(f"graph_data_as_dicts: {graph_data_as_dicts}")

            # Return both BigQuery errors and processed data
            return {
                "bigquery_errors": all_errors,
            }

        except Exception as e:
            logger.exception("An unexpected error occurred during save_graph_data:")
        raise

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

        logger.info(f"nodes loaded by graph id {nodes} already exists.")

        # Fetch edges for given graph_id
        edges_query = f"SELECT * FROM `{self.dataset_id}.edges_table` WHERE graph_id = '{graph_id}'"
        edges_query_job = self.bigquery_client.query(edges_query)
        edges_results = edges_query_job.result()
        edges = [{"from": row['from'], "to": row['to']} for row in edges_results]

        return {"nodes": nodes, "edges": edges}
    # Add the process_recursive_graph method

# def process_recursive_graph(self, graph_data):  # ToDo :: Implementation
#         # Update valid transitions to include 'variable' nodes
#         valid_transitions = {
#             'user': 'content',
#             'content': ['system', 'variable'],
#             'system': 'content',
#             'variable': 'content'
#         }
#
#         # Process the graph in a sequence
#         processed_data = {"messages": []}
#         variable_content = None
#
#         for edge in graph_data["edges"]:
#             from_node = graph_data["nodes"][edge['from']]
#             to_node = graph_data["nodes"][edge['to']]
#
#             from_node_type = self.get_node_type(from_node)
#             to_node_type = self.get_node_type(to_node)
#
#             # Check for valid transitions
#             if valid_transitions[from_node_type] == to_node_type or to_node_type in valid_transitions[from_node_type]:
#                 if from_node_type == 'variable':
#                     # Replace 'variable' node content with the previous GPT API response
#                     from_node['label'] = variable_content
#
#                 # Add the interaction to the processed data
#                 processed_data['messages'].append({
#                     "role": from_node_type,
#                     "content": from_node['label']
#                 })
#
#                 # If the 'to' node is a 'variable', get response from GPT API
#                 if to_node_type == 'variable':
#                     gpt_response = self.get_gpt_response(processed_data)
#                     variable_content = gpt_response
#
#         return processed_data
# GptAgentInteractions
#
# help(GptAgentInteractions)
