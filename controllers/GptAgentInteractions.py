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

# custom classes
from logger.CustomLogger import CustomLogger
from controllers.MatrixLayerOne import MatrixLayerOne
from controllers.BigQueryHandler import BigQueryHandler

load_dotenv()


# assumption: new methods allows chaining of agents but != recursive calls because @var isnt integrated yet

# class v2GptAgentInteractions(MatrixLayerOne):

class GptAgentInteractions():

    def __init__(self, key):
        self.key = key
        print(self.key)
        self.log_file = f'{self.key}_gpt_agent_interactions.log'
        print(self.log_file)
        self.log_dir = './temp_log'
        print(self.log_dir)
        self.log_level = logging.DEBUG
        print(self.log_level)
        self.logger = CustomLogger(self.log_file, self.log_level, self.log_dir)

        self.graph_dataset_id = os.getenv('GRAPH_DATASET_ID')
        self.graph_to_agent_adjacency_matrices = os.getenv('MATRIX_DATASET_ID')
        self.edges_table = os.getenv('EDGES_TABLE')
        self.nodes_table = os.getenv('NODES_TABLE')
        self.graph_data = None

        # self.matrix_layer_one = MatrixLayerOne(self.key, self.graph_data, self.graph_to_agent_adjacency_matrices)
        self.bq_handler = BigQueryHandler(self.key)

        self.dataset_id = os.getenv('GRAPH_DATASET_ID')

    def get_node_schema(self):
        return [
            bigquery.SchemaField("graph_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("label", "STRING", mode="REQUIRED")
        ]

    def get_edge_schema(self):
        return [
            bigquery.SchemaField("graph_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("from", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("to", "STRING", mode="REQUIRED")
        ]

    # def get_available_graphs(self):
    #     # Query to get distinct graph_ids from the nodes_table
    #     # query = f"SELECT DISTINCT graph_id FROM `{self.bq_handler.bigquery_client.project}.{self.dataset_id}.{self.nodes_table}`"
    #     query = f"SELECT DISTINCT selected_answer FROM `enter-universes.random_string_look_up.selected_answers` "
    #     self.logger.info(query)
    #     query_job = self.bq_handler.bigquery_client.query(query)
    #     results = query_job.result()
    #
    #     # return [{"graph_id": row["graph_id"], "graph_name": row["graph_id"]} for row in results]
    #     return [{"selected_answer": row["selected_answer"], "graph_name": row["selected_answer"]} for row in results]

    def get_available_graphs(self):
        # Query to get distinct selected_answers and their corresponding graph_ids
        # query = f"-- SELECT DISTINCT selected_answer, graph_id FROM `enter-universes.random_string_look_up.selected_answers`"

        query = f"""
        SELECT ANY_VALUE(selected_answer) as selected_answer, graph_id
        FROM `enter-universes.random_string_look_up.selected_answers`
        GROUP BY graph_id
        """

        self.logger.info(query)
        query_job = self.bq_handler.bigquery_client.query(query)
        results = query_job.result()

        return [{"selected_answer": row["selected_answer"], "graph_id": row["graph_id"],
                 "graph_name": row["selected_answer"]} for row in results]

    def load_graph_data_by_id(self, dataset_id, graph_id, nodes_table, edges_table, answers_table):
        try:
            # Initialize BigQuery client
            client = self.bq_handler.bigquery_client

            # Fetch nodes and edges for the given graph_id
            nodes = self.fetch_data(client, dataset_id, nodes_table, graph_id, 'nodes')
            original_edges = self.fetch_data(client, dataset_id, edges_table, graph_id, 'edges')
            self.logger.info(f"Nodes and edges loaded for graph id {graph_id}.")

            # Fetch answer nodes
            answers = self.fetch_data(client, os.getenv('ANSWER_CURATED_CHAT_COMPLETIONS'), answers_table, graph_id,
                                      'answers', is_answers=True)
            self.logger.info(f"Answers loaded for graph id {graph_id}.")

            # Combine nodes and answers
            nodes.extend(answers)

            # Initialize a set to track existing edges and avoid duplicates
            existing_edges = set()

            # Add original edges to the set and the final edge list, checking for duplicates
            edges = []
            for edge in original_edges:
                edge_pair = (edge['from'], edge['to'])
                if edge_pair not in existing_edges:
                    edges.append(edge)
                    existing_edges.add(edge_pair)

            # Create edges to connect answer nodes to their corresponding original nodes
            for answer in answers:
                if answer['id'].startswith('answer_'):
                    origin_node_id = answer['id'].replace('answer_', '')
                    edge_pair = (origin_node_id, answer['id'])

                    # Only add a new edge if it does not exist already
                    if edge_pair not in existing_edges:
                        new_edge = {
                            'from': origin_node_id,
                            'to': answer['id']
                        }
                        edges.append(new_edge)
                        existing_edges.add(edge_pair)  # Add this new edge to the set of existing edges

            return {"nodes": nodes, "edges": edges}
        except NotFound as e:
            self.logger.error(f"Table not found in specified location: {e}")
            # Handle the error appropriately
        except Exception as e:
            self.logger.error(f"Error fetching graph data: {e}")
            # Handle other exceptions

    def fetch_data(self, client, dataset_id, table_id, graph_id, data_type, is_answers=False):
        if is_answers:
            # For answer nodes, extract node_id and label from the answer_node record
            query = f"""
            SELECT answer_node.node_id as id, answer_node.label 
            FROM `{self.bq_handler.bigquery_client.project}.{table_id}.{graph_id}` 
            WHERE graph_id = '{graph_id}'
            """
            self.logger.info(query)
        else:
            # Regular query for nodes or edges
            query = f"SELECT * FROM `{dataset_id}.{table_id}` WHERE graph_id = '{graph_id}'"
            self.logger.info(query)
        query_job = client.query(query)
        results = query_job.result()

        # Processing the results based on data type
        if data_type == 'edges':
            data = [{"from": row['from'], "to": row['to']} for row in results]
        else:
            # This handles both nodes and answer nodes, as the structure is now similar
            data = [{"id": row['id'], "label": row['label']} for row in results]

        return data

    # def load_graph_data_by_id(self, dataset_id, graph_id, nodes_table, edges_table, answers_table):
    #     # Fetch nodes for given graph_id
    #     nodes_query = f"SELECT * FROM `{dataset_id}.{nodes_table}` WHERE graph_id = '{graph_id}'"
    #     nodes_query_job = self.bq_handler.bigquery_client.query(nodes_query)
    #     nodes_results = nodes_query_job.result()
    #     nodes = [{"id": row['id'], "label": row['label']} for row in nodes_results]
    #
    #     # Fetch edges for given graph_id
    #     edges_query = f"SELECT * FROM `{dataset_id}.{edges_table}` WHERE graph_id = '{graph_id}'"
    #     edges_query_job = self.bq_handler.bigquery_client.query(edges_query)
    #     edges_results = edges_query_job.result()
    #     edges = [{"from": row['from'], "to": row['to']} for row in edges_results]
    #
    #     # Integrate answer nodes into graph data
    #     answers_query = f"SELECT DISTINCT node_id, label FROM `{dataset_id}.{answers_table}` WHERE graph_id = '{graph_id}'"
    #     answers_query_job = self.bq_handler.bigquery_client.query(answers_query)
    #     answers_results = answers_query_job.result()
    #
    #     for row in answers_results:
    #         modified_node_id = row.node_id.replace('answer_', '')
    #         matching_node = next((node for node in nodes if node['id'] == modified_node_id), None)
    #
    #         if matching_node:
    #             # Add a new node for the answer
    #             new_node = {
    #                 'id': row.node_id,  # Use the node_id from the query
    #                 'label': row.label
    #             }
    #             nodes.append(new_node)
    #
    #             # Add a new edge connecting the matching node to the new node
    #             new_edge = {
    #                 'from': matching_node['id'],
    #                 'to': row.node_id  # Connect to the new node
    #             }
    #             edges.append(new_edge)
    #
    #     return {"nodes": nodes, "edges": edges}

    # def load_graph_data_by_id(self, graph_id):
    #     # nodes_table_ref = self.bq_handler.bigquery_client.dataset(self.dataset_id).table("nodes_table")
    #     # edges_table_ref = self.bq_handler.bigquery_client.dataset(self.dataset_id).table("edges_table")
    #
    #     # Fetch nodes for given graph_id
    #     nodes_query = f"SELECT * FROM `{self.bq_handler.bigquery_client.project}.{self.dataset_id}.{self.nodes_table}` WHERE graph_id = '{graph_id}'"
    #     self.logger.info(nodes_query)
    #     nodes_query_job = self.bq_handler.bigquery_client.query(nodes_query)
    #     nodes_results = nodes_query_job.result()
    #     nodes = [{"id": row['id'], "label": row['label']} for row in nodes_results]
    #
    #     self.logger.info(f"nodes loaded by graph id {nodes} already exists.")
    #
    #     # Fetch edges for given graph_id
    #     edges_query = f"SELECT * FROM `{self.bq_handler.bigquery_client.project}.{self.dataset_id}.{self.edges_table}` WHERE graph_id = '{graph_id}'"
    #     self.logger.info(edges_query)
    #     edges_query_job = self.bq_handler.bigquery_client.query(edges_query)
    #     edges_results = edges_query_job.result()
    #     edges = [{"from": row['from'], "to": row['to']} for row in edges_results]
    #
    #     return {"nodes": nodes, "edges": edges}

    def load_json_graph(self, json_graph_data):
        graph_data = json.loads(json_graph_data)
        return graph_data

    def provide_root_nodes(self, graph_data):
        root_nodes = [node['id'] for node in graph_data['nodes'] if
                      not any(edge['to'] == node['id'] for edge in graph_data['edges'])]

        return root_nodes

    def translate_graph_data_for_bigquery(self, graph_data, graph_id):
        # Extract nodes and edges from the graph data
        raw_nodes = graph_data.get('nodes', [])
        raw_edges = graph_data.get('edges', [])

        # Translate nodes
        nodes_for_bq = [
            {
                "graph_id": graph_id,
                "id": node.get('id'),
                "label": node.get('label')
            }
            for node in raw_nodes
        ]

        self.logger.info(f"nodes_for_bq: {nodes_for_bq}")

        # Translate edges
        edges_for_bq = [
            {
                "graph_id": graph_id,
                "from": edge.get('from'),
                "to": edge.get('to')
            }
            for edge in raw_edges
        ]

        self.logger.info(f"edges_for_bq: {edges_for_bq}")

        return nodes_for_bq, edges_for_bq

    def get_node_type(self, node):
        if 'user' in node['label'].lower():
            return 'user'
        elif 'system' in node['label'].lower():
            return 'system'
        else:
            return 'content'

    # def translate_graph_to_gpt_sequence(self, graph_data):
    #     nodes = graph_data["nodes"]
    #     edges = graph_data["edges"]
    #
    #     # Build a mapping of node IDs to nodes
    #     node_mapping = {node['id']: node for node in nodes}
    #     self.logger.info(f"node_map: {node_mapping}")
    #
    #     # Initialize the data structure
    #     translated_data = {
    #         "model": os.getenv("MODEL"),
    #         "messages": []
    #     }
    #
    #     self.logger.info(f"translated_data: {translated_data}")
    #
    #     # Define valid transitions
    #     valid_transitions = {
    #         'user': 'content',
    #         'content': 'system',
    #         'system': 'content'
    #     }
    #
    #     # Start from 'user' nodes and follow the valid transitions
    #     current_expected = 'user'
    #
    #     for edge in edges:
    #         from_node = node_mapping[edge['from']]
    #         to_node = node_mapping[edge['to']]
    #
    #         self.logger.info(f"from_node: {from_node}")
    #         self.logger.info(f"to_node: {to_node}")
    #
    #         from_node_type = self.get_node_type(from_node)
    #         to_node_type = self.get_node_type(to_node)
    #
    #         self.logger.info(f"from_node_type: {from_node_type}")
    #         self.logger.info(f"to_node_type: {to_node_type}")
    #
    #     # Serialize data to json
    #     json_data = json.dumps(translated_data, indent=4)
    #     filename = f"temp_local/processed_graph_{self.key}.json"
    #
    #     # Check if the temp_local directory exists
    #     if not os.path.exists('temp_local'):
    #         os.makedirs('temp_local')
    #
    #     # Save the JSON data to the file
    #     with open(filename, 'w') as json_file:
    #         json_file.write(json_data)
    #
    #     # breakpoint()  # todo ::
    #
    #     return {
    #         'bigquery_errors': {'node_errors': [], 'edge_errors': []},
    #         'processed_data': translated_data
    #     }

    def get_last_content_node(self, edges, nodes):
        # Assuming edges are ordered
        last_edge = edges[-1]
        last_node_id = last_edge['to']

        self.logger.info(f"get_last_content_node, last_node_id : {last_node_id}")

        for node in nodes:
            if node['id'] == last_node_id:
                return node
        return None

    # def get_gpt_response(self, processed_data):
    #     # post_data = {
    #     #     # "model": os.getenv("MODEL"),
    #     #     "model":processed_data["model"],
    #     #     "messages": processed_data["messages"]
    #     # }
    #     self.logger.debug(processed_data)
    #     response = requests.post(self.openai_base_url, headers=self.headers, json=processed_data)
    #     if response.status_code == 200:
    #         return response.json()["choices"][0]["message"]["content"]
    #     else:
    #         raise Exception(f"Error in GPT request: {response.status_code}, {response.text}")

    def process_gpt_response_and_update_graph(self, gpt_response, graph_data):
        last_content_node = self.get_last_content_node(graph_data['edges'], graph_data['nodes'])

        self.logger.info(f"process_gpt_response_and_update_graph, last_content_node : {last_content_node}")

        # Generate a unique ID for the new node
        new_node_id = f"agent_response_based_on{last_content_node['id']}"
        new_node = {
            'id': new_node_id,
            'label': gpt_response,
        }

        self.logger.info(f"process_gpt_response_and_update_graph, new_node : {new_node}")

        # Check if a node with the new ID already exists
        existing_node_ids = {node['id'] for node in graph_data['nodes']}
        if new_node_id not in existing_node_ids:
            graph_data['nodes'].append(new_node)
            # Create a new edge from the last content node to the new node
            new_edge = {
                'from': last_content_node['id'],
                'to': new_node_id,
            }
            graph_data['edges'].append(new_edge)
            self.logger.info(f"process_gpt_response_and_update_graph, new_edge : {new_edge}")
        else:
            self.logger.info(f"Node with ID {new_node_id} already exists. Skipping node and edge addition.")

        self.logger.info(f"process_gpt_response_and_update_graph, graph_data : {graph_data}")

        # debugging:
        graph_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        self.save_graph_data(graph_data, graph_id)
        return graph_data

    def populate_variable_nodes(self, graph_data, gpt_response):
        # Iterate through the nodes in the graph_data
        for node in graph_data['nodes']:
            # Check if the node contains '@variable'
            if '@variable' in node['label']:
                # Replace '@variable' with the GPT response
                node['label'] = node['label'].replace('@variable', gpt_response)

                # Assign a versioned node ID
                node['id'] = f"{node['id']}_v1"  # Assuming recursion_depth is always 1 for simplicity

        return graph_data

    def save_graph_data(self, graph_data, graph_id):
        try:
            self.bq_handler.create_dataset_if_not_exists(self.graph_dataset_id)

            # self.bq_handler.create_dataset_if_not_exists(os.getenv())

            nodes_table_ref = self.bq_handler.bigquery_client.dataset(self.dataset_id).table(self.nodes_table)
            edges_table_ref = self.bq_handler.bigquery_client.dataset(self.dataset_id).table(self.edges_table)

            # Check and create nodes table if it doesn't exist
            self.bq_handler.create_table_if_not_exists(self.graph_dataset_id, self.nodes_table, self.get_node_schema())

            # Check and create edges table if it doesn't exist
            self.bq_handler.create_table_if_not_exists(self.graph_dataset_id, self.edges_table, self.get_edge_schema())

            # Retrieve the tables and their schemas
            self.nodes_table = self.bq_handler.bigquery_client.get_table(nodes_table_ref)
            self.edges_table = self.bq_handler.bigquery_client.get_table(edges_table_ref)

            # Use the translator function to transform the data
            nodes_for_bq, edges_for_bq = self.translate_graph_data_for_bigquery(graph_data, graph_id)

            # Log the transformed data for debugging
            self.logger.info(f"controller save_graph_data, Transformed Nodes: {nodes_for_bq}")
            self.logger.info(f"controller save_graph_data, Transformed Edges: {edges_for_bq}")

            # Insert nodes and pass in the schema explicitly
            errors_nodes = self.bq_handler.bigquery_client.insert_rows(self.nodes_table, nodes_for_bq,
                                                                       selected_fields=self.nodes_table.schema)
            if errors_nodes:
                self.logger.info(f"Encountered errors while inserting nodes: {errors_nodes}")

            # Insert edges and pass in the schema explicitly
            errors_edges = self.bq_handler.bigquery_client.insert_rows(self.edges_table, edges_for_bq,
                                                                       selected_fields=self.edges_table.schema)
            if errors_edges:
                self.logger.info(f"Encountered errors while inserting edges: {errors_edges}")

            if errors_nodes or errors_edges:
                self.logger.error("Errors occurred during the saving of graph data.")

            # Save the transformed data as dictionaries for the workflow
            # This assumes that the data is already in a dictionary format suitable for the workflow
            graph_data_as_dicts = {
                "nodes": nodes_for_bq,
                "edges": edges_for_bq
            }

            self.logger.info(f"graph_data_as_dicts: {graph_data_as_dicts}")

            # Return both BigQuery errors and processed data
            # return {
            #     "bigquery_errors": all_errors,
            # }

            return ({"status": "success", "code": 200})
        except Exception as e:
            self.logger.error("An unexpected error occurred during save_graph_data:")
        raise
