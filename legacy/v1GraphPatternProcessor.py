import os
from dotenv import load_dotenv
import logging
from google.cloud import bigquery
import json

import uuid
from google.oauth2.service_account import Credentials

from logger.CustomLogger import CustomLogger
from controllers.BigQueryHandler import BigQueryHandler
from controllers.v1VariableConnectedComponentsProcessor import VariableConnectedComponentsProcessor
from controllers.MatrixLayerOne import MatrixLayerOne

load_dotenv()


class GraphPatternProcessor(VariableConnectedComponentsProcessor):
    def __init__(self, key, graph, num_steps):
        super().__init__(graph, key)
        self.graph = graph
        self.num_steps = num_steps
        # self.bq_client = bigquery.Client()
        bq_client_secrets = os.getenv('BQ_CLIENT_SECRETS')

        try:
            bq_client_secrets_parsed = json.loads(bq_client_secrets)
            self.bq_client_secrets = Credentials.from_service_account_info(bq_client_secrets_parsed)
            self.bq_client = bigquery.Client(credentials=self.bq_client_secrets,
                                             project=self.bq_client_secrets.project_id)
            # self.logger.info("BigQuery client successfully initialized.")
        except json.JSONDecodeError as e:
            # self.logger.error(f"Failed to parse BQ_CLIENT_SECRETS environment variable: {e}")
            raise
        except Exception as e:
            # self.logger.error(f"An error occurred while initializing the BigQuery client: {e}")
            raise

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

    def save_gpt_calls_to_jsonl(self, file_path, graph_id):
        """Save GPT calls to a JSON Lines file with additional UUID and graph_id."""
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

    def dump_to_bigquery(self, file_path, dataset_name, table_name):
        """Upload the JSONL data to BigQuery."""
        client = bigquery.Client()
        table_id = f"{client.project}.{dataset_name}.{table_name}"

        # Configure the load job
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
            autodetect=True
        )

        # Load the JSONL file to BigQuery
        with open(file_path, "rb") as source_file:
            job = client.load_table_from_file(source_file, table_id, job_config=job_config)

        # Wait for the load job to complete
        job.result()

        print(f"Uploaded {file_path} to {table_id}")


