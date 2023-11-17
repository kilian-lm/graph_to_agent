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

load_dotenv()


# assumption: new methods allows chaining of agents but != recursive calls because @var isnt integrated yet

# class v2GptAgentInteractions(MatrixLayerOne):

class v2GptAgentInteractions():

    def __init__(self, dataset_id):
        # First logging
        self.timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        print(self.timestamp)
        self.log_file = f'{self.timestamp}_gpt_agent_interactions.log'
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

        # ToDo :: From mere class initialization in another class to inheritance

        self.matrix_layer_one_dataset_id = None
        self.graph_data = None
        self.matrix_layer_one = MatrixLayerOne(self.timestamp, self.graph_data, self.matrix_layer_one_dataset_id)

        self.dataset_id = dataset_id
        bq_client_secrets = os.getenv('BQ_CLIENT_SECRETS')

        try:
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

    def create_dataset_if_not_exists(self):
        dataset_ref = self.bigquery_client.dataset(self.dataset_id)
        try:
            self.bigquery_client.get_dataset(dataset_ref)
            self.logger.info(f"Dataset {self.dataset_id} already exists.")
        except Exception as e:
            try:
                dataset = bigquery.Dataset(dataset_ref)
                self.bigquery_client.create_dataset(dataset)
                self.logger.info(f"Dataset {self.dataset_id} created.")
            except Exception as ex:
                self.logger.error(f"Failed to create dataset {self.dataset_id}: {ex}")
                raise

    def create_table_if_not_exists(self, table_id, schema):
        table_ref = self.bigquery_client.dataset(self.dataset_id).table(table_id)
        try:
            self.bigquery_client.get_table(table_ref)
            self.logger.info(f"Table {table_id} already exists.")
        except Exception as e:
            try:
                table = bigquery.Table(table_ref, schema=schema)
                self.bigquery_client.create_table(table)
                self.logger.info(f"Table {table_id} created.")
            except Exception as ex:
                self.logger.error(f"Failed to create table {table_id}: {ex}")
                raise

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

    def get_available_graphs(self):
        # Query to get distinct graph_ids from the nodes_table
        query = f"SELECT DISTINCT graph_id FROM `{self.dataset_id}.nodes_table`"
        query_job = self.bigquery_client.query(query)
        results = query_job.result()

        return [{"graph_id": row["graph_id"], "graph_name": row["graph_id"]} for row in results]

    def load_graph_data_by_id(self, graph_id):
        nodes_table_ref = self.bigquery_client.dataset(self.dataset_id).table("nodes_table")
        edges_table_ref = self.bigquery_client.dataset(self.dataset_id).table("edges_table")

        # Fetch nodes for given graph_id
        nodes_query = f"SELECT * FROM `{self.dataset_id}.nodes_table` WHERE graph_id = '{graph_id}'"
        nodes_query_job = self.bigquery_client.query(nodes_query)
        nodes_results = nodes_query_job.result()
        nodes = [{"id": row['id'], "label": row['label']} for row in nodes_results]

        self.logger.info(f"nodes loaded by graph id {nodes} already exists.")

        # Fetch edges for given graph_id
        edges_query = f"SELECT * FROM `{self.dataset_id}.edges_table` WHERE graph_id = '{graph_id}'"
        edges_query_job = self.bigquery_client.query(edges_query)
        edges_results = edges_query_job.result()
        edges = [{"from": row['from'], "to": row['to']} for row in edges_results]

        return {"nodes": nodes, "edges": edges}

    def build_tree_structure(self, nodes, edges):
        # graph_data = json.loads(graph_data)
        # nodes = graph_data['nodes']
        # edges = graph_data['edges']

        tree = {}
        for node in nodes:
            tree[node['id']] = {
                'label': node['label'],
                'children': []
            }
        for edge in edges:
            tree[edge['from']]['children'].append(edge['to'])
        return tree

    def print_tree(self, tree, node_id, depth=0):
        # This function recursively prints the tree.
        indent = ' ' * depth * 2
        print(f"{indent}- {tree[node_id]['label']}")
        for child_id in tree[node_id]['children']:
            self.print_tree(tree, child_id, depth + 1)

    def load_json_graph(self, json_graph_data):
        graph_data = json.loads(json_graph_data)
        return graph_data

    def provide_root_nodes(self, graph_data):
        root_nodes = [node['id'] for node in graph_data['nodes'] if
                      not any(edge['to'] == node['id'] for edge in graph_data['edges'])]

        return root_nodes

    def call_tree(self, root_nodes, tree):

        # tree = self.build_tree_structure(graph_data['nodes'], graph_data['edges'])

        # Now let's print the trees. There may be multiple roots if the graph is not a single tree.
        for root_id in root_nodes:
            self.print_tree(tree, root_id)
            print("\n")  # Add spacing between different trees (if any)

    def tree_to_gpt_call(self, tree, node_id, is_user=True):
        messages = []
        node = tree[node_id]

        # If the current node is a 'user' or 'system', process its first child as the content.
        if node['label'] in ['user', 'system']:
            role = 'user' if is_user else 'system'
            if node['children']:
                content_node_id = node['children'][0]  # First child is the content.
                content = tree[content_node_id]['label']
                messages.append({"role": role, "content": content})

                # Process the response (next child of the content node).
                if len(tree[content_node_id]['children']) > 0:
                    response_node_id = tree[content_node_id]['children'][0]
                    messages.extend(self.tree_to_gpt_call(tree, response_node_id, not is_user))

        return messages

    def tree_based_design_general(self, root_nodes, tree):
        all_messages = []

        for root_id in root_nodes:
            messages = self.tree_to_gpt_call(tree, root_id)
            all_messages.extend(messages)

        gpt_call = {
            "model": "gpt-3.5-turbo",
            "messages": all_messages
        }

        return gpt_call

    def main_tree_based_design_general(self, graph_data):
        # graph_data = self.load_json_graph(json_graph_data)
        self.logger.info(graph_data)
        tree = self.build_tree_structure(graph_data['nodes'], graph_data['edges'])
        self.logger.info(tree)

        root_nodes = self.provide_root_nodes(graph_data)
        self.logger.info(root_nodes)

        gpt_calls = self.tree_based_design_general(root_nodes, tree)
        self.logger.info(gpt_calls)
        self.logger.info(self.call_tree(root_nodes, tree))
        response = self.get_gpt_response(gpt_calls)

        # process_gpt_response_and_update_graph

        return response

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

    def translate_graph_to_gpt_sequence(self, graph_data):
        nodes = graph_data["nodes"]
        edges = graph_data["edges"]

        # Build a mapping of node IDs to nodes
        node_mapping = {node['id']: node for node in nodes}
        self.logger.info(f"node_map: {node_mapping}")

        # Initialize the data structure
        translated_data = {
            "model": os.getenv("MODEL"),
            "messages": []
        }

        self.logger.info(f"translated_data: {translated_data}")

        # Define valid transitions
        valid_transitions = {
            'user': 'content',
            'content': 'system',
            'system': 'content'
        }

        # Start from 'user' nodes and follow the valid transitions
        current_expected = 'user'

        for edge in edges:
            from_node = node_mapping[edge['from']]
            to_node = node_mapping[edge['to']]

            self.logger.info(f"from_node: {from_node}")
            self.logger.info(f"to_node: {to_node}")

            from_node_type = self.get_node_type(from_node)
            to_node_type = self.get_node_type(to_node)

            self.logger.info(f"from_node_type: {from_node_type}")
            self.logger.info(f"to_node_type: {to_node_type}")

        # Serialize data to json
        json_data = json.dumps(translated_data, indent=4)
        # timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"temp_local/processed_graph_{self.timestamp}.json"

        # Check if the temp_local directory exists
        if not os.path.exists('temp_local'):
            os.makedirs('temp_local')

        # Save the JSON data to the file
        with open(filename, 'w') as json_file:
            json_file.write(json_data)

        # breakpoint()  # todo ::

        return {
            'bigquery_errors': {'node_errors': [], 'edge_errors': []},
            'processed_data': translated_data
        }

    def extract_and_send_to_gpt(self, processed_data):

        actual_data = processed_data.get("processed_data", {})
        messages = actual_data.get("messages", [])

        post_data = {
            "model": os.getenv("MODEL"),
            "messages": messages
        }

        # Send POST request to GPT
        response = requests.post(self.openai_base_url, headers=self.headers, json=post_data)

        if response.status_code == 200:
            agent_content = response.json()["choices"][0]["message"]["content"]
            return agent_content
        else:
            raise Exception(f"Error in GPT request: {response.status_code}, {response.text}")

    def extract_gpt_interactions_before_save(self, graph_data, graph_id):

        nodes_for_bq, edges_for_bq = self.translate_graph_data_for_bigquery(graph_data, graph_id)
        # Log the transformed data for debugging
        self.logger.info(f"extract_gpt_interactions_before_save, Transformed Nodes: {nodes_for_bq}")
        self.logger.info(f"extract_gpt_interactions_before_save, Transformed Edges: {edges_for_bq}")

        graph_data_as_dicts = {
            "nodes": nodes_for_bq,
            "edges": edges_for_bq
        }

        self.logger.info(f"extract_gpt_interactions_before_save, graph_data_as_dicts: {graph_data_as_dicts}")

        # Pass the dictionaries to the workflow logic
        processed_data = self.translate_graph_to_gpt_sequence(graph_data_as_dicts)

        processed_data = processed_data["processed_data"]
        self.logger.info(f"processed_data: {processed_data}")
        agent_content = self.extract_and_send_to_gpt(processed_data)
        self.logger.info(f"agent_content: {agent_content}")

    def get_last_content_node(self, edges, nodes):
        # Assuming edges are ordered
        last_edge = edges[-1]
        last_node_id = last_edge['to']

        self.logger.info(f"get_last_content_node, last_node_id : {last_node_id}")

        for node in nodes:
            if node['id'] == last_node_id:
                return node
        return None

    def get_gpt_response(self, processed_data):
        # post_data = {
        #     # "model": os.getenv("MODEL"),
        #     "model":processed_data["model"],
        #     "messages": processed_data["messages"]
        # }
        self.logger.debug(processed_data)
        response = requests.post(self.openai_base_url, headers=self.headers, json=processed_data)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            raise Exception(f"Error in GPT request: {response.status_code}, {response.text}")

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
            # Check and create dataset if it doesn't exist
            self.create_dataset_if_not_exists()

            self.matrix_layer_one_dataset_id = "graph_to_agent_adjacency_matrices"
            self.graph_data = graph_data
            self.matrix_layer_one = MatrixLayerOne(self.timestamp, self.graph_data, self.matrix_layer_one_dataset_id)

            self.matrix_layer_one.upload_to_bigquery()

            nodes_table_ref = self.bigquery_client.dataset(self.dataset_id).table("nodes_table")
            edges_table_ref = self.bigquery_client.dataset(self.dataset_id).table("edges_table")

            # Check and create nodes table if it doesn't exist
            self.create_table_if_not_exists("nodes_table", self.get_node_schema())

            # Check and create edges table if it doesn't exist
            self.create_table_if_not_exists("edges_table", self.get_edge_schema())

            # Retrieve the tables and their schemas
            nodes_table = self.bigquery_client.get_table(nodes_table_ref)
            edges_table = self.bigquery_client.get_table(edges_table_ref)

            # Use the translator function to transform the data
            nodes_for_bq, edges_for_bq = self.translate_graph_data_for_bigquery(graph_data, graph_id)

            # Log the transformed data for debugging
            self.logger.info(f"controller save_graph_data, Transformed Nodes: {nodes_for_bq}")
            self.logger.info(f"controller save_graph_data, Transformed Edges: {edges_for_bq}")

            # Insert nodes and pass in the schema explicitly
            errors_nodes = self.bigquery_client.insert_rows(nodes_table, nodes_for_bq,
                                                            selected_fields=nodes_table.schema)
            if errors_nodes:
                self.logger.info(f"Encountered errors while inserting nodes: {errors_nodes}")

            # Insert edges and pass in the schema explicitly
            errors_edges = self.bigquery_client.insert_rows(edges_table, edges_for_bq,
                                                            selected_fields=edges_table.schema)
            if errors_edges:
                self.logger.info(f"Encountered errors while inserting edges: {errors_edges}")

            # Compile all errors
            # all_errors = {
            #     "node_errors": errors_nodes,
            #     "edge_errors": errors_edges
            # }

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

