import networkx as nx
from google.cloud import bigquery
import re
from collections import defaultdict

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

load_dotenv()


class VariableConnectedComponentsProcessor:
    def __init__(self, timestamp, matrix_dataset_id, graph_dataset_id, graph):
        self.graph = graph
        self.timestamp = timestamp
        print(self.timestamp)
        self.log_file = f'{self.timestamp}_matrix_layer_two.log'
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
        # todo: hand form app.py graph_id , think about coherent logic to ident nodes with matrix
        # self.graph_id = graph_id
        # self.table_name = self.graph_id

        # self.graph_data = graph_data

        self.edges_tbl = "edges_table"
        self.nodes_tbl = "nodes_table"

        self.gpt_call_log = []

        self.matrix_dataset_id = matrix_dataset_id
        self.graph_dataset_id = graph_dataset_id
        self.bq_handler = BigQueryHandler(self.timestamp, self.graph_dataset_id)

    def process_graph(self):
        """Process the graph to find connected components with @variable nodes."""
        variable_nodes = self.find_variable_nodes()
        connected_components_with_variables = self.find_connected_components_with_variables(variable_nodes)
        for component in connected_components_with_variables:
            print("Connected Component containing @variable node:", list(component))

    # def find_variable_nodes(self):
    #     """Find all @variable nodes."""
    #     variable_nodes = set()
    #     query = """
    #     SELECT * FROM `enter-universes.graph_to_agent.nodes_table`
    #     WHERE graph_id = "20231114181549" AND STARTS_WITH(label, "@")
    #     """
    #     query_job = self.bq_client.query(query)
    #     results = query_job.result()
    #     for row in results:
    #         node_id = row['id']
    #         variable_nodes.add(node_id)
    #     return variable_nodes

    def find_variable_nodes(self):
        """Find all @variable nodes."""

        self.bq_handler = BigQueryHandler(self.timestamp, self.graph_dataset_id)
        table_ref = self.bq_handler.bigquery_client.dataset(self.graph_dataset_id).table(self.nodes_tbl)
        self.logger.info(table_ref)

        variable_nodes = set()

        query = LAYER_FIND_VARIABLE.format(tbl_ref=table_ref, graph_id=self.timestamp)

        # query = """
        # SELECT * FROM `enter-universes.graph_to_agent.nodes_table`
        # WHERE graph_id = "20231114181549" AND STARTS_WITH(label, "@")
        # """
        query_job = self.bq_handler.bigquery_client.query(query)
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
