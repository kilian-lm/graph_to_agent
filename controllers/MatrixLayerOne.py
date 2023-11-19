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
    def __init__(self, timestamp, graph_data, dataset_id):
        try:
            # timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            self.timestamp = timestamp
            print(self.timestamp)
            self.log_file = f'{self.timestamp}_matrix_layer_one.log'
            print(self.log_file)
            self.log_dir = './temp_log'
            print(self.log_dir)
            self.log_level = logging.DEBUG
            print(self.log_level)
            self.logger = CustomLogger(self.log_file, self.log_level, self.log_dir)

            # todo: hand form app.py graph_id , think about coherent logic to ident nodes with matrix
            self.graph_id = self.timestamp
            self.table_name = self.graph_id

            self.graph_data = graph_data

            self.dataset_id = dataset_id
            self.bq_handler = BigQueryHandler(self.timestamp, self.dataset_id)

            # ToDo :: Dublicated import of bq !!
            #  From mere class initialization in another class to inheritance

            bq_client_secrets = os.getenv('BQ_CLIENT_SECRETS')

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

    def upload_jsonl_to_bigquery(self, filename):
        """
        Uploads a .jsonl file to a BigQuery table.
        """
        # Set the destination table and dataset.
        table_id = f"{self.bigquery_client.project}.{self.dataset_id}.{self.table_name}_multi_layered"

        # Configure the load job
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
            autodetect=True,  # Auto-detect schema.
        )

        with open(filename, "rb") as source_file:
            job = self.bigquery_client.load_table_from_file(source_file, table_id, job_config=job_config)

        # Wait for the load job to complete
        job.result()

        table = self.bigquery_client.get_table(table_id)  # Make an API request to get table info
        self.logger.info(f"Loaded {table.num_rows} rows and {len(table.schema)} columns to {table_id}")

    def create_advanced_adjacency_matrix(self):
        """
        Create an advanced adjacency matrix with binary indicators and labels for both row and column nodes,
        and save it as a .jsonl file in a query-friendly format.
        """
        nodes = self.graph_data["nodes"]
        edges = self.graph_data["edges"]

        # Open the .jsonl file for writing
        with open(f'{self.timestamp}_advanced_adjacency_matrix.jsonl', 'w') as jsonl_file:
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

        return None

    def create_bq_schema_for_advanced_matrix(self):
        """
        Create a BigQuery schema for the advanced adjacency matrix using strings instead of integers.
        """
        schema = [
            bigquery.SchemaField("node_id", "STRING", mode="REQUIRED"),
        ]
        for node in self.graph_data["nodes"]:
            field_name = str(node["id"])
            schema.append(bigquery.SchemaField(field_name, "STRING", mode="NULLABLE"))
        return schema

    def upload_advanced_matrix_to_bigquery(self):
        """
        Upload the advanced adjacency matrix to BigQuery.
        """
        advanced_matrix = self.create_advanced_adjacency_matrix()
        schema = self.create_bq_schema_for_advanced_matrix()

        table_ref = self.bigquery_client.dataset(self.dataset_id).table(self.table_name + "_multi_layered")
        self.bq_handler.create_dataset_if_not_exists()
        self.bq_handler.create_table_if_not_exists(table_ref, schema)

        rows_to_insert = []

        for node_id, connections in advanced_matrix.items():
            row = {"node_id": str(node_id)}
            for other_node_id, connection in connections.items():
                # Convert the connection data to a string representation
                connection_str = f"{connection['connected']};{connection['row_label']};{connection['col_label']}"
                row[other_node_id] = connection_str
            rows_to_insert.append(row)

        errors = self.bigquery_client.insert_rows_json(table_ref, rows_to_insert)
        if errors:
            self.logger.error(f"Errors occurred while inserting rows: {errors}")
        else:
            self.logger.info("Advanced adjacency matrix data uploaded successfully.")

    def save_matrix_to_bq(self):
        self.logger.info(self.table_name)
        table_ref = self.bigquery_client.dataset(self.dataset_id).table(self.table_name)

        schema = self.create_bq_table_schema()
        # self.logger.info(schema)
        self.bq_handler.create_dataset_if_not_exists()
        self.bq_handler.create_table_if_not_exists(table_ref, schema)

        binary_layer = self.create_binary_layer()
        rows_to_insert = []

        for node_id, connections in binary_layer.items():
            row = {"node_id": str(node_id)}
            for other_node_id, connection in connections.items():
                row[str(other_node_id)] = connection
            rows_to_insert.append(row)

        self.bigquery_client.insert_rows(self.table_name, rows_to_insert)

    def generate_bigquery_schema_from_graph(self):
        # Initialize schema with 'node_id' field
        schema = [bigquery.SchemaField('node_id', 'STRING', 'NULLABLE')]

        # Extract node IDs and create schema fields for each
        node_ids = [node['id'] for node in self.graph_data['nodes']]
        for node_id in node_ids:
            schema.append(bigquery.SchemaField(node_id, 'INTEGER', 'NULLABLE'))

        return schema

    def upload_to_bigquery(self):
        # Initialize a BigQuery client

        # Generate the binary layer
        binary_layer = self.create_binary_layer()

        # Generate the schema from the graph data
        schema = self.generate_bigquery_schema_from_graph()

        # Define the table reference
        table_ref = self.bigquery_client.dataset(self.dataset_id).table(self.timestamp)

        # Create or overwrite the table
        table = bigquery.Table(table_ref, schema=schema)
        table = self.bigquery_client.create_table(table, exists_ok=True)

        # Prepare rows to insert
        rows_to_insert = []
        for node_id, connections in binary_layer.items():
            row = {'node_id': node_id}
            row.update(connections)
            rows_to_insert.append(row)

        # Insert data into the table
        errors = self.bigquery_client.insert_rows_json(table, rows_to_insert)
        if errors:
            print("Errors occurred while inserting rows: {}".format(errors))
        else:
            print("Data uploaded successfully.")

    def count_trees_in_matrix(self, df):
        """
        Count the number of distinct trees (connected components) in the adjacency matrix represented by a pandas DataFrame.
        """

        def dfs(node, visited):
            visited.add(node)
            for neighbor in range(len(df)):
                # Check if there's an edge and the neighbor hasn't been visited
                if df.iloc[node, neighbor] == 1 and neighbor not in visited:
                    dfs(neighbor, visited)

        visited = set()
        tree_count = 0

        for node in range(len(df)):
            if node not in visited:
                dfs(node, visited)
                tree_count += 1

        return tree_count

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

    def create_label_layer(self):
        # Create a label layer based on node labels
        nodes = self.graph_data["nodes"]
        label_layer = {}
        for node in nodes:
            label_layer[node["id"]] = node["label"]
        return label_layer

    def find_patterns(self):
        # Find hierarchical patterns in the 3D matrix
        patterns = []
        nodes = self.graph_data["nodes"]
        edges = self.graph_data["edges"]

        def is_valid_pattern(pattern):
            # Check if a pattern is valid (e.g., "user", "system", "user")
            if len(pattern) != 6:
                return False
            return (
                    pattern[0] == "user" and
                    pattern[2] == "system" and
                    pattern[4] == "user"
            )

        def dfs(node, pattern):
            # Depth-first search to traverse the hierarchy and find patterns
            pattern.append(node["label"])

            if node["label"] == "system" and len(pattern) > 1:
                for edge in edges:
                    if edge["from"] == node["id"]:
                        next_node = next(n for n in nodes if n["id"] == edge["to"])
                        dfs(next_node, pattern)

            if node["label"] == "user" and len(pattern) > 1:
                patterns.append(tuple(pattern))

            pattern.pop()

        for node in nodes:
            if node["label"] == "user":
                dfs(node, [])

        valid_patterns = [p for p in patterns if is_valid_pattern(p)]
        return valid_patterns

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

    def prepare_and_identify_label(self, search_label):
        """
        Prepare a third layer and identify a single string in the label data.
        """
        label_layer = self.create_label_layer()
        matching_nodes = [node_id for node_id, label in label_layer.items() if label == search_label]
        print(f"Nodes with label '{search_label}': {matching_nodes}")
        return matching_nodes

    # Example usage:
    # patterns = your_matrix_instance.find_patterns()
    # print(patterns)
    # def get_patterns(self):
    # Return the found patterns
    # return self.find_patterns()

    def main_matrix_layer_one(self, json_graph_data):
        graph_data = json.loads(json_graph_data)
        self.graph_id = self.timestamp
        # mat_3d = Matrix3D(graph_data, "graph_to_agent_adjacency_matrices", f"{graph_id}_2")