# graph_data_json = """
# {
#   "nodes": [
#     {
#       "id": "c7d1c0a4-6365-44d6-be0c-bd3fc5436b85",
#       "label": "user"
#     },
#     {
#       "id": "757e7439-08f8-4cea-afac-c25b01167d32",
#       "label": "user"
#     },
#     {
#       "id": "2e419e7e-a540-4c9a-af4e-5110e54fad96",
#       "label": "system"
#     },
#     {
#       "id": "07537a68-1c7e-4edb-a72f-2d82015c490f",
#       "label": "Understood! As I'm an expert in the .puml syntax i will correct it"
#     },
#     {
#       "id": "1cc45118-72ee-4efe-95d8-06e8c02fb4c0",
#       "label": "The following is a .puml content generated by an agent. Please critically review it and correct any mistakes, especially ensuring it strictly adheres to .puml syntax and does not contain any elements from other diagramming languages like Mermaid"
#     },
#     {
#       "id": "2d545024-3765-4b01-b1df-04da99ea4e80",
#       "x": -575.9889498552049,
#       "y": -331.9214349905721,
#       "label": "sequenceDiagramAlice->>John: Hello John, how are you?John-->>Alice: Great!Alice-)John: See you later!"
#     }
#   ],
#   "edges": [
#     {
#       "from": "07537a68-1c7e-4edb-a72f-2d82015c490f",
#       "to": "757e7439-08f8-4cea-afac-c25b01167d32",
#       "id": "84f178f5-9dba-4f5c-b525-e16ea173be2f"
#     },
#     {
#       "from": "1cc45118-72ee-4efe-95d8-06e8c02fb4c0",
#       "to": "2e419e7e-a540-4c9a-af4e-5110e54fad96",
#       "id": "d535cac8-7bec-452e-b3ef-4c0184610ba3"
#     },
#     {
#       "from": "2e419e7e-a540-4c9a-af4e-5110e54fad96",
#       "to": "07537a68-1c7e-4edb-a72f-2d82015c490f",
#       "id": "1764a3dc-3198-4e08-819e-51ccf56f4a07"
#     },
#     {
#       "from": "c7d1c0a4-6365-44d6-be0c-bd3fc5436b85",
#       "to": "1cc45118-72ee-4efe-95d8-06e8c02fb4c0",
#       "id": "10bad7e6-bf61-42f2-95aa-47ba7abe6b30"
#     },
#     {
#       "from": "757e7439-08f8-4cea-afac-c25b01167d32",
#       "to": "2d545024-3765-4b01-b1df-04da99ea4e80",
#       "id": "eb438078-7275-414e-9eed-cf77d931e0c3"
#     }
#   ]
# }
# """


