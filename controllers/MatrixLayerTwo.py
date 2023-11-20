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

            self.gpt_call_log = []

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

    # def update_gpt_call_with_responses(self, gpt_call, var_responses):
    #     """Update the GPT call by replacing @var terms with responses from var_responses."""
    #     updated_messages = []
    #
    #     # Find the highest variable suffix
    #     highest_suffix = 0
    #     for var in var_responses.keys():
    #         parts = var.split('_')
    #         suffix = int(parts[-1])
    #         highest_suffix = max(highest_suffix, suffix)
    #
    #     # Update the GPT call with responses and replace @variable_x_y with the next higher one
    #     for message in gpt_call['messages']:
    #         content = message['content']
    #         for var, response in var_responses.items():
    #             placeholder = f'@{var}'
    #             if placeholder in content:
    #                 content = content.replace(placeholder, response)
    #                 self.logger.debug(f"Replaced {placeholder} with {response} in GPT call.")
    #
    #                 # Replace @variable_x_y-1 with the next higher one
    #                 parts = var.split('_')
    #                 prefix = '_'.join(parts[:-1])
    #                 suffix = int(parts[-1])
    #                 if suffix == highest_suffix and suffix > 1:
    #                     prev_var = f'{prefix}_{suffix - 1}'
    #                     prev_placeholder = f'@{prev_var}'
    #                     if prev_placeholder in content:
    #                         content = content.replace(prev_placeholder, response)
    #                         self.logger.debug(f"Replaced {prev_placeholder} with {response} in GPT call.")
    #
    #         updated_messages.append({'role': message['role'], 'content': content})
    #
    #     gpt_call['messages'] = updated_messages
    #     self.logger.debug(f"Updated GPT call: {gpt_call}")
    #
    #     return gpt_call

    # def get_next_variable(self, current_var):
    #     """Get the next higher @variable based on current variable suffix."""
    #     parts = current_var.split('_')
    #     self.logger.info(parts)
    #     if len(parts) == 3:
    #         try:
    #             suffix = int(parts[-1]) + 1
    #             return f"{parts[0]}_{parts[1]}_{suffix}"
    #         except ValueError:
    #             pass
    #     return None

    # def process_graph_to_gpt_calls(self, graph, num_steps):
    #     organized_components = self.organize_components_by_variable_suffix(graph)
    #     self.log_info(organized_components)
    #
    #     variable_suffix_nodes = self.get_variable_suffix_nodes(organized_components)
    #     self.log_info(variable_suffix_nodes)
    #
    #     sorted_components_by_suffix = self.sort_components_by_suffix(organized_components)
    #     user_nodes = self.get_user_nodes(graph)
    #     self.log_info(user_nodes)
    #
    #     matched, unmatched = self.classify_gpt_calls(graph, user_nodes, variable_suffix_nodes, num_steps)
    #
    #     self.logger.info(matched)
    #     # breakpoint()
    #     var_responses = self.process_matched_gpt_calls(matched, sorted_components_by_suffix)
    #
    #     self.process_unmatched_gpt_calls(unmatched, var_responses)
    #
    #     self.save_gpt_calls_to_file()
    #     return var_responses

    # def get_variable_suffix_nodes(self, organized_components):
    #     return [node for nodes in organized_components.values() for node in nodes]
    #
    # def sort_components_by_suffix(self, organized_components):
    #     return sorted(organized_components.items(), key=lambda x: self.suffix_order_key(x[0]))
    #
    # def get_user_nodes(self, graph):
    #     return [node for node, attrs in graph.nodes(data=True) if attrs['label'] == 'user']
    #
    # def classify_gpt_calls(self, graph, user_nodes, variable_suffix_nodes, num_steps):
    #     matched = []
    #     unmatched = []
    #     for start_node in user_nodes:
    #         for path in self.explore_paths(graph, start_node, steps=num_steps):
    #             gpt_call = self.check_and_print_gpt_call(graph, path)
    #             self.log_info(gpt_call)
    #             if gpt_call:
    #                 if any(node in variable_suffix_nodes for node in path):
    #                     matched.append(gpt_call)
    #                 else:
    #                     unmatched.append(gpt_call)
    #     return matched, unmatched

    # def process_matched_gpt_calls(self, matched_calls, sorted_components):
    #
    #     # Write the parameters to JSON files
    #     with open('matched_calls.json', 'w') as matched_calls_file:
    #         json.dump(matched_calls, matched_calls_file, indent=4)
    #
    #     with open('sorted_components.json', 'w') as sorted_components_file:
    #         json.dump(sorted_components, sorted_components_file, indent=4)
    #
    #     breakpoint()
    #
    #     var_responses = {}
    #     for suffix, nodes in sorted_components:
    #         for gpt_call in matched_calls:
    #             # Check and process each GPT call only if all @variable terms are resolved
    #             if self.are_all_variables_resolved(gpt_call, var_responses):
    #                 updated_call, response = self.process_single_gpt_call(gpt_call, var_responses)
    #                 var_key = f"variable_{suffix}"
    #                 var_responses[var_key] = response
    #                 self.log_gpt_call(updated_call, response, var_key)
    #             else:
    #                 self.logger.error(f"Circuit break: Unresolved variables in GPT call: {gpt_call}")
    #                 raise Exception("Attempted to process a GPT call with unresolved @variable placeholders")
    #
    #     return var_responses

    # def are_all_variables_resolved(self, gpt_call, var_responses):
    #     """
    #     Check if all @variable placeholders in the GPT call are resolved.
    #     """
    #     for message in gpt_call['messages']:
    #         content = message['content']
    #         if any(f"@variable_{suffix}" in content for suffix in var_responses):
    #             return False
    #     return True


    # def process_unmatched_gpt_calls(self, unmatched_calls, var_responses):
    #     for gpt_call in unmatched_calls:
    #         updated_call, response = self.process_single_gpt_call(gpt_call, var_responses)
    #         self.log_gpt_call(updated_call, response)

    # def process_single_gpt_call(self, gpt_call, var_responses):
    #     # Circuit break if the call contains unresolved variables
    #     if not self.are_all_variables_resolved(gpt_call, var_responses):
    #         self.logger.error(f"Circuit break: Attempted to process a GPT call with unresolved variables: {gpt_call}")
    #         raise Exception("Circuit break: Attempted to process a GPT call with unresolved @variable placeholders")
    #
    #     # If all variables are resolved, proceed with processing
    #     updated_call = self.update_gpt_call_with_responses(gpt_call, var_responses)
    #     self.logger.info(f"Processing GPT call: {updated_call}")
    #     response = self.get_gpt_response(updated_call)
    #     self.logger.info(f"GPT response received: {response}")
    #     return updated_call, response

    def save_gpt_calls_to_file(self):
        try:
            debug_timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            # with open(f'gpt_calls_{self.timestamp}.json', 'w') as file:
            with open(f'gpt_calls_{debug_timestamp}.json', 'w') as file:
                json.dump(self.gpt_call_log, file, indent=4)
        except Exception as e:
            self.logger.error(f"Error saving JSON file: {e}")

    def log_info(self, message):
        self.logger.info(message)

    def log_gpt_call(self, request, response, var_key=None):
        log_entry = {"request": request, "response": response}
        if var_key:
            log_entry["variable_key"] = var_key
        self.gpt_call_log.append(log_entry)
        self.log_info(log_entry)

    def suffix_order_key(self, suffix):
        """Key function for sorting suffixes in the order like 1_1, 1_2, 2_1, etc."""
        # Extract the numeric parts of the suffix
        parts = suffix.split('_')[1:]  # Ignore the 'variable' part
        return tuple(map(int, parts))

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

    def check_and_print_gpt_call(self, graph, path):
        """Check if the path matches the blueprint pattern and return the GPT call."""
        labels = [graph.nodes[node]['label'] for node in path]
        if self.is_valid_blueprint(labels):
            gpt_call = {
                "model": os.getenv("MODEL"),
                "messages": [
                    {"role": "user", "content": labels[1]},
                    {"role": "system", "content": labels[3]},
                    {"role": "user", "content": labels[5]}
                ]
            }
            return gpt_call
        else:
            return None

    def generate_gpt_call_json(self, graph, path, path_uuid, graph_id):
        """Generate a JSON representation of a GPT call with UUID and graph_id."""
        labels = [graph.nodes[node]['label'] for node in path]
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

    def get_answer_label(self, graph, path):
        """Get the label for the answer node, considering @variable terms."""
        # Find @variable nodes
        variable_nodes = self.find_variable_nodes()
        components_with_variables = self.find_connected_components_with_variables(graph, variable_nodes)

        # Check if any node in the path is part of a connected component with @variables
        for component in components_with_variables:
            if any(node in path for node in component):
                for node in component:
                    if node in variable_nodes:
                        return graph.nodes[node]['label']

        return "None"

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
        self.logger.info(response)
        if response.status_code == 200:
            self.logger.info(response.json()["choices"][0]["message"]["content"])
            return response.json()["choices"][0]["message"]["content"]
        else:
            raise Exception(f"Error in GPT request: {response.status_code}, {response.text}")

    def main(self):
        df = self.get_adjacency_matrix(self.graph_id).set_index("node_id")
        G = self.create_graph_from_adjacency(df)
        self.check_graph_correctly_recveied_via_matrix(G)  # ToDo :: Translate tree to logs
        self.check_degree_distribution(G)  # ToDo :: Translate Hist to logs or display it in analysis tab
        self.check_diameter_and_centrality(G)
        df_nodes = self.get_nodes()
        label_dict = df_nodes.set_index('id')['label'].to_dict()
        nx.set_node_attributes(G, label_dict, 'label')


