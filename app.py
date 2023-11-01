from flask import Flask, render_template, request, jsonify, session
import os
import json
from google.cloud import bigquery
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
from google.api_core.exceptions import NotFound
import logging
from google.oauth2.service_account import Credentials
from google.oauth2 import service_account

# from app.Solver import Solver
# from app.LoggerPublisher.MainPublisher import MainPublisher
# from app.LoggerPublisher.MainLogger import MainLogger

# load_dotenv()

import datetime
import json

from google.cloud import bigquery
from google.oauth2.service_account import Credentials
from google.cloud.exceptions import NotFound

from flask import Flask, render_template
import json


from flask import Flask, render_template, jsonify, request
import json
from app.BigQueryHandler import BigQueryHandler

app = Flask(__name__)

# Initialize BigQueryHandler
bq_handler = BigQueryHandler('graph_to_agent', '../test.json')


@app.route('/save-graph', methods=['POST'])
def save_graph():
    try:
        graph_data = request.json
        # Generate a unique graph_id based on the current timestamp
        graph_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        bq_handler.save_graph_data(graph_data, graph_id)
        return jsonify({"status": "success", "message": "Graph saved successfully!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route('/')
def serve_graph():
    # Ensure dataset exists
    bq_handler.create_dataset_if_not_exists()

    # Ensure nodes and edges tables exist
    bq_handler.create_table_if_not_exists("nodes_table", bq_handler.get_node_schema())
    bq_handler.create_table_if_not_exists("edges_table", bq_handler.get_edge_schema())

    # Load the JSON data
    with open("../agent_interactions_20231031_185854.json", "r") as file:
        data = json.load(file)

    agent_interactions = data['agent_interactions']

    visjs_data = translate_to_visjs(agent_interactions)

    # Return the rendered HTML template and pass the visjs_data
    return render_template('graph.html', data=visjs_data)



@app.route('/save-graph', methods=['POST'])
def save_graph():
    try:
        graph_data = request.json
        bq_handler.save_graph_data(graph_data)
        return jsonify({"status": "success", "message": "Graph saved successfully!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route('/load-graph', methods=['GET'])
def load_graph():
    try:
        nodes, edges = bq_handler.load_latest_graph_data()
        if nodes and edges:
            return jsonify({"nodes": nodes, "edges": edges})
        else:
            return jsonify({"status": "error", "message": "No data found."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


def translate_to_visjs(agent_interactions):
    nodes = []
    edges = []
    node_id = 0

    prev_content_node_id = None

    for interaction_group in agent_interactions:
        messages = interaction_group['messages']
        for interaction in messages:
            # Extract role and content
            role = interaction['role']
            # content = interaction['content'][:100] + "..."  # Truncate content for brevity
            content = interaction['content']

            # Create nodes
            role_node = {"id": node_id, "label": role}
            nodes.append(role_node)
            role_node_id = node_id
            node_id += 1

            content_node = {"id": node_id, "label": content}
            nodes.append(content_node)
            content_node_id = node_id
            node_id += 1

            # Create edges
            edges.append({"from": role_node_id, "to": content_node_id})  # Role to content
            if prev_content_node_id is not None:
                edges.append({"from": prev_content_node_id, "to": role_node_id})  # Previous content to current role

            prev_content_node_id = content_node_id

    return {"nodes": nodes, "edges": edges}

if __name__ == '__main__':
    app.run(debug=True)

