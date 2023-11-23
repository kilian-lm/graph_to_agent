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
import google.api_core.exceptions
import requests

load_dotenv()

from logger.CustomLogger import CustomLogger


class BigQueryHandler:

    def __init__(self, key, dataset_id):
        # timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        self.key = key
        print(self.key)
        self.log_file = f'{self.key}_bq_handler.log'
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

    def create_view(self, dataset_id, view_id, view_query):
        view_ref = self.bigquery_client.dataset(dataset_id).table(view_id)
        view = bigquery.Table(view_ref)
        view.view_query = view_query

        try:
            self.bigquery_client.get_table(view_ref)
            print(f"View {dataset_id}.{view_id} already exists. Deleting it.")
            self.bigquery_client.delete_table(view_ref)
        except NotFound:
            print(f"View {dataset_id}.{view_id} does not exist.")

        try:
            view = self.bigquery_client.create_table(view)
            print(f"View {dataset_id}.{view_id} created.")
        except google.api_core.exceptions.BadRequest as e:
            print(f"Error creating the view: {str(e)}")
            raise
        except Exception as e:
            print(f"Error creating the view: {str(e)}")
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

    def create_table_if_not_exists(self, table_id, schema=None):
        table_ref = self.bigquery_client.dataset(self.dataset_id).table(table_id)

        try:
            self.bigquery_client.get_table(table_ref)
            self.logger.info(f"Table {table_id} already exists.")
        except Exception as e:
            if schema is not None:
                table = bigquery.Table(table_ref, schema=schema)
            else:
                table = bigquery.Table(table_ref)

            self.bigquery_client.create_table(table)
            self.logger.info(f"Table {table_id} has been created.")

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

        self.logger.debug(f"nodes_for_bq: {nodes_for_bq}")

        # Translate edges
        edges_for_bq = [
            {
                "graph_id": graph_id,
                "from": edge.get('from'),
                "to": edge.get('to')
            }
            for edge in raw_edges
        ]

        self.logger.debug(f"edges_for_bq: {edges_for_bq}")

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
            self.logger.debug(f"Transformed Nodes: {nodes_for_bq}")
            self.logger.debug(f"Transformed Edges: {edges_for_bq}")

            # Insert nodes and pass in the schema explicitly
            errors_nodes = self.bigquery_client.insert_rows(nodes_table, nodes_for_bq,
                                                            selected_fields=nodes_table.schema)
            if errors_nodes:
                self.logger.warning(f"Encountered errors while inserting nodes: {errors_nodes}")

            # Insert edges and pass in the schema explicitly
            errors_edges = self.bigquery_client.insert_rows(edges_table, edges_for_bq,
                                                            selected_fields=edges_table.schema)
            if errors_edges:
                self.logger.warning(f"Encountered errors while inserting edges: {errors_edges}")

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

            self.logger.debug(f"graph_data_as_dicts: {graph_data_as_dicts}")

            # Return both BigQuery errors and processed data
            # return {
            #     "bigquery_errors": all_errors,
            # }

            return ({"status": "success", "savedGraph": graph_data_as_dicts})

        except Exception as e:
            self.logger.exception("An unexpected error occurred during save_graph_data:")
        raise

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

    def get_available_graphs(self):
        # Query to get distinct graph_ids from the nodes_table
        query = f"SELECT DISTINCT graph_id FROM `{self.dataset_id}.nodes_table`"
        query_job = self.bigquery_client.query(query)
        results = query_job.result()

        return [{"graph_id": row["graph_id"], "graph_name": row["graph_id"]} for row in results]

    def load_jsonl_to_bq(self, dataset_id, table_id, jsonl_file_path):
        # Initialize the BigQuery client

        # Create the table if it doesn't exist
        self.create_table_if_not_exists(dataset_id, table_id)

        # Define the job configuration with auto-detect schema
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
            autodetect=True,  # Automatically detect schema from JSONL
        )

        # Define the dataset and table
        dataset_ref = self.bigquery_client.dataset(dataset_id)
        table_ref = dataset_ref.table(table_id)

        # with open("test.jsonl", "rb") as source_file:
        #     print(source_file)

        # Start the job to load data from JSONL file
        with open(jsonl_file_path, "rb") as source_file:
            job = self.bigquery_client.load_table_from_file(
                source_file, table_ref, job_config=job_config
            )

        # Wait for the job to complete
        job.result()

        print(f"Loaded {job.output_rows} rows into {dataset_id}.{table_id}")

# openai_api_key = os.getenv('OPEN_AI_KEY')
# open_ai_url = "https://api.openai.com/v1/chat/completions"
# bot = BigQueryHandler('graph_to_agent', 'test.json')
#
# bot.extract_and_send_to_gpt('test')

# bq_handler = BigQueryHandler( 'graph_to_agent', 'test.json')
#
# bq_handler.load_graph_data_by_id('example_graph_001')