mat_l_t = MatrixLayerTwo("20231117163236", "graph_to_agent_adjacency_matrices", "graph_to_agent")

# mat_l_t.get_edges()
# mat_l_t.get_nodes()
# mat_l_t.get_adjacency_matrix()

df = mat_l_t.get_adjacency_matrix().set_index("node_id")
G = mat_l_t.create_graph_from_adjacency(df)
G.number_of_edges()

# mat_l_t.check_diameter_and_centrality(G)
# mat_l_t.check_degree_distribution(G)
# mat_l_t.check_graph_correctly_recveied_via_matrix(G)

df_nodes = mat_l_t.get_nodes()
label_dict = df_nodes.set_index('id')['label'].to_dict()
nx.set_node_attributes(G, label_dict, 'label')

organized_components = mat_l_t.organize_components_by_variable_suffix(G)
mat_l_t.log_info(organized_components)

variable_suffix_nodes = mat_l_t.get_variable_suffix_nodes(organized_components)
mat_l_t.log_info(variable_suffix_nodes)

sorted_components_by_suffix = mat_l_t.sort_components_by_suffix(organized_components)
user_nodes = mat_l_t.get_user_nodes(G)
mat_l_t.log_info(user_nodes)

matched, unmatched = mat_l_t.classify_gpt_calls(G, user_nodes, variable_suffix_nodes, 10)

answers = mat_l_t.process_graph_to_gpt_calls(G, 10)
answers

var_matched_gpt_calls, var_unmatched_gpt_calls = mat_l_t.process_graph_to_gpt_calls(G, 10)
var_matched_gpt_calls
var_unmatched_gpt_calls

# mat_l_t.organize_components_by_variable_suffix(G)
# mat_l_t.process_graph_for_variables_layer(G)
