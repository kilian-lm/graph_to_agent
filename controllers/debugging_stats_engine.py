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
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

import networkx as nx
from google.cloud import bigquery
import re
from collections import defaultdict
import uuid

load_dotenv()

from logger.CustomLogger import CustomLogger


# q_adj = """SELECT * FROM `enter-universes.graph_to_agent_adjacency_matrices.20231123102234_fed37e7d-aa97-466a-b723-cb1290fc452f`"""
# q_edges = """SELECT * FROM `enter-universes.graph_to_agent.edges_table` where graph_id = '20231123102234_fed37e7d-aa97-466a-b723-cb1290fc452f'"""
# q_nodes = """SELECT * FROM `enter-universes.graph_to_agent.nodes_table` where graph_id = '20231123102234_fed37e7d-aa97-466a-b723-cb1290fc452f'"""


class VariableConnectedComponentsProcessor:
    def __init__(self, graph):
        self.graph = graph
        try:
            bq_client_secrets = os.getenv('BQ_CLIENT_SECRETS')

            bq_client_secrets_parsed = json.loads(bq_client_secrets)
            self.bq_client_secrets = Credentials.from_service_account_info(bq_client_secrets_parsed)
            self.bq_client = bigquery.Client(credentials=self.bq_client_secrets,
                                             project=self.bq_client_secrets.project_id)
        except json.JSONDecodeError as e:
            raise
        except Exception as e:
            raise

    def process_graph(self):
        """Process the graph to find connected components with @variable nodes."""
        variable_nodes = self.find_variable_nodes()
        connected_components_with_variables = self.find_connected_components_with_variables(variable_nodes)
        for component in connected_components_with_variables:
            print("Connected Component containing @variable node:", list(component))

    def find_variable_nodes(self):
        """Find all @variable nodes."""
        variable_nodes = set()
        query = """
        SELECT * FROM `enter-universes.graph_to_agent.nodes_table`
        WHERE graph_id = "20231123102234_fed37e7d-aa97-466a-b723-cb1290fc452f" AND STARTS_WITH(label, "@")
        """
        query_job = self.bq_client.query(query)
        results = query_job.result()
        for row in results:
            node_id = row['id']
            variable_nodes.add(node_id)
        return variable_nodes

    def find_connected_components_with_variables(self, variable_nodes):
        """Find connected components that contain @variable nodes."""
        components_with_variables = []
        for component in nx.connected_components(self.graph):
            if any(node in variable_nodes for node in component):
                components_with_variables.append(component)
        return components_with_variables

    def organize_components_by_variable_suffix(self):
        """Organize connected components based on @variable suffixes."""
        variable_nodes = self.find_variable_nodes()
        connected_components = self.find_connected_components_with_variables(variable_nodes)
        components_dict = defaultdict(list)

        for component in connected_components:
            for node in component:
                if node in variable_nodes:
                    label = self.graph.nodes[node]['label']
                    variable_suffix = self.extract_variable_suffix(label)
                    if variable_suffix:
                        components_dict[variable_suffix].append(node)

        # Sorting the dictionary by variable suffixes
        ordered_components_dict = dict(sorted(components_dict.items(), key=lambda x: x[0]))

        for suffix, nodes in ordered_components_dict.items():
            print(f"Connected Component for @variable_{suffix}:", nodes)

    def extract_variable_suffix(self, label):
        """Extract the variable suffix from the label."""
        match = re.search(r"@(\w+_\d+_\d+)", label)
        return match.group(1) if match else None


