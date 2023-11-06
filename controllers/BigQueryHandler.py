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

load_dotenv()

logging.basicConfig(level=logging.DEBUG)  # You can change the level as needed.
logger = logging.getLogger(__name__)


class BigQueryHandler:

    def __init__(self, dataset_id, schema_json_path):
        self.openai_api_key = os.getenv('OPEN_AI_KEY')
        self.openai_base_url = "https://api.openai.com/v1/chat/completions"
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.openai_api_key}'
        }
        self.dataset_id = dataset_id
        self.schema_json_path = schema_json_path
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
                # Ignoring coordinates for now
            }
            for node in raw_nodes
        ]

        print(nodes_for_bq)

        # Translate edges
        edges_for_bq = [
            {
                "graph_id": graph_id,
                "from": edge.get('from'),
                "to": edge.get('to')
            }
            for edge in raw_edges
        ]

        print(edges_for_bq)

        return nodes_for_bq, edges_for_bq

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
            logger.debug(f"Transformed Nodes: {nodes_for_bq}")
            logger.debug(f"Transformed Edges: {edges_for_bq}")

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

            # Pass the dictionaries to the workflow logic
            processed_data = self.translate_graph_to_gpt_sequence(graph_data_as_dicts)
            #
            #
            # processed_data = processed_data["processed_data"]
            # logger.debug(f"processed_data: {processed_data}")
            # agent_content = self.extract_and_send_to_gpt(processed_data)
            # logger.debug(f"agent_content: {agent_content}")

            # Serialize data to json
            json_data = json.dumps(processed_data, indent=4)
            logger.debug(f"json_data: {json_data}")



            # Write to a timestamped JSON file
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"processed_graph_{timestamp}.json"
            with open(filename, 'w') as json_file:
                json_file.write(json_data)

            # Return both BigQuery errors and processed data
            return {
                "bigquery_errors": all_errors,
                "processed_data": processed_data,
                "json_file": filename
            }

        except Exception as e:
            logger.exception("An unexpected error occurred during save_graph_data:")
        raise


    # A helper function to determine a node's type (user, system, or content)
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
        json_filename = f"processed_graph_{timestamp}.json"

        with open(json_filename, "w") as json_file:
            json_file.write(json_data)

        return {
            'bigquery_errors': {'node_errors': [], 'edge_errors': []},
            'processed_data': translated_data
        }

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

    def get_available_graphs(self):
        # Query to get distinct graph_ids from the nodes_table
        query = f"SELECT DISTINCT graph_id FROM `{self.dataset_id}.nodes_table`"
        query_job = self.bigquery_client.query(query)
        results = query_job.result()

        return [{"graph_id": row["graph_id"], "graph_name": row["graph_id"]} for row in results]

    def extract_and_send_to_gpt(self, processed_data):

        # Prepare the data for the POST request
        # Assuming 'processed_data' contains the necessary format for GPT-4 API
        post_data = {
            "model": os.getenv("MODEL"),
            "messages": processed_data["messages"]
        }

        # Send POST request to GPT
        response = requests.post(self.openai_base_url, headers=self.headers, json=post_data)

        # Check if the request was successful and extract PUML content
        if response.status_code == 200:
            agent_content = response.json()["choices"][0]["message"]["content"]
            return agent_content
        else:
            raise Exception(f"Error in GPT request: {response.status_code}, {response.text}")





# openai_api_key = os.getenv('OPEN_AI_KEY')
# open_ai_url = "https://api.openai.com/v1/chat/completions"
# bot = BigQueryHandler('graph_to_agent', 'test.json')
#
# bot.extract_and_send_to_gpt('test')

# bq_handler = BigQueryHandler( 'graph_to_agent', 'test.json')
#
# bq_handler.load_graph_data_by_id('example_graph_001')
