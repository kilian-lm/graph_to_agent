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
from logger.CustomLogger import CustomLogger
import inspect

load_dotenv()


# assumption: new methods allows chaining of agents but != recursive calls because @var isnt integrated yet

class EngineRoom():

    def __init__(self, dataset_id):
        # First logging
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        print(timestamp)
        self.log_file = f'{timestamp}_gpt_agent_interactions.log'
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

    def prepare_gpt_format(self, root_nodes, tree):
        all_messages = []

        for root_id in root_nodes:
            messages = self.tree_to_gpt_call(tree, root_id)
            all_messages.extend(messages)

        gpt_call = {
            "model": "gpt-3.5-turbo",
            "messages": all_messages
        }

        return gpt_call



    def get_node_type(self, node):
        if 'user' in node['label'].lower():
            return 'user'
        elif 'system' in node['label'].lower():
            return 'system'
        else:
            return 'content'

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
        # Find the last 'user' node in the graph_data
        last_user_node = None
        for edge in reversed(graph_data['edges']):  # Reverse to start from the end
            for node in graph_data['nodes']:
                if node['id'] == edge['to'] and self.get_node_type(node) == 'content':
                    last_user_node = node
                    break
            if last_user_node:
                break

        if last_user_node is None:
            raise Exception("Last user node could not be found.")

        self.logger.info(f"process_gpt_response_and_update_graph, last_user_node : {last_user_node}")

        # Generate a unique ID for the new content node based on the last user node
        new_content_node_id = f"content_{int(datetime.datetime.now().timestamp() * 1000)}"
        new_content_node = {
            'id': new_content_node_id,
            'label': gpt_response,
        }

        # Add the new content node to the nodes list
        graph_data['nodes'].append(new_content_node)

        # Create a new edge from the last user node to the new content node
        new_edge_to_content = {
            'from': last_user_node['id'],
            'to': new_content_node_id,
        }
        graph_data['edges'].append(new_edge_to_content)

        # Create a new edge from the new content node to the GPT agent response node
        # new_agent_response_node_id = f"agent_response_{int(datetime.datetime.now().timestamp() * 1000)}"
        # new_agent_response_node = {
        #     'id': new_agent_response_node_id,
        #     'label': 'GPT response based on the content node'
        # }
        # graph_data['nodes'].append(new_agent_response_node)

        # new_edge_to_agent_response = {
        #     'from': new_content_node_id,
        #     'to': new_agent_response_node_id,
        # }
        # graph_data['edges'].append(new_edge_to_agent_response)

        self.logger.info(f"process_gpt_response_and_update_graph, new_content_node : {new_content_node}")
        self.logger.info(f"process_gpt_response_and_update_graph, new_edge_to_content : {new_edge_to_content}")
        # self.logger.info(f"process_gpt_response_and_update_graph, new_agent_response_node : {new_agent_response_node}")
        # self.logger.info(
            # f"process_gpt_response_and_update_graph, new_edge_to_agent_response : {new_edge_to_agent_response}")

        return graph_data

    def v2_subgraphs_process_gpt_response_and_update_graph(self, gpt_responses, graph_data):
        # This assumes that gpt_responses is a list of responses for each disconnected subgraph
        # If it's a single string, you'll need to modify this to make the call for each subgraph and collect the responses.

        # Identify all root nodes, which are starting points for each disconnected subgraph
        root_nodes = self.provide_root_nodes(graph_data)

        # Build a tree structure for each subgraph
        trees = [self.build_tree_structure(graph_data['nodes'], graph_data['edges'], root) for root in root_nodes]

        # Find the last content node for each subgraph and connect the GPT response
        for i, tree in enumerate(trees):
            last_content_node = self.find_last_content_node_in_tree(tree)
            # Get corresponding GPT response for this subgraph
            gpt_response = gpt_responses[
                i]  # This line is just an example. Adjust it to fit how you get your GPT responses.

            # Create a new node for the GPT response and add it to the graph
            new_node_id = f"agent_response_{i}_{int(datetime.datetime.now().timestamp() * 1000)}"
            new_node = {'id': new_node_id, 'label': gpt_response}
            graph_data['nodes'].append(new_node)

            # Connect this new node to the last content node
            new_edge = {'from': last_content_node['id'], 'to': new_node_id}
            graph_data['edges'].append(new_edge)

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

    def main_tree_based_design_general(self, graph_data):
        # graph_data = self.load_json_graph(json_graph_data)
        self.logger.info(graph_data)
        tree = self.build_tree_structure(graph_data['nodes'], graph_data['edges'])
        self.logger.info(tree)

        root_nodes = self.provide_root_nodes(graph_data)
        self.logger.info(root_nodes)

        gpt_calls = self.prepare_gpt_format(root_nodes, tree)
        self.logger.info(gpt_calls)
        self.logger.info(self.call_tree(root_nodes, tree))
        response = self.get_gpt_response(gpt_calls)

        self.logger.info(f"return_gpt_agent_answer_to_graph, gpt_response: {response}")
        updated_graph = self.process_gpt_response_and_update_graph(response, graph_data)
        self.logger.info(f"return_gpt_agent_answer_to_graph, updated_graph: {updated_graph}")


        return updated_graph

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