# class GraphPatternProcessor(VariableConnectedComponentsProcessor):
#     def __init__(self, key, matrix_dataset_id, graph_dataset_id, graph, num_steps):
#         super().__init__(graph,key)
#         self.graph = graph
#         self.num_steps = num_steps
#         self.key = key
#         print(self.key)
#         self.log_file = f'{self.key}_matrix_layer_two.log'
#         print(self.log_file)
#         self.log_dir = './temp_log'
#         print(self.log_dir)
#         self.log_level = logging.DEBUG
#         print(self.log_level)
#         self.logger = CustomLogger(self.log_file, self.log_level, self.log_dir)
#
#         self.openai_api_key = os.getenv('OPENAI_API_KEY')
#         self.openai_base_url = "https://api.openai.com/v1/chat/completions"
#         self.headers = {
#             'Content-Type': 'application/json',
#             'Authorization': f'Bearer {self.openai_api_key}'
#         }
#         # todo: hand form app.py graph_id , think about coherent logic to ident nodes with matrix
#         # self.graph_id = graph_id
#         # self.table_name = self.graph_id
#
#         # self.graph_data = graph_data
#
#         self.gpt_call_log = []
#
#         self.edges_tbl = "edges_table"
#         self.nodes_tbl = "nodes_table"
#         self.matrix_dataset_id = matrix_dataset_id
#         self.graph_dataset_id = graph_dataset_id
#         self.bq_handler = BigQueryHandler(self.key, self.graph_dataset_id)
#
#     def explore_paths(self, start_node, steps):
#         """Explore all paths up to a certain number of steps from a start node."""
#         paths = []
#         self.dfs(start_node, [], steps, paths)
#
#         # Filter out empty paths
#         non_empty_paths = [path for path in paths if path]
#
#         self.logger.info(non_empty_paths)
#         self.logger.info(steps)
#         return non_empty_paths
#
#     # def explore_paths(self, start_node, steps):
#     #     """Explore all paths up to a certain number of steps from a start node."""
#     #     paths = []
#     #     self.dfs(start_node, [], steps, paths)
#     #
#     #     self.logger.info(paths)
#     #     self.logger.info(steps)
#     #     return paths
#
#
#     def dfs(self, node, path, steps, paths):
#         """Depth-first search to explore paths."""
#
#         self.logger.info(node)
#         self.logger.info(path)
#         self.logger.info(steps)
#         self.logger.info(paths)
#
#         if steps == 0 or node in path:
#             return
#         path.append(node)
#         if len(path) == steps + 1:
#             paths.append(path.copy())
#         else:
#             for neighbor in self.graph.neighbors(node):
#                 self.logger.info(neighbor)
#                 self.dfs(neighbor, path, steps - 1, paths)
#         self.logger.info(path)
#
#         path.pop()
#
#     def is_valid_blueprint(self, labels):
#         """Check if labels sequence matches the blueprint pattern."""
#         return (len(labels) == 6 and labels[0] == 'user' and labels[2] == 'system' and labels[4] == 'user' and
#                 all(label not in ['user', 'system'] for label in [labels[1], labels[3], labels[5]]))
#
#     def save_gpt_calls_to_jsonl(self, file_path, graph_id):
#         """Save GPT calls to a JSON Lines file with additional UUID and graph_id."""
#         with open(file_path, 'w') as file:
#             user_nodes = [node for node, attrs in self.graph.nodes(data=True) if attrs['label'] == 'user']
#             self.logger.info(user_nodes)
#             # breakpoint()
#             for start_node in user_nodes:
#                 self.logger.info(start_node)
#                 # Generate a UUID for each component path
#                 path_uuid = str(uuid.uuid4())  # ToDo :: Backroll PK logic until here
#                 self.logger.info(path_uuid)
#                 for path in self.explore_paths(start_node, steps=self.num_steps):
#                     gpt_call, is_valid = self.generate_gpt_call_json(path, path_uuid, graph_id)
#                     self.logger.info(gpt_call)
#                     if is_valid:
#                         json_line = json.dumps(gpt_call)
#                         file.write(json_line + '\n')
#
#         return file_path
#
#     def generate_gpt_call_json(self, path, path_uuid, graph_id):
#         """Generate a JSON representation of a GPT call with UUID and graph_id."""
#         labels = [self.graph.nodes[node]['label'] for node in path]
#         self.logger.info(labels)
#         if self.is_valid_blueprint(labels):
#             gpt_call_json = {
#                 "path": path,
#                 "gpt_call": {
#                     "model": os.getenv("MODEL"),
#                     "messages": [
#                         {"role": "user", "content": labels[1]},
#                         {"role": "system", "content": labels[3]},
#                         {"role": "user", "content": labels[5]}
#                     ]
#                 },
#                 "answer_node": {
#                     "node_id": f"answer_{path[-1]}",
#                     "label": self.get_answer_label(path)
#                 },
#                 "uuid": path_uuid,
#                 "graph_id": graph_id
#             }
#             self.logger.info(gpt_call_json)
#             return gpt_call_json, True
#         return {}, False
#
#     def get_answer_label(self, path):
#         """Get the label for the answer node, considering @variable terms."""
#         # Find @variable nodes
#         variable_nodes = self.find_variable_nodes()
#         components_with_variables = self.find_connected_components_with_variables(variable_nodes)
#
#         # Check if any node in the path is part of a connected component with @variables
#         for component in components_with_variables:
#             if any(node in path for node in component):
#                 for node in component:
#                     if node in variable_nodes:
#                         return self.graph.nodes[node]['label']
#
#         return "None"
#
#     def dump_to_bigquery(self, file_path, dataset_name, table_name):
#         """Upload the JSONL data to BigQuery."""
#
#         # graph_to_agent_chat_completions
#
#         # client = bigquery.Client()
#         table_id = f"{self.bq_handler.bigquery_client.project}.{dataset_name}.{table_name}"
#
#         table = self.bq_handler.bigquery_client.create_table(table_id, exists_ok=True)
#
#         # Configure the load job
#         job_config = bigquery.LoadJobConfig(
#             source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
#             autodetect=True
#         )
#
#         # Load the JSONL file to BigQuery
#         with open(file_path, "rb") as source_file:
#             job = self.bq_handler.bigquery_client.load_table_from_file(source_file, table_id, job_config=job_config)
#
#         # Wait for the load job to complete
#         job.result()
#
#         print(f"Uploaded {file_path} to {table_id}")


