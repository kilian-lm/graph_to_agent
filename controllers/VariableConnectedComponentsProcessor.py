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


class VariableConnectedComponentsProcessor:
    def __init__(self, graph, key):
        self.graph = graph
        self.key = key
        print(self.key)
        self.log_file = f'{self.key}_answer_pattern_processor.log'
        print(self.log_file)
        self.log_dir = './temp_log'
        print(self.log_dir)
        self.log_level = logging.DEBUG
        print(self.log_level)
        self.logger = CustomLogger(self.log_file, self.log_level, self.log_dir)

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

    def find_variable_nodes(self, key):
        """Find all @variable nodes."""
        variable_nodes = set()
        # query = """
        # SELECT * FROM `enter-universes.graph_to_agent.nodes_table`
        # WHERE graph_id = "20231123102234_fed37e7d-aa97-466a-b723-cb1290fc452f" AND STARTS_WITH(label, "@")
        # """

        query = f"SELECT * FROM `enter-universes.graph_to_agent.nodes_table` WHERE graph_id = '{key}' AND STARTS_WITH(label, '@')"
        query_job = self.bq_client.query(query)
        self.logger.info(f"Querying BigQuery for variable nodes: {query}")
        results = query_job.result()
        for row in results:
            node_id = row['id']
            self.logger.info(f"Found variable node: {node_id}")
            variable_nodes.add(node_id)
            self.logger.info(f"Variable nodes: {variable_nodes}")
        return variable_nodes

    def find_connected_components_with_variables(self, variable_nodes):
        """Find connected components that contain @variable nodes."""
        components_with_variables = []
        for component in nx.connected_components(self.graph):
            if any(node in variable_nodes for node in component):
                components_with_variables.append(component)
        return components_with_variables

    def organize_components_by_variable_suffix(self, key):
        """Organize connected components based on @variable suffixes."""
        variable_nodes = self.find_variable_nodes(key)
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

    @staticmethod
    def extract_variable_suffix(label):
        """Extract the variable suffix from the label."""
        match = re.search(r"@(\w+_\d+_\d+)", label)
        return match.group(1) if match else None
