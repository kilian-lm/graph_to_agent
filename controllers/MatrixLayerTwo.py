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

json_graph_data = """
{
  "nodes": [
    {
      "id": "07537a68-1c7e-4edb-a72f-2d82015c490f",
      "label": "Understood! As I'm an expert in the .puml syntax i will correct it"
    },
    {
      "id": "1cc45118-72ee-4efe-95d8-06e8c02fb4c0",
      "label": "The following is a .puml content generated by an agent. Please critically review it and correct any mistakes, especially ensuring it strictly adheres to .puml syntax and does not contain any elements from other diagramming languages like Mermaid"
    },
    {
      "id": "2e419e7e-a540-4c9a-af4e-5110e54fad96",
      "label": "system"
    },
    {
      "id": "757e7439-08f8-4cea-afac-c25b01167d32",
      "label": "user"
    },
    {
      "id": "c7d1c0a4-6365-44d6-be0c-bd3fc5436b85",
      "label": "user"
    },
    {
      "id": "eac6de73-9726-43b7-9441-f8e319a972e6",
      "label": "@variable_1_2"
    },
    {
      "id": "copied-1699797991293-eac6de73-9726-43b7-9441-f8e319a972e6",
      "label": "sequenceDiagramAlice->>John: Hello John, how are you?John-->>Alice: Great!Alice-)John: See you later!"
    },
    {
      "id": "copied-1699889663524-copied-1699797991293-c7d1c0a4-6365-44d6-be0c-bd3fc5436b85",
      "label": "user"
    },
    {
      "id": "copied-1699889663524-copied-1699797991293-07537a68-1c7e-4edb-a72f-2d82015c490f",
      "label": "Understood! , I'm agent-'Deductive Reasoning', solving problems like you just described. Please provide the problem-space for me to navigate it best as possible..."
    },
    {
      "id": "copied-1699889663524-copied-1699797991293-1cc45118-72ee-4efe-95d8-06e8c02fb4c0",
      "label": "You're agent-'Deductive Reasoning'. You're one agent out of 7 who try to model problem-spaces and suggest solutions based on logical reasoning, similar to the detectives of The Poisoned Chocolates Case. Your strength lies in deriving specific conclusions from general hypotheses. Utilize schemas like Modus Ponens, Modus Tollens, Hypothetical Syllogism, and Disjunctive Syllogism., in order to solve problems, you use one of the following schemas ['Modus Ponens', 'Modus Tollens', 'Hypothetical Syllogism', 'Disjunctive Syllogism']"
    },
    {
      "id": "copied-1699889663524-copied-1699797991293-2e419e7e-a540-4c9a-af4e-5110e54fad96",
      "label": "system"
    },
    {
      "id": "copied-1699889663524-copied-1699797991293-757e7439-08f8-4cea-afac-c25b01167d32",
      "label": "user"
    },
    {
      "id": "copied-1699890186553-copied-1699889663524-copied-1699797991293-eac6de73-9726-43b7-9441-f8e319a972e6",
      "label": "How would you model following problem-space?: There was a attack of the Palestinien sided group Hamas on Israel. Now Israel is bombing Gaza with heavy civiliens casualties. There is a total 'cleaning' of the Hamas in Gaza planned by Isralien-Army. There is a high danger that the whole region will fall into war.."
    },
    {
      "id": "copied-1699890186553-copied-1699797991293-07537a68-1c7e-4edb-a72f-2d82015c490f",
      "label": "Understood! I will review following .mmd"
    },
    {
      "id": "copied-1699890186553-copied-1699797991293-1cc45118-72ee-4efe-95d8-06e8c02fb4c0",
      "label": "You're an expert in mermeid .mmd and you nedd to review following .mmd"
    },
    {
      "id": "copied-1699890186553-copied-1699797991293-2e419e7e-a540-4c9a-af4e-5110e54fad96",
      "label": "system"
    },
    {
      "id": "copied-1699890186553-copied-1699797991293-757e7439-08f8-4cea-afac-c25b01167d32",
      "label": "user"
    },
    {
      "id": "copied-1699890186553-copied-1699797991293-c7d1c0a4-6365-44d6-be0c-bd3fc5436b85",
      "label": "user"
    },
    {
      "id": "234ec0c2-3d02-4ef5-9fb1-7adaeb58a1b6",
      "x": 1626.674810293892,
      "y": -632.9703327332509,
      "label": "@varibale_1_1"
    }
  ],
  "edges": [
    {
      "from": "07537a68-1c7e-4edb-a72f-2d82015c490f",
      "id": "67194bdc-f1f3-417f-9778-4d163c8b82d1",
      "to": "757e7439-08f8-4cea-afac-c25b01167d32"
    },
    {
      "from": "1cc45118-72ee-4efe-95d8-06e8c02fb4c0",
      "id": "1329a8be-e4e2-42fd-bdb6-2057f9c320d3",
      "to": "2e419e7e-a540-4c9a-af4e-5110e54fad96"
    },
    {
      "from": "2e419e7e-a540-4c9a-af4e-5110e54fad96",
      "id": "33312b2e-b683-4489-b471-e2d1ca03d21a",
      "to": "07537a68-1c7e-4edb-a72f-2d82015c490f"
    },
    {
      "from": "757e7439-08f8-4cea-afac-c25b01167d32",
      "id": "f5b47e5e-4121-44a3-8b29-97bfe2069148",
      "to": "eac6de73-9726-43b7-9441-f8e319a972e6"
    },
    {
      "from": "c7d1c0a4-6365-44d6-be0c-bd3fc5436b85",
      "id": "f4e2015e-e7f1-4e03-b3c6-ee82986533ca",
      "to": "1cc45118-72ee-4efe-95d8-06e8c02fb4c0"
    },
    {
      "from": "copied-1699889663524-copied-1699797991293-c7d1c0a4-6365-44d6-be0c-bd3fc5436b85",
      "id": "copied-1699889663524-copied-1699797991293-f4e2015e-e7f1-4e03-b3c6-ee82986533ca",
      "to": "copied-1699889663524-copied-1699797991293-1cc45118-72ee-4efe-95d8-06e8c02fb4c0"
    },
    {
      "from": "copied-1699889663524-copied-1699797991293-07537a68-1c7e-4edb-a72f-2d82015c490f",
      "id": "copied-1699889663524-copied-1699797991293-67194bdc-f1f3-417f-9778-4d163c8b82d1",
      "to": "copied-1699889663524-copied-1699797991293-757e7439-08f8-4cea-afac-c25b01167d32"
    },
    {
      "from": "copied-1699889663524-copied-1699797991293-2e419e7e-a540-4c9a-af4e-5110e54fad96",
      "id": "copied-1699889663524-copied-1699797991293-33312b2e-b683-4489-b471-e2d1ca03d21a",
      "to": "copied-1699889663524-copied-1699797991293-07537a68-1c7e-4edb-a72f-2d82015c490f"
    },
    {
      "from": "copied-1699889663524-copied-1699797991293-1cc45118-72ee-4efe-95d8-06e8c02fb4c0",
      "id": "copied-1699889663524-copied-1699797991293-1329a8be-e4e2-42fd-bdb6-2057f9c320d3",
      "to": "copied-1699889663524-copied-1699797991293-2e419e7e-a540-4c9a-af4e-5110e54fad96"
    },
    {
      "from": "copied-1699889663524-copied-1699797991293-757e7439-08f8-4cea-afac-c25b01167d32",
      "id": "copied-1699890186553-copied-1699889663524-copied-1699797991293-f5b47e5e-4121-44a3-8b29-97bfe2069148",
      "to": "copied-1699890186553-copied-1699889663524-copied-1699797991293-eac6de73-9726-43b7-9441-f8e319a972e6"
    },
    {
      "from": "copied-1699890186553-copied-1699797991293-07537a68-1c7e-4edb-a72f-2d82015c490f",
      "id": "copied-1699890186553-copied-1699797991293-67194bdc-f1f3-417f-9778-4d163c8b82d1",
      "to": "copied-1699890186553-copied-1699797991293-757e7439-08f8-4cea-afac-c25b01167d32"
    },
    {
      "from": "copied-1699890186553-copied-1699797991293-2e419e7e-a540-4c9a-af4e-5110e54fad96",
      "id": "copied-1699890186553-copied-1699797991293-33312b2e-b683-4489-b471-e2d1ca03d21a",
      "to": "copied-1699890186553-copied-1699797991293-07537a68-1c7e-4edb-a72f-2d82015c490f"
    },
    {
      "from": "copied-1699890186553-copied-1699797991293-1cc45118-72ee-4efe-95d8-06e8c02fb4c0",
      "id": "copied-1699890186553-copied-1699797991293-1329a8be-e4e2-42fd-bdb6-2057f9c320d3",
      "to": "copied-1699890186553-copied-1699797991293-2e419e7e-a540-4c9a-af4e-5110e54fad96"
    },
    {
      "from": "copied-1699890186553-copied-1699797991293-c7d1c0a4-6365-44d6-be0c-bd3fc5436b85",
      "id": "copied-1699890186553-copied-1699797991293-f4e2015e-e7f1-4e03-b3c6-ee82986533ca",
      "to": "copied-1699890186553-copied-1699797991293-1cc45118-72ee-4efe-95d8-06e8c02fb4c0"
    },
    {
      "from": "copied-1699890186553-copied-1699797991293-757e7439-08f8-4cea-afac-c25b01167d32",
      "id": "copied-1699890186553-copied-1699797991293-f5b47e5e-4121-44a3-8b29-97bfe2069148",
      "to": "copied-1699797991293-eac6de73-9726-43b7-9441-f8e319a972e6"
    },
    {
      "from": "234ec0c2-3d02-4ef5-9fb1-7adaeb58a1b6",
      "to": "copied-1699890186553-copied-1699889663524-copied-1699797991293-eac6de73-9726-43b7-9441-f8e319a972e6",
      "id": "218594c0-41f7-4e0b-bea6-de7aa2349017"
    }
  ]
}

"""