# help(GraphPatternProcessor)
# json_file_path = "./logics/simple_va_inheritance_20231117.json"
#
# with open(json_file_path, 'r') as json_file:
#     graph_data = json.load(json_file)
#
# key = "20231123102234_fed37e7d-aa97-466a-b723-cb1290fc452f"
# # key = "20231117163236"
#
# matrix_layer_one = MatrixLayerOne(key, graph_data, "graph_to_agent")
# # #
# filename = matrix_layer_one.create_advanced_adjacency_matrix()
# filename
# matrix_layer_one.upload_jsonl_to_bigquery(filename, os.getenv('MULTI_LAYERED_MATRIX_DATASET_ID'))
# #
#
# from controllers.MatrixLayerTwo import MatrixLayerTwo
# import networkx as nx
# from collections import defaultdict
#
# mat_l_t = MatrixLayerTwo(key, os.getenv('ADJACENCY_MATRIX_DATASET_ID'), os.getenv('GRAPH_DATASET_ID'))
#
# mat_l_t.get_edges()
# mat_l_t.get_nodes()
# mat_l_t.get_adjacency_matrix()
#
# df = mat_l_t.get_adjacency_matrix().set_index("node_id")
# G = mat_l_t.create_graph_from_adjacency(df)
# G.number_of_edges()
#
# df_nodes = mat_l_t.get_nodes()
# label_dict = df_nodes.set_index('id')['label'].to_dict()
# nx.set_node_attributes(G, label_dict, 'label')
#
# # graph_pattern_processor = GraphPatternProcessor(key, os.getenv('ADJACENCY_MATRIX_DATASET_ID'), os.getenv('GRAPH_DATASET_ID'),
# #                                                 G, os.getenv('NUM_STEPS'))
#
# graph_pattern_processor = GraphPatternProcessor(key, G, os.getenv('NUM_STEPS'))
# graph_pattern_processor.process_graph()
#
# graph_pattern_processor.save_gpt_calls_to_jsonl('4_test_20231123.jsonl', key)
#
# graph_pattern_processor.dump_to_bigquery('4_test_20231120.jsonl', 'graph_to_agent_chat_completions', 'test_2')

# answer_pat_pro = AnswerPatternProcessor("20231117163236", "graph_to_agent_chat_completions")
#
# answer_pat_pro.bq_handler.create_dataset_if_not_exists()
#
# answer_pat_pro.dump_gpt_jsonl_to_bigquery("gpt_answer_8262cd2c-c5e5-4ad1-a418-0217131aba70_20231117163236.jsonl",
#                                           "graph_to_agent_chat_completions",
#                                           "gpt_answer_8262cd2c-c5e5-4ad1-a418-0217131aba70_20231117163236")
#
# answer_pat_pro.run()


# graph_pattern_processor = GraphPatternProcessor("20231117163236", "graph_to_agent_adjacency_matrices", "graph_to_agent", G, 10)
#
# graph_pattern_processor.graph
#
# user_nodes = [node for node, attrs in G.nodes(data=True) if attrs['label'] == 'user']
#
# graph_pattern_processor.get_answer_label()
# graph_pattern_processor.save_gpt_calls_to_jsonl('4_test_20231120.jsonl', '20231117163236')
