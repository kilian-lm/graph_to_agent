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
            self.bq_handler = BigQueryHandler(self.dataset_id)

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

    def create_bq_table_schema(self):
        """
        Create a BigQuery table schema for the adjacency matrix.
        """
        schema = [
            bigquery.SchemaField("node_id", "STRING", mode="NULLABLE"),
        ]
        for node in self.graph_data["nodes"]:
            schema.append(bigquery.SchemaField(str(node["id"]), "INTEGER"))

        self.logger.info(schema)
        return schema

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

    # todo :: try bq via jsonl dup

    # def save_matrix_to_jsonl(self, file_path):
    #     binary_layer = self.create_binary_layer()
    #     with open(file_path, 'w') as file:
    #         for node_id, connections in binary_layer.items():
    #             row = {"node_id": str(node_id)}
    #             self.logger.info(row)
    #             for other_node_id, connection in connections.items():
    #                 row[str(other_node_id)] = connection
    #             json.dump(row, file)
    #             file.write('\n')  # New line for next JSON object
    #
    #     return file_path

    def generate_bigquery_schema_from_graph(self):
        # Initialize schema with 'node_id' field
        schema = [bigquery.SchemaField('node_id', 'STRING', 'NULLABLE')]

        # Extract node IDs and create schema fields for each
        node_ids = [node['id'] for node in self.graph_data['nodes']]
        for node_id in node_ids:
            schema.append(bigquery.SchemaField(node_id, 'INTEGER', 'NULLABLE'))

        return schema

    # def upload_jsonl_to_bq(self, table_name, file_path):
    #     table_ref = self.bigquery_client.dataset(self.dataset_id).table(self.table_name)
    #
    #     # self.logger.info(schema)
    #     self.bq_handler.create_dataset_if_not_exists()
    #
    #     schema = self.generate_bigquery_schema_from_graph()
    #
    #     self.bq_handler.create_table_if_not_exists(table_ref, schema)
    #
    #     # self.bq_handler.load_jsonl_to_bq(self.dataset_id, table_name, file_path)

    def find_connected_subtrees(self):
        # Find connected subtrees in the 3D matrix
        binary_layer = self.create_binary_layer()
        self.logger.info(binary_layer)
        nodes = self.graph_data["nodes"]
        self.logger.info(nodes)

        visited = set()
        subtrees = []

        def dfs(node_id, subtree):
            visited.add(node_id)

            self.logger.info(node_id)

            subtree.append(node_id)
            self.logger.info(subtree)

            for neighbor_id, is_connected in binary_layer[node_id].items():
                if is_connected == 1 and neighbor_id not in visited:
                    dfs(neighbor_id, subtree)
                    self.logger.info(dfs)

        for node in nodes:
            if node["id"] not in visited:
                subtree = []
                dfs(node["id"], subtree)
                subtrees.append(subtree)

        return subtrees

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

    def count_connected_subtrees(self):
        # Count the number of connected subtrees in the 3D matrix
        binary_layer = self.create_binary_layer()
        connected_subtrees = self.find_connected_subtrees()
        num_connected_trees = 0

        for subtree in connected_subtrees:
            # Check if the subtree has only one connecting node
            connecting_nodes = 0
            for node_id in subtree:
                neighbors = binary_layer[node_id]
                num_neighbors = sum(neighbors.values())
                if num_neighbors == 1:
                    connecting_nodes += 1

            if connecting_nodes == 1:
                num_connected_trees += 1

        return num_connected_trees

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