json_file_path = "./logics/simple_va_inheritance_20231117.json"

with open(json_file_path, 'r') as json_file:
    graph_data = json.load(json_file)

matrix_layer_one = MatrixLayerOne("20231117163236", graph_data, "graph_to_agent")

matrix_layer_one.create_advanced_adjacency_matrix()
matrix_layer_one.upload_jsonl_to_bigquery('20231117163236_advanced_adjacency_matrix.jsonl')

matrix_layer_one.create_bq_schema_for_advanced_matrix()

matrix_layer_one.upload_advanced_matrix_to_bigquery()
#
# timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
#
# # mat_3d = Matrix3D(graph_data, "graph_to_agent_adjacency_matrices", f"{graph_id}_2")
#
# mat_3d = MatrixLayerOne(timestamp, graph_data, "graph_to_agent_adjacency_matrices")
# mat_3d.upload_to_bigquery()
# # mat_1 = mat_3d.create_binary_layer()
# # mat_1
# #
# # tbl = mat_3d.bigquery_client.get_table("enter-universes.graph_to_agent_adjacency_matrices.20231114115221_2")
# #
# # tbl_id = "enter-universes.graph_to_agent_adjacency_matrices.20231114115221_2"
# #
# # df = mat_3d.bigquery_client.query(f"SELECT * FROM `{tbl_id}`").to_dataframe()
# # df
#
# # mat_3d.count_trees_in_matrix(df)
#
# mat_3d.upload_to_bigquery("graph_to_agent_adjacency_matrices",f"{graph_id}_2")
# mat_3d.upload_jsonl_to_bq(f"{graph_id}_2","test.jsonl")
# mat_3d.save_matrix_to_jsonl("test.jsonl")
#
# mat_3d.bq_handler.load_jsonl_to_bq("graph_to_agent_adjacency_matrices", graph_id, "test.jsonl")
#
# mat_3d.save_matrix_to_bq()
#
# mat_3d.create_binary_layer()
#
# mat_3d.bigquery_client.schema_from_json('test.jsonl')
#
# mat_3d.bigquery_client.get_table("enter-universes.graph_to_agent_adjacency_matrices.test").schema
#
# mat_3d.print_binary_layer_matrix()
# mat_3d.count_connected_subtrees()
#
# mat_3d.find_connected_subtrees()
#
# mat_3d.find_patterns()
