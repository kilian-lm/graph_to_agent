import os
import json
import requests
from google.cloud import bigquery
from google.oauth2 import service_account

class BigQueryHandler:
    def __init__(self, dataset_id, schema_json_path):
        # ... (your existing code)

        # GPT-4 API Configuration
        self.gpt4_api_url = "https://api.openai.com/v1/custom/gpt-4/instruct"
        self.gpt4_api_key = "your_gpt4_api_key"

    # ... (your existing methods)

    def translate_graph_data_for_bigquery(self, graph_data, graph_id):
        # ... (your existing code)

    def send_to_gpt4(self, messages):
        data = {
            "model": "gpt-4",
            "messages": messages
        }
        headers = {
            "Authorization": f"Bearer {self.gpt4_api_key}",
            "Content-Type": "application/json"
        }

        response = requests.post(self.gpt4_api_url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            raise Exception(f"Failed to send data to GPT-4 API: {response.status_code} - {response.text}")

    def process_graph_data_with_gpt4(self, graph_data, graph_id):
        nodes_for_bq, edges_for_bq = self.translate_graph_data_for_bigquery(graph_data, graph_id)

        # Assuming you want to send nodes and edges as separate requests to GPT-4
        nodes_message = [{"role": "user", "content": json.dumps(node)} for node in nodes_for_bq]
        edges_message = [{"role": "user", "content": json.dumps(edge)} for edge in edges_for_bq]

        # Send nodes to GPT-4
        nodes_response = self.send_to_gpt4(nodes_message)

        # Send edges to GPT-4
        edges_response = self.send_to_gpt4(edges_message)

        return nodes_response, edges_response

    # ... (other methods)

