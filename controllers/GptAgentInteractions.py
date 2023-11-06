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
from controllers.BigQueryHandler import BigQueryHandler

load_dotenv()

logging.basicConfig(level=logging.DEBUG)  # You can change the level as needed.
logger = logging.getLogger(__name__)


class GptAgentInteractions(BigQueryHandler):

    def __init__(self, dataset_id):
        super().__init__(dataset_id)
        # print(self.openai_api_key)
        # self.openai_api_key = os.getenv('OPEN_AI_KEY')
        # self.openai_base_url = "https://api.openai.com/v1/chat/completions"
        # self.headers = {
        #     'Content-Type': 'application/json',
        #     'Authorization': f'Bearer {self.openai_api_key}'
        # }
        # self.dataset_id = dataset_id
        # bq_client_secrets = os.getenv('BQ_CLIENT_SECRETS')
        #
        # try:
        #     bq_client_secrets_parsed = json.loads(bq_client_secrets)
        #     self.bq_client_secrets = Credentials.from_service_account_info(bq_client_secrets_parsed)
        #     self.bigquery_client = bigquery.Client(credentials=self.bq_client_secrets,
        #                                            project=self.bq_client_secrets.project_id)
        #     logger.info("BigQuery client successfully initialized.")
        # except json.JSONDecodeError as e:
        #     logger.error(f"Failed to parse BQ_CLIENT_SECRETS environment variable: {e}")
        #     raise
        # except Exception as e:
        #     logger.error(f"An error occurred while initializing the BigQuery client: {e}")
        #     raise

    def extract_gpt_interactions_before_save(self, graph_data, graph_id):

        nodes_for_bq, edges_for_bq = self.translate_graph_data_for_bigquery(graph_data, graph_id)
        # Log the transformed data for debugging
        logger.debug(f"Transformed Nodes: {nodes_for_bq}")
        logger.debug(f"Transformed Edges: {edges_for_bq}")

        graph_data_as_dicts = {
            "nodes": nodes_for_bq,
            "edges": edges_for_bq
        }

        logger.debug(f"graph_data_as_dicts: {graph_data_as_dicts}")

        # Pass the dictionaries to the workflow logic
        processed_data = self.translate_graph_to_gpt_sequence(graph_data_as_dicts)

        processed_data = processed_data["processed_data"]
        logger.debug(f"processed_data: {processed_data}")
        agent_content = self.extract_and_send_to_gpt(processed_data)
        logger.debug(f"agent_content: {agent_content}")

    # Add the process_recursive_graph method
    def process_recursive_graph(self, graph_data):
        # Update valid transitions to include 'variable' nodes
        valid_transitions = {
            'user': 'content',
            'content': ['system', 'variable'],
            'system': 'content',
            'variable': 'content'
        }

        # Process the graph in a sequence
        processed_data = {"messages": []}
        variable_content = None

        for edge in graph_data["edges"]:
            from_node = graph_data["nodes"][edge['from']]
            to_node = graph_data["nodes"][edge['to']]

            from_node_type = self.get_node_type(from_node)
            to_node_type = self.get_node_type(to_node)

            # Check for valid transitions
            if valid_transitions[from_node_type] == to_node_type or to_node_type in valid_transitions[from_node_type]:
                if from_node_type == 'variable':
                    # Replace 'variable' node content with the previous GPT API response
                    from_node['label'] = variable_content

                # Add the interaction to the processed data
                processed_data['messages'].append({
                    "role": from_node_type,
                    "content": from_node['label']
                })

                # If the 'to' node is a 'variable', get response from GPT API
                if to_node_type == 'variable':
                    gpt_response = self.get_gpt_response(processed_data)
                    variable_content = gpt_response

        return processed_data

    # New method to interact with the GPT API
    def get_gpt_response(self, processed_data):
        post_data = {
            "model": os.getenv("MODEL"),
            "messages": processed_data["messages"]
        }
        response = requests.post(self.openai_base_url, headers=self.headers, json=post_data)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            raise Exception(f"Error in GPT request: {response.status_code}, {response.text}")



# GptAgentInteractions
#
# help(GptAgentInteractions)