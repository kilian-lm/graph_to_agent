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
from controllers.BigQueryHandler import BigQueryHandler
from controllers.GptAgentInteractions import GptAgentInteractions

app = Flask(__name__)

# Initialize BigQueryHandler
bq_handler = BigQueryHandler('graph_to_agent')
gpt_agent_interactions = GptAgentInteractions('graph_to_agent')

logging.basicConfig(level=logging.DEBUG)  # You can change the level as needed.
logger = logging.getLogger(__name__)


@app.route('/')
def index_call():
    return render_template('graph.html')


@app.route('/get-graph-data', methods=['POST'])
def get_graph_data():
    try:
        graph_id = request.json['graph_id']
        graph_data = bq_handler.load_graph_data_by_id(graph_id)
        # Assuming graph_data is already in the correct format for the frontend
        return jsonify(graph_data)
    except Exception as e:
        # Logging and returning an error response
        print(f"Error fetching graph data: {e}")
        return jsonify({"status": "error", "message": str(e)})


# @app.route('/get-graph-data', methods=['POST'])
# def get_graph_data():
#     try:
#         graph_id = request.json['graph_id']
#         graph_data = bq_handler.load_graph_data_by_id(graph_id)
#         return jsonify(graph_data)
#     except Exception as e:
#         return jsonify({"status": "error", "message": str(e)})


@app.route('/get-available-graphs', methods=['GET'])
def get_available_graphs():
    try:
        available_graphs = bq_handler.get_available_graphs()
        return jsonify(available_graphs)
    except Exception as e:
        print(e)  # Log the error for debugging
        return jsonify({"status": "error", "message": str(e)})


# extract to gpt interactions class
@app.route('/return-gpt-agent-answer-to-graph', methods=['POST'])
def return_gpt_agent_answer_to_graph():
    graph_data = request.json
    logger.debug(f"return_gpt_agent_answer_to_graph, graph_data : {graph_data}")
    processed_data = gpt_agent_interactions.translate_graph_to_gpt_sequence(graph_data)
    logger.debug(f"return_gpt_agent_answer_to_graph, processed_data : {processed_data}")

    gpt_response = gpt_agent_interactions.extract_and_send_to_gpt(processed_data)
    logger.debug(f"return_gpt_agent_answer_to_graph, gpt_response : {gpt_response}")

    updated_graph = gpt_agent_interactions.process_gpt_response_and_update_graph(gpt_response, graph_data)
    logger.debug(f"return_gpt_agent_answer_to_graph, updated_graph : {updated_graph}")

    # try:


    return jsonify({"status": "success", "updatedGraph": updated_graph})
    # except Exception as e:
    #     return jsonify({"status": "error", "message": str(e)})


@app.route('/save-graph', methods=['POST'])
def save_graph():
    try:
        graph_data = request.json
        logger.debug(f"save_graph, graph_data : {graph_data}")

        # Generate a unique graph_id based on the current timestamp
        graph_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        logger.debug(f"save_graph, graph_id : {graph_id}")
        errors = bq_handler.save_graph_data(graph_data, graph_id)

        logger.error(f"save_graph, errors : {errors}")

        if errors:
            return jsonify({"status": "error", "message": "Failed to save some data.", "errors": errors})

        return jsonify({"status": "success", "message": "Graph saved successfully!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


if __name__ == '__main__':
    app.run(debug=True)