class GraphPatternProcessor(VariableConnectedComponentsProcessor):
    def __init__(self, num_steps, key):

        self.key = key
        print(self.key)
        self.log_file = f'{self.key}_stats_engine_debug.log'
        print(self.log_file)
        self.log_dir = './temp_log'
        print(self.log_dir)
        self.log_level = logging.DEBUG
        print(self.log_level)
        self.logger = CustomLogger(self.log_file, self.log_level, self.log_dir)

        self.graph = None
        self.num_steps = num_steps
        try:
            bq_client_secrets = os.getenv('BQ_CLIENT_SECRETS')

            bq_client_secrets_parsed = json.loads(bq_client_secrets)
            self.bq_client_secrets = Credentials.from_service_account_info(bq_client_secrets_parsed)
            self.bq_client = bigquery.Client(credentials=self.bq_client_secrets,
                                             project=self.bq_client_secrets.project_id)

            q_adj = f"""SELECT * FROM `enter-universes.graph_to_agent_adjacency_matrices.{key}`"""

            self.df_adj = self.query_bigquery(q_adj)
            self.df_adj = pd.DataFrame(self.df_adj).set_index("node_id")

            self.graph = self.create_graph_from_adjacency(self.df_adj)
            self.logger.info(f"self.graph: {self.graph}")
            q_nodes = f"SELECT * FROM `enter-universes.graph_to_agent.nodes_table` where graph_id = '{key}'"
            self.logger.info(q_nodes)
            df_nodes = self.query_bigquery(q_nodes)
            # breakpoint()
            self.logger.info(f"df_nodes: {df_nodes}")
            # Adding labels to the nodes
            label_dict = df_nodes.set_index('id')['label'].to_dict()
            nx.set_node_attributes(self.graph, label_dict, 'label')

            missing_labels = [node for node in self.graph.nodes() if node not in label_dict]
            if missing_labels:
                self.logger.debug("Missing labels for nodes:", missing_labels)


        except json.JSONDecodeError as e:
            raise
        except Exception as e:
            raise

    def create_graph_from_adjacency(self, df_adj):
        """
        Create a NetworkX graph from an adjacency matrix DataFrame.
        Assumes that node identifiers are in the DataFrame's index.
        """
        import networkx as nx

        # Create a graph
        self.graph = nx.Graph()

        # Add nodes
        for node in df_adj.index:
            self.graph.add_node(node)

        # Add edges
        for i, row in df_adj.iterrows():
            for j, val in row.items():
                if val != 0:  # Assuming non-zero values indicate an edge
                    self.graph.add_edge(i, j)

        return self.graph

    def query_bigquery(self, sql_query):
        """
        Queries a BigQuery table and returns the results.

        Args:
            sql_query (str): The SQL query to be executed.

        Returns:
            bigquery.QueryJob: The result of the query.
        """

        # Execute the query
        query_job = self.bq_client.query(sql_query)

        return query_job.result().to_dataframe()  # Waits for the query to finish

    def process_graph(self, df_nodes):
        """
        Additional processing on the graph, like adding labels.
        """
        label_dict = df_nodes.set_index('id')['label'].to_dict()
        nx.set_node_attributes(self.graph, label_dict, 'label')

        # Any other graph processing steps can be added here

    def explore_paths(self, start_node, steps):
        """Explore all paths up to a certain number of steps from a start node."""
        paths = []
        self.dfs(start_node, [], steps, paths)
        return paths

    def dfs(self, node, path, steps, paths):
        """Depth-first search to explore paths."""
        if steps == 0 or node in path:
            return
        path.append(node)
        if len(path) == steps + 1:
            paths.append(path.copy())
        else:
            for neighbor in self.graph.neighbors(node):
                self.dfs(neighbor, path, steps - 1, paths)
        path.pop()

    def is_valid_blueprint(self, labels):
        """Check if labels sequence matches the blueprint pattern."""
        return (len(labels) == 6 and labels[0] == 'user' and labels[2] == 'system' and labels[4] == 'user' and
                all(label not in ['user', 'system'] for label in [labels[1], labels[3], labels[5]]))

    def save_gpt_calls_to_jsonl(self, graph_id):
        """Save GPT calls to a JSON Lines file with additional UUID and self.graph_id."""

        file_path = f"{graph_id}.jsonl"
        # missing_labels = [node for node in G.nodes() if node not in label_dict]
        # if missing_labels:
        #     print("Missing labels for nodes:", missing_labels)

        with open(file_path, 'w') as file:
            user_nodes = [node for node, attrs in self.graph.nodes(data=True) if attrs['label'] == 'user']
            for start_node in user_nodes:
                # Generate a UUID for each component path
                path_uuid = str(uuid.uuid4())
                for path in self.explore_paths(start_node, steps=self.num_steps):
                    gpt_call, is_valid = self.generate_gpt_call_json(path, path_uuid, graph_id)
                    if is_valid:
                        json_line = json.dumps(gpt_call)
                        file.write(json_line + '\n')

    def generate_gpt_call_json(self, path, path_uuid, graph_id):
        """Generate a JSON representation of a GPT call with UUID and graph_id."""
        labels = [self.graph.nodes[node]['label'] for node in path]
        if self.is_valid_blueprint(labels):
            gpt_call_json = {
                "path": path,
                "gpt_call": {
                    "model": "gpt-4",
                    "messages": [
                        {"role": "user", "content": labels[1]},
                        {"role": "system", "content": labels[3]},
                        {"role": "user", "content": labels[5]}
                    ]
                },
                "answer_node": {
                    "node_id": f"answer_{path[-1]}",
                    "label": self.get_answer_label(path)
                },
                "uuid": path_uuid,
                "graph_id": graph_id
            }
            return gpt_call_json, True
        return {}, False

    def get_answer_label(self, path):
        """Get the label for the answer node, considering @variable terms."""
        # Find @variable nodes
        variable_nodes = self.find_variable_nodes()
        components_with_variables = self.find_connected_components_with_variables(variable_nodes)

        # Check if any node in the path is part of a connected component with @variables
        for component in components_with_variables:
            if any(node in path for node in component):
                for node in component:
                    if node in variable_nodes:
                        return self.graph.nodes[node]['label']

        return "None"

    def dump_to_bigquery(self, table_name, dataset_name, file_path):
        """Upload the JSONL data to BigQuery."""
        table_id = f"{self.bq_client.project}.{dataset_name}.{table_name}"

        # Configure the load job
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
            autodetect=True
        )

        # Load the JSONL file to BigQuery
        with open(file_path, "rb") as source_file:
            job = self.bq_client.load_table_from_file(source_file, table_id, job_config=job_config)

        # Wait for the load job to complete
        job.result()

        print(f"Uploaded {file_path} to {table_id}")