graph_data = json.loads(json_graph_data)


class MatrixLayerTwo:
    def __init__(self, timestamp, matrix_dataset_id, graph_dataset_id):
        try:
            # self.timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')

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

            self.matrix_dataset_id = matrix_dataset_id
            self.graph_dataset_id = graph_dataset_id
            self.bq_handler = BigQueryHandler(self.timestamp, self.graph_dataset_id)

            self.edges_tbl = "edges_table"
            self.nodes_tbl = "nodes_table"
            self.matrix_views = "matrix_views"
            self.edges_views = "edges_views"
            self.nodes_views = "nodes_views"
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse BQ_CLIENT_SECRETS environment variable: {e}")
            raise
        except Exception as e:
            self.logger.error(f"An error occurred while initializing the BigQuery client: {e}")
            raise

    def get_adjacency_matrix(self):
        self.bq_handler = BigQueryHandler(self.timestamp, self.matrix_dataset_id)
        table_ref = self.bq_handler.bigquery_client.dataset(self.matrix_dataset_id).table(self.timestamp)
        print(table_ref)
        query = ADJACENCY_MATRIX_QUERY.format(
            adjacency_matrix=table_ref)

        # self.bq_handler.create_view(self.matrix_views,
        #                             f'adjacency_matrix_{self.timestamp}',
        #                             query)

        query_job = self.bq_handler.bigquery_client.query(query)

        df = query_job.to_dataframe()

        return df

    def get_nodes(self):
        self.bq_handler = BigQueryHandler(self.timestamp, self.graph_dataset_id)
        table_ref = self.bq_handler.bigquery_client.dataset(self.graph_dataset_id).table(self.nodes_tbl)
        self.logger.info(table_ref)
        query = NODES_QUERY.format(
            tbl_ref=table_ref, graph_id=self.timestamp)

        self.logger.info(query)

        # self.bq_handler.create_view(self.nodes_views,
        #                             f'nodes_{self.timestamp}',
        #                             query)

        query_job = self.bq_handler.bigquery_client.query(query)

        df = query_job.to_dataframe()

        return df

    def get_edges(self):
        self.bq_handler = BigQueryHandler(self.timestamp, self.graph_dataset_id)
        table_ref = self.bq_handler.bigquery_client.dataset(self.graph_dataset_id).table(self.edges_tbl)

        query = EDGES_QUERY.format(
            tbl_ref=table_ref, graph_id=self.timestamp)

        # self.bq_handler.create_view(self.edges_views,
        #                             f'edges_{self.timestamp}',
        #                             query)

        query_job = self.bq_handler.bigquery_client.query(query)

        df = query_job.to_dataframe()

        return df

    def create_graph_from_adjacency(self, df):
        """
        Create a NetworkX graph from an adjacency matrix DataFrame.
        Assumes that node identifiers are in the DataFrame's index.
        """
        import networkx as nx

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

    def check_graph_correctly_recveied_via_matrix(self, G):
        import networkx as nx

        connected_components = list(nx.connected_components(G))
        number_of_subgraphs = len(connected_components)

        print("Number of connected components (subgraphs):", number_of_subgraphs)

        num_nodes = G.number_of_nodes()
        num_edges = G.number_of_edges()

        # Basic Graph Properties
        num_nodes = G.number_of_nodes()
        num_edges = G.number_of_edges()
        is_directed = nx.is_directed(G)

        print(is_directed)

        # Draw the Graph
        plt.figure(figsize=(8, 6))
        nx.draw(G, with_labels=False, font_weight='bold', node_color='skyblue', node_size=700)
        plt.title("Graph Visualization")
        plt.show()

    def check_degree_distribution(self, G):
        # Degree Distribution
        degrees = [G.degree(n) for n in G.nodes()]
        plt.figure(figsize=(8, 6))
        plt.hist(degrees, bins=range(min(degrees), max(degrees) + 1, 1), align='left')
        plt.title("Degree Distribution")
        plt.xlabel("Degree")
        plt.ylabel("Number of Nodes")
        plt.xticks(range(min(degrees), max(degrees) + 1, 1))
        plt.show()

    def check_diameter_and_centrality(self, G):
        num_nodes = G.number_of_nodes()
        num_edges = G.number_of_edges()
        degrees = [G.degree(n) for n in G.nodes()]
        # Average Degree
        average_degree = sum(degrees) / num_nodes

        # Diameter of the graph
        # As the graph might not be fully connected, we consider the largest connected component
        largest_cc = max(nx.connected_components(G), key=len)
        subgraph = G.subgraph(largest_cc)
        diameter = nx.diameter(subgraph)

        # Average Shortest Path Length
        avg_shortest_path_length = nx.average_shortest_path_length(subgraph)

        # Clustering Coefficient
        clustering_coefficient = nx.average_clustering(G)

        # Degree Centrality
        degree_centrality = nx.degree_centrality(G)

        # Display Advanced Statistics
        advanced_stats = {
            "Average Degree": average_degree,
            "Diameter": diameter,
            "Average Shortest Path Length": avg_shortest_path_length,
            "Average Clustering Coefficient": clustering_coefficient,
            "Degree Centrality": degree_centrality
        }

        return advanced_stats

    # def process_graph_to_gpt_calls(self, graph, num_steps):
    #     """Main method to process the graph."""
    #     user_nodes = [node for node, attrs in graph.nodes(data=True) if attrs['label'] == 'user']
    #     for start_node in user_nodes:
    #         for path in self.explore_paths(graph, start_node, steps=num_steps):
    #             self.check_and_print_gpt_call(graph, path)

    # def process_graph_to_gpt_calls(self, graph, num_steps):
    #     """Main method to process the graph and accumulate GPT calls."""
    #     user_nodes = [node for node, attrs in graph.nodes(data=True) if attrs['label'] == 'user']
    #     gpt_calls = []
    #     for start_node in user_nodes:
    #         for path in self.explore_paths(graph, start_node, steps=num_steps):
    #             gpt_call = self.check_and_print_gpt_call(graph, path)
    #             if gpt_call is not None:
    #                 gpt_calls.append(gpt_call)
    #     return gpt_calls

    def process_graph_to_gpt_calls(self, graph, num_steps):
        """Main method to process the graph and accumulate GPT calls."""
        # First, organize components by variable suffix.
        organized_components = self.organize_components_by_variable_suffix(graph)
        self.logger.info(organized_components)
        # Flatten the organized components to get a list of nodes involved.
        variable_suffix_nodes = [node for nodes in organized_components.values() for node in nodes]
        self.logger.info(variable_suffix_nodes)
        # Initialize the lists for the two types of nodes.
        matched_nodes_gpt_calls = []
        unmatched_nodes_gpt_calls = []

        user_nodes = [node for node, attrs in graph.nodes(data=True) if attrs['label'] == 'user']
        self.logger.info(user_nodes)
        for start_node in user_nodes:
            for path in self.explore_paths(graph, start_node, steps=num_steps):
                gpt_call = self.check_and_print_gpt_call(graph, path)
                self.logger.info(gpt_call)
                if gpt_call is not None:
                    # Check if any node in the path is in the variable_suffix_nodes
                    if any(node in variable_suffix_nodes for node in path):
                        matched_nodes_gpt_calls.append(gpt_call)
                        self.logger.info(matched_nodes_gpt_calls)
                    else:
                        unmatched_nodes_gpt_calls.append(gpt_call)
                        self.logger.info(unmatched_nodes_gpt_calls)

        return matched_nodes_gpt_calls, unmatched_nodes_gpt_calls

    def explore_paths(self, graph, start_node, steps):
        """Explore all paths up to a certain number of steps from a start node."""
        paths = []
        self.dfs(graph, start_node, [], steps, paths)
        return paths

    def dfs(self, graph, node, path, steps, paths):
        """Depth-first search to explore paths."""
        if steps == 0 or node in path:
            return
        path.append(node)
        if len(path) == steps + 1:
            paths.append(path.copy())
        else:
            for neighbor in graph.neighbors(node):
                self.dfs(graph, neighbor, path, steps - 1, paths)
        path.pop()

    # def check_and_print_gpt_call(self, graph, paths):
    #     """Check if the paths match the blueprint pattern and return a list of GPT calls."""
    #     gpt_calls = []
    #     for path in paths:
    #         self.logger.info(path)
    #         labels = [graph.nodes[node]['label'] for node in path]
    #         self.logger.info(labels)
    #
    #         if self.is_valid_blueprint(labels):
    #             gpt_call = {
    #                 "model": "gpt-4",
    #                 "messages": [
    #                     {"role": "user", "content": labels[1]},
    #                     {"role": "system", "content": labels[3]},
    #                     {"role": "user", "content": labels[5]}
    #                 ]
    #             }
    #             gpt_calls.append(gpt_call)
    #             self.logger.info(gpt_calls)
    #
    #         else:
    #             print("Blueprint pattern not found in path:", path)
    #
    #     return gpt_calls

    # def check_and_print_gpt_call(self, graph, path):
    #     """Check if the path matches the blueprint pattern and print the GPT call."""
    #     labels = [graph.nodes[node]['label'] for node in path]
    #     if self.is_valid_blueprint(labels):
    #         gpt_call = {
    #             "model": "gpt-4",
    #             "messages": [
    #                 {"role": "user", "content": labels[1]},
    #                 {"role": "system", "content": labels[3]},
    #                 {"role": "user", "content": labels[5]}
    #             ]
    #         }
    #         print("GPT Call:", gpt_call)
    #         return gpt_call
    #     else:
    #         print("Blueprint pattern not found in this path.")

    def check_and_print_gpt_call(self, graph, path):
        """Check if the path matches the blueprint pattern and return the GPT call."""
        labels = [graph.nodes[node]['label'] for node in path]
        if self.is_valid_blueprint(labels):
            gpt_call = {
                "model": "gpt-4",
                "messages": [
                    {"role": "user", "content": labels[1]},
                    {"role": "system", "content": labels[3]},
                    {"role": "user", "content": labels[5]}
                ]
            }
            return gpt_call
        else:
            return None

    def is_valid_blueprint(self, labels):
        """Check if labels sequence matches the blueprint pattern."""
        return (len(labels) == 6 and labels[0] == 'user' and labels[2] == 'system' and labels[4] == 'user' and
                all(label not in ['user', 'system'] for label in [labels[1], labels[3], labels[5]]))

    def process_graph_for_variables_layer(self, graph):
        """Process the graph to find connected components with @variable nodes."""
        variable_nodes = self.find_variable_nodes()
        connected_components_with_variables = self.find_connected_components_with_variables(graph, variable_nodes)
        for component in connected_components_with_variables:
            print("Connected Component containing @variable node:", list(component))

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

    def find_connected_components_with_variables(self, graph, variable_nodes):
        """Find connected components that contain @variable nodes."""
        components_with_variables = []
        for component in nx.connected_components(graph):
            if any(node in variable_nodes for node in component):
                components_with_variables.append(component)
        return components_with_variables

    def organize_components_by_variable_suffix(self, graph):
        """Organize connected components based on @variable suffixes."""
        variable_nodes = self.find_variable_nodes()
        connected_components = self.find_connected_components_with_variables(graph, variable_nodes)
        components_dict = defaultdict(list)

        for component in connected_components:
            for node in component:
                if node in variable_nodes:
                    label = graph.nodes[node]['label']
                    variable_suffix = self.extract_variable_suffix(label)
                    if variable_suffix:
                        components_dict[variable_suffix].append(node)

        # Sorting the dictionary by variable suffixes
        ordered_components_dict = dict(sorted(components_dict.items(), key=lambda x: x[0]))

        for suffix, nodes in ordered_components_dict.items():
            print(f"Connected Component for @variable_{suffix}:", nodes)

        return ordered_components_dict

    def extract_variable_suffix(self, label):
        """Extract the variable suffix from the label."""
        match = re.search(r"@(\w+_\d+_\d+)", label)
        return match.group(1) if match else None

    def get_gpt_response(self, processed_data):
        self.logger.debug(processed_data)
        response = requests.post(self.openai_base_url, headers=self.headers, json=processed_data)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            raise Exception(f"Error in GPT request: {response.status_code}, {response.text}")

    def orchestrator_process_graph(self):
        """Extend the processing to include request orchestration."""

        # ToDo :
        # 1. Just get gpt calls queued running without @variable
        # 2.

        super().process_graph()
        self.enqueue_requests()
        self.process_requests()

    def main(self):
        df = self.get_adjacency_matrix(self.graph_id).set_index("node_id")
        G = self.create_graph_from_adjacency(df)
        self.check_graph_correctly_recveied_via_matrix(G)  # ToDo :: Translate tree to logs
        self.check_degree_distribution(G)  # ToDo :: Translate Hist to logs or display it in analysis tab
        self.check_diameter_and_centrality(G)
        df_nodes = self.get_nodes()
        label_dict = df_nodes.set_index('id')['label'].to_dict()
        nx.set_node_attributes(G, label_dict, 'label')


mat_l_t = MatrixLayerTwo("20231117163236","graph_to_agent_adjacency_matrices", "graph_to_agent")

mat_l_t.get_edges()
mat_l_t.get_nodes()
mat_l_t.get_adjacency_matrix()

df = mat_l_t.get_adjacency_matrix().set_index("node_id")
G = mat_l_t.create_graph_from_adjacency(df)
G.number_of_edges()

mat_l_t.check_diameter_and_centrality(G)
mat_l_t.check_degree_distribution(G)
mat_l_t.check_graph_correctly_recveied_via_matrix(G)
df_nodes = mat_l_t.get_nodes()

label_dict = df_nodes.set_index('id')['label'].to_dict()
nx.set_node_attributes(G, label_dict, 'label')

gpt_calls = mat_l_t.process_graph_to_gpt_calls(G, 15)

var_matched_gpt_calls, var_unmatched_gpt_calls = mat_l_t.process_graph_to_gpt_calls(G, 10)
var_matched_gpt_calls
var_unmatched_gpt_calls

# mat_l_t.organize_components_by_variable_suffix(G)
# mat_l_t.process_graph_for_variables_layer(G)
