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

load_dotenv()

logging.basicConfig(level=logging.INFO)  # You can change the level as needed.
logger = logging.getLogger(__name__)

class BigQueryHandler:
    def __init__(self, dataset_id, schema_json_path):
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
        """
        Translates the provided graph data to match the BigQuery schema.

        Args:
        - graph_data (dict): The graph data containing nodes and edges.
        - graph_id (str): The unique identifier for the graph.

        Returns:
        - tuple: A tuple containing nodes and edges in BigQuery format.
        """

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

            return all_errors
        except Exception as e:
            logger.exception("An unexpected error occurred during save_graph_data:")
            raise

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

# bq_handler = BigQueryHandler( 'graph_to_agent', 'test.json')
#
# bq_handler.load_graph_data_by_id('example_graph_001')