# import datetime
#
#
# json_graph_data = """
# {
#   "nodes": [
#     {
#       "id": "07537a68-1c7e-4edb-a72f-2d82015c490f",
#       "label": "Understood! As I'm an expert in the .puml syntax i will correct it"
#     },
#     {
#       "id": "1cc45118-72ee-4efe-95d8-06e8c02fb4c0",
#       "label": "The following is a .puml content generated by an agent. Please critically review it and correct any mistakes, especially ensuring it strictly adheres to .puml syntax and does not contain any elements from other diagramming languages like Mermaid"
#     },
#     {
#       "id": "2e419e7e-a540-4c9a-af4e-5110e54fad96",
#       "label": "system"
#     },
#     {
#       "id": "757e7439-08f8-4cea-afac-c25b01167d32",
#       "label": "user"
#     },
#     {
#       "id": "c7d1c0a4-6365-44d6-be0c-bd3fc5436b85",
#       "label": "user"
#     },
#     {
#       "id": "eac6de73-9726-43b7-9441-f8e319a972e6",
#       "label": "@variable_1_2"
#     },
#     {
#       "id": "copied-1699797991293-eac6de73-9726-43b7-9441-f8e319a972e6",
#       "label": "sequenceDiagramAlice->>John: Hello John, how are you?John-->>Alice: Great!Alice-)John: See you later!"
#     },
#     {
#       "id": "copied-1699889663524-copied-1699797991293-c7d1c0a4-6365-44d6-be0c-bd3fc5436b85",
#       "label": "user"
#     },
#     {
#       "id": "copied-1699889663524-copied-1699797991293-07537a68-1c7e-4edb-a72f-2d82015c490f",
#       "label": "Understood! , I'm agent-'Deductive Reasoning', solving problems like you just described. Please provide the problem-space for me to navigate it best as possible..."
#     },
#     {
#       "id": "copied-1699889663524-copied-1699797991293-1cc45118-72ee-4efe-95d8-06e8c02fb4c0",
#       "label": "You're agent-'Deductive Reasoning'. You're one agent out of 7 who try to model problem-spaces and suggest solutions based on logical reasoning, similar to the detectives of The Poisoned Chocolates Case. Your strength lies in deriving specific conclusions from general hypotheses. Utilize schemas like Modus Ponens, Modus Tollens, Hypothetical Syllogism, and Disjunctive Syllogism., in order to solve problems, you use one of the following schemas ['Modus Ponens', 'Modus Tollens', 'Hypothetical Syllogism', 'Disjunctive Syllogism']"
#     },
#     {
#       "id": "copied-1699889663524-copied-1699797991293-2e419e7e-a540-4c9a-af4e-5110e54fad96",
#       "label": "system"
#     },
#     {
#       "id": "copied-1699889663524-copied-1699797991293-757e7439-08f8-4cea-afac-c25b01167d32",
#       "label": "user"
#     },
#     {
#       "id": "copied-1699890186553-copied-1699889663524-copied-1699797991293-eac6de73-9726-43b7-9441-f8e319a972e6",
#       "label": "How would you model following problem-space?: There was a attack of the Palestinien sided group Hamas on Israel. Now Israel is bombing Gaza with heavy civiliens casualties. There is a total 'cleaning' of the Hamas in Gaza planned by Isralien-Army. There is a high danger that the whole region will fall into war.."
#     },
#     {
#       "id": "copied-1699890186553-copied-1699797991293-07537a68-1c7e-4edb-a72f-2d82015c490f",
#       "label": "Understood! I will review following .mmd"
#     },
#     {
#       "id": "copied-1699890186553-copied-1699797991293-1cc45118-72ee-4efe-95d8-06e8c02fb4c0",
#       "label": "You're an expert in mermeid .mmd and you nedd to review following .mmd"
#     },
#     {
#       "id": "copied-1699890186553-copied-1699797991293-2e419e7e-a540-4c9a-af4e-5110e54fad96",
#       "label": "system"
#     },
#     {
#       "id": "copied-1699890186553-copied-1699797991293-757e7439-08f8-4cea-afac-c25b01167d32",
#       "label": "user"
#     },
#     {
#       "id": "copied-1699890186553-copied-1699797991293-c7d1c0a4-6365-44d6-be0c-bd3fc5436b85",
#       "label": "user"
#     },
#     {
#       "id": "234ec0c2-3d02-4ef5-9fb1-7adaeb58a1b6",
#       "x": 1626.674810293892,
#       "y": -632.9703327332509,
#       "label": "@varibale_1_1"
#     }
#   ],
#   "edges": [
#     {
#       "from": "07537a68-1c7e-4edb-a72f-2d82015c490f",
#       "id": "67194bdc-f1f3-417f-9778-4d163c8b82d1",
#       "to": "757e7439-08f8-4cea-afac-c25b01167d32"
#     },
#     {
#       "from": "1cc45118-72ee-4efe-95d8-06e8c02fb4c0",
#       "id": "1329a8be-e4e2-42fd-bdb6-2057f9c320d3",
#       "to": "2e419e7e-a540-4c9a-af4e-5110e54fad96"
#     },
#     {
#       "from": "2e419e7e-a540-4c9a-af4e-5110e54fad96",
#       "id": "33312b2e-b683-4489-b471-e2d1ca03d21a",
#       "to": "07537a68-1c7e-4edb-a72f-2d82015c490f"
#     },
#     {
#       "from": "757e7439-08f8-4cea-afac-c25b01167d32",
#       "id": "f5b47e5e-4121-44a3-8b29-97bfe2069148",
#       "to": "eac6de73-9726-43b7-9441-f8e319a972e6"
#     },
#     {
#       "from": "c7d1c0a4-6365-44d6-be0c-bd3fc5436b85",
#       "id": "f4e2015e-e7f1-4e03-b3c6-ee82986533ca",
#       "to": "1cc45118-72ee-4efe-95d8-06e8c02fb4c0"
#     },
#     {
#       "from": "copied-1699889663524-copied-1699797991293-c7d1c0a4-6365-44d6-be0c-bd3fc5436b85",
#       "id": "copied-1699889663524-copied-1699797991293-f4e2015e-e7f1-4e03-b3c6-ee82986533ca",
#       "to": "copied-1699889663524-copied-1699797991293-1cc45118-72ee-4efe-95d8-06e8c02fb4c0"
#     },
#     {
#       "from": "copied-1699889663524-copied-1699797991293-07537a68-1c7e-4edb-a72f-2d82015c490f",
#       "id": "copied-1699889663524-copied-1699797991293-67194bdc-f1f3-417f-9778-4d163c8b82d1",
#       "to": "copied-1699889663524-copied-1699797991293-757e7439-08f8-4cea-afac-c25b01167d32"
#     },
#     {
#       "from": "copied-1699889663524-copied-1699797991293-2e419e7e-a540-4c9a-af4e-5110e54fad96",
#       "id": "copied-1699889663524-copied-1699797991293-33312b2e-b683-4489-b471-e2d1ca03d21a",
#       "to": "copied-1699889663524-copied-1699797991293-07537a68-1c7e-4edb-a72f-2d82015c490f"
#     },
#     {
#       "from": "copied-1699889663524-copied-1699797991293-1cc45118-72ee-4efe-95d8-06e8c02fb4c0",
#       "id": "copied-1699889663524-copied-1699797991293-1329a8be-e4e2-42fd-bdb6-2057f9c320d3",
#       "to": "copied-1699889663524-copied-1699797991293-2e419e7e-a540-4c9a-af4e-5110e54fad96"
#     },
#     {
#       "from": "copied-1699889663524-copied-1699797991293-757e7439-08f8-4cea-afac-c25b01167d32",
#       "id": "copied-1699890186553-copied-1699889663524-copied-1699797991293-f5b47e5e-4121-44a3-8b29-97bfe2069148",
#       "to": "copied-1699890186553-copied-1699889663524-copied-1699797991293-eac6de73-9726-43b7-9441-f8e319a972e6"
#     },
#     {
#       "from": "copied-1699890186553-copied-1699797991293-07537a68-1c7e-4edb-a72f-2d82015c490f",
#       "id": "copied-1699890186553-copied-1699797991293-67194bdc-f1f3-417f-9778-4d163c8b82d1",
#       "to": "copied-1699890186553-copied-1699797991293-757e7439-08f8-4cea-afac-c25b01167d32"
#     },
#     {
#       "from": "copied-1699890186553-copied-1699797991293-2e419e7e-a540-4c9a-af4e-5110e54fad96",
#       "id": "copied-1699890186553-copied-1699797991293-33312b2e-b683-4489-b471-e2d1ca03d21a",
#       "to": "copied-1699890186553-copied-1699797991293-07537a68-1c7e-4edb-a72f-2d82015c490f"
#     },
#     {
#       "from": "copied-1699890186553-copied-1699797991293-1cc45118-72ee-4efe-95d8-06e8c02fb4c0",
#       "id": "copied-1699890186553-copied-1699797991293-1329a8be-e4e2-42fd-bdb6-2057f9c320d3",
#       "to": "copied-1699890186553-copied-1699797991293-2e419e7e-a540-4c9a-af4e-5110e54fad96"
#     },
#     {
#       "from": "copied-1699890186553-copied-1699797991293-c7d1c0a4-6365-44d6-be0c-bd3fc5436b85",
#       "id": "copied-1699890186553-copied-1699797991293-f4e2015e-e7f1-4e03-b3c6-ee82986533ca",
#       "to": "copied-1699890186553-copied-1699797991293-1cc45118-72ee-4efe-95d8-06e8c02fb4c0"
#     },
#     {
#       "from": "copied-1699890186553-copied-1699797991293-757e7439-08f8-4cea-afac-c25b01167d32",
#       "id": "copied-1699890186553-copied-1699797991293-f5b47e5e-4121-44a3-8b29-97bfe2069148",
#       "to": "copied-1699797991293-eac6de73-9726-43b7-9441-f8e319a972e6"
#     },
#     {
#       "from": "234ec0c2-3d02-4ef5-9fb1-7adaeb58a1b6",
#       "to": "copied-1699890186553-copied-1699889663524-copied-1699797991293-eac6de73-9726-43b7-9441-f8e319a972e6",
#       "id": "218594c0-41f7-4e0b-bea6-de7aa2349017"
#     }
#   ]
# }
#
# """
#
# graph_data = json.loads(json_graph_data)
#
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
