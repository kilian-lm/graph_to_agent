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
from google.api_core.exceptions import NotFound
import numpy as np
import uuid

import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict

from logger.CustomLogger import CustomLogger
from controllers.BigQueryHandler import BigQueryHandler
from sql_queries.adjacency_matrix_query import ADJACENCY_MATRIX_QUERY
from sql_queries.edges_query import EDGES_QUERY
from sql_queries.nodes_query import NODES_QUERY
from sql_queries.layer_find_variable import LAYER_FIND_VARIABLE

from sql_queries.gpt_call_blueprint import GPT_CALL_BLUEPRINT

from controllers.VariableConnectedComponentsProcessor import VariableConnectedComponentsProcessor

load_dotenv()


class GraphPatternProcessor(VariableConnectedComponentsProcessor):
    def __init__(self, num_steps, key):

        self.key = key
        print(self.key)
        self.log_file = f'{self.key}_graph_pattern_processor.log'
        print(self.log_file)
        self.log_dir = os.getenv('LOG_DIR_LOCAL')
        print(self.log_dir)
        self.log_level = logging.DEBUG
        print(self.log_level)
        self.logger = CustomLogger(self.log_file, self.log_level, self.log_dir)

        self.graph = None
        self.num_steps = num_steps
        self.temp_checkpoints_gpt_calls = os.getenv('TEMP_CHECKPOINTS_GPT_CALLS')

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

        except Exception as e:
            self.logger.error(f"Label could not be assigned to graph data: {e}")
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

        dir_path = self.temp_checkpoints_gpt_calls

        # Check if the directory exists, if not, create it
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        file_path = f"{self.temp_checkpoints_gpt_calls}/{graph_id}.jsonl"
        self.logger.info(f"file_path: {file_path}")

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

        return file_path

    def generate_gpt_call_json(self, path, path_uuid, key):
        """Generate a JSON representation of a GPT call with UUID and graph_id."""
        labels = [self.graph.nodes[node]['label'] for node in path]
        if self.is_valid_blueprint(labels):
            gpt_call_json = {
                "path": path,
                "gpt_call": {
                    "model": os.getenv('MODEL'),
                    "messages": [
                        {"role": "user", "content": labels[1]},
                        {"role": "system", "content": labels[3]},
                        {"role": "user", "content": labels[5]}
                    ]
                },
                "answer_node": {
                    "node_id": f"answer_{path[-1]}",
                    "label": self.get_answer_label(path, key)
                },
                "uuid": path_uuid,
                "graph_id": key
            }
            return gpt_call_json, True
        return {}, False

    def get_answer_label(self, path, key):
        """Get the label for the answer node, considering @variable terms."""
        # Find @variable nodes
        variable_nodes = self.find_variable_nodes(key)
        components_with_variables = self.find_connected_components_with_variables(variable_nodes)

        # Check if any node in the path is part of a connected component with @variables
        for component in components_with_variables:
            if any(node in path for node in component):
                for node in component:
                    if node in variable_nodes:
                        return self.graph.nodes[node]['label']

        return "None"

    def dump_to_bigquery(self, key, dataset_name):
        """Upload the JSONL data to BigQuery."""

        table_name = key
        file_path = f"{self.temp_checkpoints_gpt_calls}/{key}.jsonl"
        self.logger.info(f"file_path: {file_path}")

        table_id = f"{self.bq_client.project}.{dataset_name}.{table_name}"
        self.logger.info(f"table_id: {table_id}")

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
