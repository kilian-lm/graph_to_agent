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
import inspect
import re

from logger.CustomLogger import CustomLogger
from controllers.BigQueryHandler import BigQueryHandler

load_dotenv()


class MatrixLayerOne:
    def __init__(self, key, graph_data, dataset_id):
        self.key = key
        print(self.key)
        self.log_file = f'{self.key}_matrix_layer_one.log'
        print(self.log_file)
        self.log_dir = './temp_log'
        print(self.log_dir)
        self.log_level = logging.DEBUG
        print(self.log_level)
        self.logger = CustomLogger(self.log_file, self.log_level, self.log_dir)

        self.filename = None
        self.graph_data = graph_data
        self.temp_multi_layered_matrix_dir = os.getenv('TEMP_MULTI_LAYERED_MATRIX_DIR')
        self.dataset_id = dataset_id
        self.bq_handler = BigQueryHandler(self.key)

    def multi_layered_matrix_upload_jsonl_to_bigquery(self, filename, dataset_id):
        """
        Uploads multi_layered_matrix as .jsonl file to a BigQuery table.
        """
        # Set the destination table and dataset.
        table_id = f"{self.bq_handler.bigquery_client.project}.{dataset_id}.{self.key}"

        # Configure the load job
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
            autodetect=True,  # Auto-detect schema.
        )

        with open(filename, "rb") as source_file:
            job = self.bq_handler.bigquery_client.load_table_from_file(source_file, table_id, job_config=job_config)

        # Wait for the load job to complete
        job.result()

        table = self.bq_handler.bigquery_client.get_table(table_id)  # Make an API request to get table info
        self.logger.info(f"Loaded {table.num_rows} rows and {len(table.schema)} columns to {table_id}")

    def create_advanced_adjacency_matrix(self):
        """
        Create an advanced adjacency matrix with binary indicators and labels for both row and column nodes,
        and save it as a .jsonl file in a query-friendly format.
        """
        nodes = self.graph_data["nodes"]
        edges = self.graph_data["edges"]

        # Open the .jsonl file for writing
        self.filename = f'{self.temp_multi_layered_matrix_dir}/{self.key}_multi_layered_matrix.jsonl'
        with open(self.filename, 'w') as jsonl_file:
            for row_node in nodes:
                row_node_id = row_node["id"]
                row_node_label = row_node["label"]
                connections = []

                for col_node in nodes:
                    col_node_id = col_node["id"]
                    col_node_label = col_node["label"]
                    edge_exists = any(edge["to"] == col_node_id and edge["from"] == row_node_id for edge in edges)

                    connection_record = {
                        "connected_node_id": col_node_id,
                        "connected": 1 if edge_exists else 0,
                        "row_label": row_node_label,
                        "col_label": col_node_label
                    }
                    connections.append(connection_record)

                # Write each node's connections as an array of records
                jsonl_file.write(json.dumps({"node_id": row_node_id, "connections": connections}) + "\n")

        return self.filename

    def generate_bigquery_schema_from_graph(self):
        # Initialize schema with 'node_id' field
        schema = [bigquery.SchemaField('node_id', 'STRING', 'NULLABLE')]

        # Extract node IDs and create schema fields for each
        node_ids = [node['id'] for node in self.graph_data['nodes']]
        for node_id in node_ids:
            schema.append(bigquery.SchemaField(node_id, 'INTEGER', 'NULLABLE'))

        return schema

    def adjacency_matrix_upload_to_bigquery(self, dataset_id):
        # Initialize a BigQuery client

        # Generate the binary layer
        binary_layer = self.create_binary_layer()

        # Generate the schema from the graph data
        schema = self.generate_bigquery_schema_from_graph()

        # Define the table reference
        table_ref = self.bq_handler.bigquery_client.dataset(dataset_id).table(self.key)

        # Create or overwrite the table
        table = bigquery.Table(table_ref, schema=schema)
        table = self.bq_handler.bigquery_client.create_table(table, exists_ok=True)

        # Prepare rows to insert
        rows_to_insert = []
        for node_id, connections in binary_layer.items():
            row = {'node_id': node_id}
            row.update(connections)
            rows_to_insert.append(row)

        # Insert data into the table
        errors = self.bq_handler.bigquery_client.insert_rows_json(table, rows_to_insert)
        if errors:
            print("Errors occurred while inserting rows: {}".format(errors))
        else:
            print("Data uploaded successfully.")

    def create_binary_layer(self):
        # Create a binary layer based on node connections
        nodes = self.graph_data["nodes"]
        self.logger.info(nodes)
        edges = self.graph_data["edges"]
        self.logger.info(edges)

        binary_layer = {}
        for node in nodes:
            binary_layer[node["id"]] = {}
            for other_node in nodes:
                if any(edge["from"] == node["id"] and edge["to"] == other_node["id"] for edge in edges):
                    binary_layer[node["id"]][other_node["id"]] = 1
                else:
                    binary_layer[node["id"]][other_node["id"]] = 0

        self.logger.info(binary_layer)

        return binary_layer

    def print_binary_layer_matrix(self):
        """
        Print the binary layer as an adjacency matrix.
        """
        binary_layer = self.create_binary_layer()
        nodes = sorted(self.graph_data["nodes"], key=lambda x: x["id"])
        print("Adjacency Matrix:")

        # Print header row
        print("   ", end="")
        for node in nodes:
            print(f"{node['id']} ", end="")
        print()

        # Print each row of the matrix
        for node in nodes:
            print(f"{node['id']} ", end="")
            for other_node in nodes:
                print(f"{binary_layer[node['id']][other_node['id']]} ", end="")
            print()  # New line after each row

    def print_second_layer(self):
        """
        Print the second layer, assuming it deals with relationships between nodes.
        """
        # Example: Print edges in a human-readable format
        edges = self.graph_data.get("edges", [])
        for edge in edges:
            print(f"From {edge['from']} to {edge['to']}")