#
# gpt_agent_interactions = v2GptAgentInteractions('graph_to_agent')

# gpt_agent_interactions.main_tree_based_design_general(graph_data_json)

#
# graph_data = gpt_agent_interactions.load_json_graph(graph_data_json)
#
# gpt_agent_interactions.logger.info(graph_data)
# tree = gpt_agent_interactions.build_tree_structure(graph_data['nodes'], graph_data['edges'])
# gpt_agent_interactions.logger.info(tree)
#
# root_nodes = gpt_agent_interactions.provide_root_nodes(graph_data)
# gpt_agent_interactions.logger.info(root_nodes)
#
# gpt_calls = gpt_agent_interactions.tree_based_design_general(root_nodes, tree)
# gpt_agent_interactions.logger.info(gpt_calls)
#
# type(gpt_calls)
#
# test = json.dumps(gpt_calls)

# post_data = {
#     # "model": os.getenv("MODEL"),
#     "model": test["model"],
#     "messages": gpt_calls["messages"]
# }

# gpt_agent_interactions.extract_and_send_to_gpt(gpt_calls)

# response =gpt_agent_interactions.get_gpt_response(gpt_calls)
#
# response = gpt_agent_interactions.get_gpt_response(gpt_calls)
# response
#
#
#
# gpt_agent_interactions.call_tree(graph_data_json)
# nodes_for_bq, edges_for_bq = gpt_agent_interactions.translate_graph_data_for_bigquery(graph_data_json, "test")

