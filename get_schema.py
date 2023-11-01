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

load_dotenv()


def upload_example_to_bq(dataset_id, json_path, bq_client_secrets):
    # Load the JSON data
    with open(json_path, "r") as file:
        data = json.load(file)

    nodes = data['nodes']
    edges = data['edges']

    # Convert the client secrets string to Credentials object
    bq_client_secrets_parsed = json.loads(bq_client_secrets)
    credentials = Credentials.from_service_account_info(bq_client_secrets_parsed)
    bigquery_client = bigquery.Client(credentials=credentials, project=credentials.project_id)

    # Ensure dataset exists
    dataset_ref = bigquery_client.dataset(dataset_id)
    try:
        bigquery_client.get_dataset(dataset_ref)
    except Exception as e:
        dataset = bigquery.Dataset(dataset_ref)
        bigquery_client.create_dataset(dataset)

    # Ensure nodes and edges tables exist
    node_schema = [
        bigquery.SchemaField("id", "INT64", mode="REQUIRED"),
        bigquery.SchemaField("label", "STRING", mode="REQUIRED")
    ]
    edge_schema = [
        bigquery.SchemaField("from", "INT64", mode="REQUIRED"),
        bigquery.SchemaField("to", "INT64", mode="REQUIRED")
    ]
    nodes_table_ref = bigquery_client.dataset(dataset_id).table("nodes_table")
    edges_table_ref = bigquery_client.dataset(dataset_id).table("edges_table")

    try:
        bigquery_client.get_table(nodes_table_ref)
    except Exception as e:
        table = bigquery.Table(nodes_table_ref, schema=node_schema)
        bigquery_client.create_table(table)

    try:
        bigquery_client.get_table(edges_table_ref)
    except Exception as e:
        table = bigquery.Table(edges_table_ref, schema=edge_schema)
        bigquery_client.create_table(table)

    # Insert nodes and edges
    errors_nodes = bigquery_client.insert_rows(nodes_table_ref, nodes)
    errors_edges = bigquery_client.insert_rows(edges_table_ref, edges)

    if errors_nodes:
        return f"Encountered errors while inserting nodes: {errors_nodes}"
    if errors_edges:
        return f"Encountered errors while inserting edges: {errors_edges}"

    return "Data uploaded successfully!"

def translate_to_visjs(agent_interactions):
    nodes = []
    edges = []
    node_id = 0
    prev_content_node_id = None
    for interaction_group in agent_interactions:
        messages = interaction_group['messages']
        for interaction in messages:
            role = interaction['role']
            content = interaction['content']
            role_node = {"id": node_id, "label": role}
            nodes.append(role_node)
            role_node_id = node_id
            node_id += 1
            content_node = {"id": node_id, "label": content}
            nodes.append(content_node)
            content_node_id = node_id
            node_id += 1
            edges.append({"from": role_node_id, "to": content_node_id})
            if prev_content_node_id is not None:
                edges.append({"from": prev_content_node_id, "to": role_node_id})
            prev_content_node_id = content_node_id
    return {"nodes": nodes, "edges": edges}


# Example usage:
bq_client_secrets = os.getenv('BQ_CLIENT_SECRETS')
upload_example_to_bq('graph_to_agent', './test.json', bq_client_secrets)

import json
from app.BigQueryHandler import BigQueryHandler

# todo v2


# Load the provided JSON file
with open("./test.json", "r") as file:
    graph_data = json.load(file)

# Display the structure of the JSON data
graph_data.keys(), len(graph_data['nodes']), len(graph_data['edges'])



import time

# Generate a unique graph_id for this data
user_id = "user123"
timestamp = int(time.time())
graph_id = f"{user_id}_{timestamp}"

# Transform the nodes and edges to include the graph_id
transformed_nodes = [{"graph_id": graph_id, **node} for node in graph_data['nodes']]
transformed_edges = [{"graph_id": graph_id, **edge} for edge in graph_data['edges']]

transformed_data = {
    "nodes": transformed_nodes,
    "edges": transformed_edges
}

transformed_data["nodes"], transformed_data["edges"]  # Display first 5 nodes and edges for inspection


# Initialization
dataset_id = "your_dataset_id"
schema_json_path = "path_to_your_schema.json"  # This is not used in UpdatedBigQueryHandlerV2 but kept for consistency

bq_handler = BigQueryHandler("graph_to_agent", schema_json_path)

# Create dataset and tables
bq_handler.create_dataset_if_not_exists()
bq_handler.create_table_if_not_exists("nodes_table", bq_handler.get_node_schema())
bq_handler.create_table_if_not_exists("edges_table", bq_handler.get_edge_schema())

# Save the transformed graph data
bq_handler.save_graph_data(transformed_data, graph_id)


















# todo v1
def get_schema(obj, key="root"):
    """Recursively derive the schema of a JSON object."""
    schema = {}

    if isinstance(obj, dict):
        schema[key] = {}
        for k, v in obj.items():
            schema[key].update(get_schema(v, k))
    elif isinstance(obj, list) and len(obj) > 0:
        schema[key] = []
        # for simplicity, assuming all items in the list have the same schema
        schema[key].append(get_schema(obj[0]))
    else:
        schema[key] = type(obj).__name__

    return schema

def load_json_and_get_schema(filename):
    """Load a JSON file and get its schema."""
    with open(filename, 'r') as f:
        data = json.load(f)
    return get_schema(data)

# Example Usage:
schema = load_json_and_get_schema('test.json')
schema2 = load_json_and_get_schema('agent_interactions_20231031_185854.json')
print(schema)
print(schema2)