# ToDo :: Test Run

import uuid
from controllers.MatrixLayerOne import MatrixLayerOne
# from controllers.v1GraphPatternProcessor import v1GraphPatternProcessor
from controllers.MatrixLayerTwo import MatrixLayerTwo
from controllers.v2GptAgentInteractions import v2GptAgentInteractions

timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
general_uuid = str(uuid.uuid4())
key = f"{timestamp}_{general_uuid}"

json_file_path = "./logics/simple_va_inheritance_20231117.json"

with open(json_file_path, 'r') as json_file:
    graph_data = json.load(json_file)

gpt_agent_interactions = v2GptAgentInteractions(key, os.getenv('GRAPH_DATASET_ID'))

gpt_agent_interactions.save_graph_data(graph_data, key)

matrix_layer_one = MatrixLayerOne(key, graph_data, os.getenv('MULTI_LAYERED_MATRIX_DATASET_ID'))

filename = matrix_layer_one.create_advanced_adjacency_matrix()
filename
matrix_layer_one.upload_jsonl_to_bigquery(filename, os.getenv('MULTI_LAYERED_MATRIX_DATASET_ID'))

matrix_layer_one.upload_to_bigquery(os.getenv('ADJACENCY_MATRIX_DATASET_ID'))

# matrix_layer_one.upload_jsonl_to_bigquery(os.getenv('ADJACENCY_MATRIX_DATASET_ID'), filename)

# '20231117163236_advanced_adjacency_matrix.jsonl'
# mat_l_t = MatrixLayerTwo(key, os.getenv('ADJACENCY_MATRIX_DATASET_ID'), os.getenv('GRAPH_DATASET_ID'))

# graph_processor = GraphPatternProcessor(G, 10)
graph_processor = GraphPatternProcessor(10, key)

# graph_processor.save_gpt_calls_to_jsonl('20231123102234_fed37e7d-aa97-466a-b723-cb1290fc452f.jsonl',
#                                         '20231123102234_fed37e7d-aa97-466a-b723-cb1290fc452f')

# filename = '20231123102234_fed37e7d-aa97-466a-b723-cb1290fc452f.jsonl'
# key ='20231123102234_fed37e7d-aa97-466a-b723-cb1290fc452f'

graph_processor.save_gpt_calls_to_jsonl(key)

graph_processor.dump_to_bigquery(filename, os.getenv('CURATED_CHAT_COMPLETIONS'), key)

from controllers.AnswerPatternProcessor import AnswerPatternProcessor

answer_pat_pro = AnswerPatternProcessor(key)

# answer_pat_pro.bq_handler.create_dataset_if_not_exists()
key

answer_pat_pro.dump_gpt_jsonl_to_bigquery(os.getenv('CURATED_CHAT_COMPLETIONS'), filename)
key
# ToDo :: Next up
answer_pat_pro.get_gpt_calls_blueprint()
answer_pat_pro.run()