# graph_data_json = """
# {
#   "nodes": [
#     {
#       "id": "c7d1c0a4-6365-44d6-be0c-bd3fc5436b85",
#       "label": "user"
#     },
#     {
#       "id": "757e7439-08f8-4cea-afac-c25b01167d32",
#       "label": "user"
#     },
#     {
#       "id": "2e419e7e-a540-4c9a-af4e-5110e54fad96",
#       "label": "system"
#     },
#     {
#       "id": "07537a68-1c7e-4edb-a72f-2d82015c490f",
#       "label": "Understood! As I'm an expert in the .puml syntax i will correct it"
#     },
#     {
#       "id": "1cc45118-72ee-4efe-95d8-06e8c02fb4c0",
#       "label": "The following is a .puml content generated by an agent. Please critically review it and correct any mistakes, especially ensuring it strictly adheres to .puml syntax and does not contain any elements from other diagramming languages like Mermaid"
#     },
#     {
#       "id": "2d545024-3765-4b01-b1df-04da99ea4e80",
#       "x": -575.9889498552049,
#       "y": -331.9214349905721,
#       "label": "sequenceDiagramAlice->>John: Hello John, how are you?John-->>Alice: Great!Alice-)John: See you later!"
#     }
#   ],
#   "edges": [
#     {
#       "from": "07537a68-1c7e-4edb-a72f-2d82015c490f",
#       "to": "757e7439-08f8-4cea-afac-c25b01167d32",
#       "id": "84f178f5-9dba-4f5c-b525-e16ea173be2f"
#     },
#     {
#       "from": "1cc45118-72ee-4efe-95d8-06e8c02fb4c0",
#       "to": "2e419e7e-a540-4c9a-af4e-5110e54fad96",
#       "id": "d535cac8-7bec-452e-b3ef-4c0184610ba3"
#     },
#     {
#       "from": "2e419e7e-a540-4c9a-af4e-5110e54fad96",
#       "to": "07537a68-1c7e-4edb-a72f-2d82015c490f",
#       "id": "1764a3dc-3198-4e08-819e-51ccf56f4a07"
#     },
#     {
#       "from": "c7d1c0a4-6365-44d6-be0c-bd3fc5436b85",
#       "to": "1cc45118-72ee-4efe-95d8-06e8c02fb4c0",
#       "id": "10bad7e6-bf61-42f2-95aa-47ba7abe6b30"
#     },
#     {
#       "from": "757e7439-08f8-4cea-afac-c25b01167d32",
#       "to": "2d545024-3765-4b01-b1df-04da99ea4e80",
#       "id": "eb438078-7275-414e-9eed-cf77d931e0c3"
#     }
#   ]
# }
# """
# graph_data = json.loads(graph_data_json)
# gpt_agent_interactions.translate_graph_to_gpt_sequence(graph_data)

#
# help(GptAgentInteractions)
