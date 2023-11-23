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

load_dotenv()

from logger.CustomLogger import CustomLogger

q_adj = """SELECT * FROM `enter-universes.graph_to_agent_adjacency_matrices.20231123102234_fed37e7d-aa97-466a-b723-cb1290fc452f`"""
q_edges = """SELECT * FROM `enter-universes.graph_to_agent.edges_table` where graph_id = '20231123102234_fed37e7d-aa97-466a-b723-cb1290fc452f'"""
q_nodes = """SELECT * FROM `enter-universes.graph_to_agent.nodes_table` where graph_id = '20231123102234_fed37e7d-aa97-466a-b723-cb1290fc452f'"""


class DebuggingDataScience():
    def __init__(self, key, graph, num_steps):
        bq_client_secrets = os.getenv('BQ_CLIENT_SECRETS')
        self.key = key
        print(self.key)
        self.log_file = f'{self.key}_bq_handler.log'
        print(self.log_file)
        self.log_dir = './temp_log'
        print(self.log_dir)
        self.log_level = logging.DEBUG
        print(self.log_level)
        self.logger = CustomLogger(self.log_file, self.log_level, self.log_dir)

        try:
            bq_client_secrets_parsed = json.loads(bq_client_secrets)
            self.bq_client_secrets = Credentials.from_service_account_info(bq_client_secrets_parsed)
            self.bq_client = bigquery.Client(credentials=self.bq_client_secrets,
                                             project=self.bq_client_secrets.project_id)
            self.logger.info("BigQuery client successfully initialized.")
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse BQ_CLIENT_SECRETS environment variable: {e}")
            raise
        except Exception as e:
            self.logger.error(f"An error occurred while initializing the BigQuery client: {e}")
            raise

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

    def create_graph_from_adjacency(self, df):
        """
        Create a NetworkX graph from an adjacency matrix DataFrame.
        Assumes that node identifiers are in the DataFrame's index.
        """

        # Create a graph
        G = nx.Graph()

        # Add nodes
        for node in df.index:
            G.add_node(node)

        # Add edges
        for i, row in df.iterrows():
            for j, val in row.items():
                if val != 0:  # Assuming non-zero values indicate an edge
                    G.add_edge(i, j)

        return G

    def process_graph(self):
        """Main method to process the graph."""
        user_nodes = [node for node, attrs in self.graph.nodes(data=True) if attrs['label'] == 'user']
        for start_node in user_nodes:
            for path in self.explore_paths(start_node, steps=self.num_steps):
                self.check_and_print_gpt_call(path)

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

    def check_and_print_gpt_call(self, path):
        """Check if the path matches the blueprint pattern and print the GPT call."""
        labels = [self.graph.nodes[node]['label'] for node in path]
        if self.is_valid_blueprint(labels):
            gpt_call = {
                "model": "gpt-4",
                "messages": [
                    {"role": "user", "content": labels[1]},
                    {"role": "system", "content": labels[3]},
                    {"role": "user", "content": labels[5]}
                ]
            }
            print("GPT Call:", gpt_call)
        else:
            print("Blueprint pattern not found in this path.")

    def is_valid_blueprint(self, labels):
        """Check if labels sequence matches the blueprint pattern."""
        return (len(labels) == 6 and labels[0] == 'user' and labels[2] == 'system' and labels[4] == 'user' and
                all(label not in ['user', 'system'] for label in [labels[1], labels[3], labels[5]]))


#     def __init__(self, key, graph, num_steps):

key = "20231123102234_fed37e7d-aa97-466a-b723-cb1290fc452f"
# DebuggingDataScience(key, None, None).query_bigquery(step_1)
debug_ds = DebuggingDataScience(key, None, None)
df_adj = debug_ds.query_bigquery(q_adj)
G = debug_ds.create_graph_from_adjacency(df_adj)

df_edges = debug_ds.query_bigquery(q_edges)
df_nodes = debug_ds.query_bigquery(q_nodes)
