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


@app.route('/')
def index_call():
    return render_template('graph.html')

@app.route('/get-graph-data', methods=['POST'])
def get_graph_data():
    try:
        graph_id = request.json['graph_id']
        graph_data = bq_handler.load_graph_data_by_id(graph_id)
        return jsonify(graph_data)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route('/get-available-graphs', methods=['GET'])
def get_available_graphs():
    try:
        available_graphs = bq_handler.get_available_graphs()
        return jsonify(available_graphs)
    except Exception as e:
        print(e)  # Log the error for debugging
        return jsonify({"status": "error", "message": str(e)})


@app.route('/save-graph', methods=['POST'])
def save_graph():
    try:
        graph_data = request.json
        # Generate a unique graph_id based on the current timestamp
        graph_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        errors = bq_handler.save_graph_data(graph_data, graph_id)

        if errors:
            return jsonify({"status": "error", "message": "Failed to save some data.", "errors": errors})

        return jsonify({"status": "success", "message": "Graph saved successfully!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


if __name__ == '__main__':
    app.run(debug=True)



# def translate_to_visjs(agent_interactions):
#     nodes = []
#     edges = []
#     node_id = 0
#
#     prev_content_node_id = None
#
#     for interaction_group in agent_interactions:
#         messages = interaction_group['messages']
#         for interaction in messages:
#             # Extract role and content
#             role = interaction['role']
#             # content = interaction['content'][:100] + "..."  # Truncate content for brevity
#             content = interaction['content']
#
#             # Create nodes
#             role_node = {"id": node_id, "label": role}
#             nodes.append(role_node)
#             role_node_id = node_id
#             node_id += 1
#
#             content_node = {"id": node_id, "label": content}
#             nodes.append(content_node)
#             content_node_id = node_id
#             node_id += 1
#
#             # Create edges
#             edges.append({"from": role_node_id, "to": content_node_id})  # Role to content
#             if prev_content_node_id is not None:
#                 edges.append({"from": prev_content_node_id, "to": role_node_id})  # Previous content to current role
#
#             prev_content_node_id = content_node_id
#
#     return {"nodes": nodes, "edges": edges}