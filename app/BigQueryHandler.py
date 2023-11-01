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



class BigQueryHandler:
    def __init__(self, dataset_id, schema_json_path):
        self.dataset_id = dataset_id
        self.schema_json_path = schema_json_path
        bq_client_secrets = os.getenv('BQ_CLIENT_SECRETS')

        bq_client_secrets_parsed = json.loads(bq_client_secrets)
        self.bq_client_secrets = Credentials.from_service_account_info(bq_client_secrets_parsed)
        self.bigquery_client = bigquery.Client(credentials=self.bq_client_secrets,
                                               project=self.bq_client_secrets.project_id)

    def create_dataset_if_not_exists(self):
        dataset_ref = self.bigquery_client.dataset(self.dataset_id)
        try:
            self.bigquery_client.get_dataset(dataset_ref)
        except Exception as e:
            dataset = bigquery.Dataset(dataset_ref)
            self.bigquery_client.create_dataset(dataset)

    def create_table_if_not_exists(self, table_id, schema):
        table_ref = self.bigquery_client.dataset(self.dataset_id).table(table_id)
        try:
            self.bigquery_client.get_table(table_ref)
        except Exception as e:
            table = bigquery.Table(table_ref, schema=schema)
            self.bigquery_client.create_table(table)

    def get_node_schema(self):
        return [
            bigquery.SchemaField("graph_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("id", "INT64", mode="REQUIRED"),
            bigquery.SchemaField("label", "STRING", mode="REQUIRED")
        ]

    def get_edge_schema(self):
        return [
            bigquery.SchemaField("graph_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("from", "INT64", mode="REQUIRED"),
            bigquery.SchemaField("to", "INT64", mode="REQUIRED")
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

        # Translate edges
        edges_for_bq = [
            {
                "graph_id": graph_id,
                "from": edge.get('from'),
                "to": edge.get('to')
            }
            for edge in raw_edges
        ]

        return nodes_for_bq, edges_for_bq

    def save_graph_data(self, graph_data, graph_id):
        nodes_table_ref = self.bigquery_client.dataset(self.dataset_id).table("nodes_table")
        edges_table_ref = self.bigquery_client.dataset(self.dataset_id).table("edges_table")

        # Use the translator function to transform the data
        nodes_for_bq, edges_for_bq = translate_graph_data_for_bigquery(graph_data, graph_id)

        # Print the transformed data for debugging
        print("Transformed Nodes:", nodes_for_bq)
        print("Transformed Edges:", edges_for_bq)

        # Insert nodes
        errors_nodes = self.bigquery_client.insert_rows(nodes_table_ref, nodes_for_bq)
        if errors_nodes:
            print(f"Encountered errors while inserting nodes: {errors_nodes}")

        # Insert edges
        errors_edges = self.bigquery_client.insert_rows(edges_table_ref, edges_for_bq)
        if errors_edges:
            print(f"Encountered errors while inserting edges: {errors_edges}")

        # Compile all errors
        all_errors = {
            "node_errors": errors_nodes,
            "edge_errors": errors_edges
        }

        return all_errors
    def load_graph_data_by_id(self, graph_id):
        nodes_table_ref = self.bigquery_client.dataset(self.dataset_id).table("nodes_table")
        edges_table_ref = self.bigquery_client.dataset(self.dataset_id).table("edges_table")

        # Fetch nodes for given graph_id
        nodes_query = f"SELECT * FROM `{self.dataset_id}.nodes_table` WHERE graph_id = '{graph_id}'"
        nodes_query_job = self.bigquery_client.query(nodes_query)
        nodes_results = nodes_query_job.result()
        nodes = [{"id": row['id'], "label": row['label']} for row in nodes_results]

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